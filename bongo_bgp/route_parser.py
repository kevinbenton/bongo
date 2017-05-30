from bongo_bgp import log
import json
import netaddr
import os
import pprint
import sys


class FileWatcher(object):

    def __init__(self, path, route_receiver):
        """Parse a file or stdin for route updates and relay to callback.

        :path:  Path to watch for raw route updates from EXABGP. Use None for
                stdin.
        :route_receiver:  callback that accepts prefix, next_hop, and as_path
        """

        if path and not os.path.exists(path):
            raise RuntimeError("Path %s doesn't exist" % path)
        self._path = path
        self._route_receiver = route_receiver

    def watch(self):
        with open(self._path, 'r') if self._path else sys.stdin as rh:
            for line in rh:
                self._process_line(line)

    def _process_line(self, line):
        if not line.strip():
            return
        for next_hop, local_asn, msg, prefix, path in parse_exabgp_line(line):
            action = 'add' if msg == 'announce' else 'remove'
            self._route_receiver(prefix, next_hop, path, action)


def parse_exabgp_line(line):
    """Parse the json format from ExaBGP. Currently only ipv4 supported."""
    actions = []
    try:
        data = json.loads(line)
        log.debug('json decoded :' + pprint.pformat(data))
    except Exception as e:
        log.error('failure, json can not be decoded (%s): %s '
                  % (str(e), line.rstrip()))
        return actions
    if data['type'] != 'update':
        log.debug('Type is not update: %s' % data['type'])
        return actions
    if 'update' not in data['neighbor']['message']:
        log.debug('No route change in update')
        return actions
    next_hop = netaddr.IPAddress(data['neighbor']['address']['peer'])
    local_asn = int(data['neighbor']['asn']['local'])
    update = data['neighbor']['message']['update']
    if 'withdraw' in update:
        for prefix in update['withdraw']['ipv4 unicast']:
            actions.append((next_hop, local_asn, 'withdraw',
                            netaddr.IPNetwork(prefix), []))
    if 'announce' in update:
        if 'attribute' not in update or 'as-path' not in update['attribute']:
            log.debug('no as-path in update')
            return actions
        path = update['attribute']['as-path']
        log.debug("AS_PATH: %s" % path)
        for prefixes in update['announce']['ipv4 unicast'].values():
            for prefix in prefixes.keys():
                actions.append((next_hop, local_asn, 'announce',
                                netaddr.IPNetwork(prefix), path))
    return actions
