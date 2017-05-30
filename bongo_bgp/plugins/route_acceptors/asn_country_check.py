import collections
import netaddr
import os
import sys

from bongo_bgp import log
from bongo_bgp.plugins.route_acceptors import base


_THIS_DIR = os.path.dirname(sys.modules[__name__].__file__)
_FIREWALLING_DIR = os.path.join(_THIS_DIR, '..', '..', '..',
                                'configs_for_demos',
                                'firewalling_scenic_routes')
_POLICY_FILE = os.path.join(_FIREWALLING_DIR, 'scenic_policy.cfg')
_COUNTRY_FILE = os.path.join(_FIREWALLING_DIR, 'country_codes.csv')


class ASNCountryCheck(base.AcceptorBase):
    """Checks to see if path to a prefix contains banned country codes."""

    path_to_policy_file = _POLICY_FILE
    path_to_asn_to_country_code_map = _COUNTRY_FILE

    def __init__(self):
        self._parse_policy_file()
        self._parse_country_map()

    def _parse_country_map(self):
        self._AS_TO_COUNTRY = {}
        with open(self.path_to_asn_to_country_code_map, 'r+') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    asn, ccode = line.split(',')
                    asn = int(asn)
                except ValueError:
                    log.error("Bad country code mapping in csv. %s" % line)
                    raise
                self._AS_TO_COUNTRY[asn] = ccode

    def _parse_policy_file(self):
        self._PREFIX_REJECTS = collections.defaultdict(set)
        self._PREFIX_ALLOWS = collections.defaultdict(set)
        with open(self.path_to_policy_file, 'r+') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    prefix, allowed, blocked = line.split(',')
                    prefix = netaddr.IPNetwork(prefix)
                    allowed = allowed.split(' ')   # CCs space separataed
                    blocked = blocked.split(' ')
                except Exception:
                    log.error("Bad policy line. %s" % line)
                    raise
                for a in allowed:
                    if not a or a == "*":
                        continue
                    self._PREFIX_ALLOWS[prefix].add(a)
                for b in blocked:
                    if not b or b == "*":
                        continue
                    self._PREFIX_REJECTS[prefix].add(b)

    def _asns_ccodes(self, asns):
        """Return set of country codes for a list of ASNs."""
        return {self._AS_TO_COUNTRY.get(asn) for asn in asns}

    def is_route_acceptable(self, prefix, next_hop, as_path):
        # check all supersets looking for policy with longest prefix match
        for net in [prefix] + list(reversed(prefix.supernet(0))):
            if net in self._PREFIX_REJECTS:
                for ccode in self._asns_ccodes(as_path):
                    # reject if any are in reject list
                    if ccode in self._PREFIX_REJECTS[net]:
                        return False
            if net in self._PREFIX_ALLOWS:
                # a whitelist policy was defined so we only allow if all
                # prefixes in the path are allowed
                return self._asns_ccodes(as_path).issubset(
                    self._PREFIX_ALLOWS[net])
        return True
