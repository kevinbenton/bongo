import netaddr

from bongo_bgp.plugins.route_acceptors import asn_country_check
from bongo_bgp.tests.unit import base


class TestShellCall(base.BaseTestCase):
    """Notes about sample configs used for these tests.

    99.0.0.0/25 is whitelisted to US code.
    99.0.0.0/24 blacklists US and GB.
    10.2.0.0/16 blacklists DE.
    10.3.0.0/16 whitelists CN and US.

    ASN Country maps:
    65001,JP
    65002,US
    65003,CN
    65004,DE
    65005,GB
    """

    def setup_method(self, test_method):
        self.plugin = asn_country_check.ASNCountryCheck()
        self.next_hop = netaddr.IPAddress('1.1.1.1')

    def test_is_route_acceptable_true(self):
        allowed_for_US = map(netaddr.IPNetwork, ['99.0.0.0/25', '99.0.0.0/26',
                                                 '10.3.0.0/16', '10.2.0.0/16'])
        for a in allowed_for_US:
            self.assertTrue(self.plugin.is_route_acceptable(
                a, self.next_hop, [65002]))
        # whilelist of only CN and US
        pref = netaddr.IPNetwork('10.3.4.0/28')
        self.assertTrue(self.plugin.is_route_acceptable(
            pref, self.next_hop, [65002, 65003]))

    def test_is_route_acceptable_False(self):
        rejected_for_US_GB = map(netaddr.IPNetwork,
                                 ['99.0.0.0/24', '99.0.0.128/26'])

        for a in rejected_for_US_GB:
            for bad_hop in (65005, 65002):
                self.assertFalse(self.plugin.is_route_acceptable(
                    a, self.next_hop, [65001, 65003, bad_hop]))
