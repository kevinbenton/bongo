import copy
import subprocess
import time

import netaddr

from bongo_bgp import log
from bongo_bgp.plugins.route_reactors import base


class FPRPFReactor(base.ReactorBase):
    """Feasible Path Reverse Path Filtering Implementation.

    Generates allow rules for routes with leaky algorithm for ceiling.
    All other traffic will be dropped.

    Simplified version of POX implementation that lives at
    https://github.com/kevinbenton/pox/commit/3a85a1fa34710dc639e685024bbc754fbc39c929
    """

    BASE_OFCTL = "ovs-ofctl"
    OF_BRIDGE = "filter-br"
    # map of peer IPs that will show up in next_hop values to their mac address
    # that will be used on the wire to forward traffic to their prefixes.
    PEER_IP_MAC_MAP = {netaddr.IPAddress('127.100.0.1'): '00:11:22:33:44:55'}
    # maximum number of openflow block rules before compression should occur.
    MAX_TABLE_ENTRIES = 100

    def __init__(self):
        self.current_openflow_rules = set()
        self.peer_ip_mac_map = copy.copy(self.PEER_IP_MAC_MAP)
        # keep track of allowed prefixes and their next hop mac.
        # a.k.a a Forwarding Information Base
        self.FIB = {mac: set() for mac in self.peer_ip_mac_map.values()}
        assert self.MAX_TABLE_ENTRIES >= len(self.peer_ip_mac_map)
        self.max_table_entries = self.MAX_TABLE_ENTRIES
        self.process = False
        self._startup = True

    def _to_mac(self, next_hop):
        if next_hop not in self.peer_ip_mac_map:
            log.warning("next_hop %s not in next hop mac map %s"
                        % (next_hop, self.peer_ip_mac_map))
        return self.peer_ip_mac_map.get(next_hop)

    def route_accepted(self, prefix, next_hop, as_path):
        mac = self._to_mac(next_hop)
        if not mac:
            return
        self.FIB[mac].add(prefix)
        self.process = True

    def route_removed(self, prefix, next_hop, as_path):
        mac = self._to_mac(next_hop)
        if not mac:
            return
        self.FIB[mac].discard(prefix)
        self.process = True

    def route_rejected(self, prefix, next_hop, as_path):
        # rejected and removed are equivalent in a whitelist FPRPF system
        self.route_removed(prefix, next_hop, as_path)

    def process_thread(self, wait_for_more=True):
        while True:
            while not self.process:
                time.sleep(1)
                continue
            self._refresh_rules()
            if not wait_for_more:
                break

    def _refresh_rules(self):
        new = self._generate_rules()
        to_add = new - self.current_openflow_rules
        to_remove = self.current_openflow_rules - new
        log.debug("%s flows to add" % len(to_add))
        log.debug("%s flows to remove" % len(to_remove))
        if self._startup:
            self._startup = False
            # clear whatever was there before
            self._of_exec('del-flows')
        for flow in to_remove:
            self._of_exec('del-flows', self._del_prep(flow))
        for flow in to_add:
            self._of_exec('add-flow', flow)
        self.current_openflow_rules = new

    def _del_prep(self, flow):
        """Delete doesn't accept priority or actions."""
        new = []
        for criteria in flow.split(','):
            if 'priority=' in criteria or 'actions' in criteria:
                continue
            new.append(criteria)
        return ','.join(new)

    def _of_exec(self, action, flow=None):
        cmd = ['sudo', self.BASE_OFCTL, action, self.OF_BRIDGE]
        if flow:
            cmd.append(flow)
        subprocess.check_call(cmd)

    def _generate_rules(self):
        new_openflow_rules = set()
        # divide up the table space by ratios of routes from each peer
        total = float(sum(map(len, self.FIB.values())))
        for mac, prefixes in self.FIB.items():
            if not prefixes:
                continue
            ratio = float(len(prefixes)) / total
            quota = int(ratio * self.max_table_entries)
            cidrs = self._leaky_compress(prefixes, quota)
            new_openflow_rules.add(self._default_block_mac_rule(mac))
            for cidr in cidrs:
                new_openflow_rules.add(self._allow_cidr_mac_rule(mac, cidr))
        return new_openflow_rules

    def _default_block_mac_rule(self, mac):
        return 'priority=5,dl_dst=%s,actions=DROP' % mac

    def _allow_cidr_mac_rule(self, mac, cidr):
        return 'priority=10,ip,dl_dst=%s,nw_dst=%s,actions=NORMAL' % (mac,
                                                                      cidr)

    def _leaky_compress(self, cidrs, limit):
        """compress CIDRs into limit by allowing min extra IPs required"""
        # start with smallest networks and work our way up.
        cidrs = sorted(cidrs, reverse=True, key=lambda cidr: cidr.prefixlen)
        netmask = 32
        while len(cidrs) > limit:
            netmask -= 1
            for cidr in cidrs:
                if cidr.prefixlen <= netmask:
                    break
                pcopy = netaddr.IPNetwork(cidr)
                pcopy.prefixlen = netmask
                new = netaddr.IPSet([pcopy]) | netaddr.IPSet(cidrs)
                new_cidrs = new.iter_cidrs()
                if len(new_cidrs) < len(cidrs):
                    cidrs = set(new_cidrs)
                    break
        return cidrs
