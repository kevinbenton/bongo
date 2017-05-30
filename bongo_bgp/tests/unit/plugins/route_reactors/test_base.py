import netaddr

from bongo_bgp.plugins.route_reactors import base
from bongo_bgp.tests.unit import base as test_base


class TestBaseReactor(test_base.BaseTestCase):

    DRIVER_CLASS = base.ReactorBase

    def setup_method(self, test_method):
        self.driver = self.DRIVER_CLASS()

    def after_accept_assertions(self, prefix, next_hop):
        pass

    def after_remove_assertions(self, prefix, next_hop):
        pass

    def after_reject_assertions(self, prefix, next_hop):
        pass

    def test_route_accepted(self):
        next_hop = netaddr.IPAddress('1.1.1.1')
        prefix = netaddr.IPNetwork('10.0.0.0/24')
        self.assertIsNone(self.driver.route_accepted(prefix, next_hop, []))
        self.after_accept_assertions(prefix, next_hop)

    def test_route_rejected(self):
        next_hop = netaddr.IPAddress('1.1.1.1')
        prefix = netaddr.IPNetwork('10.0.0.0/24')
        self.assertIsNone(self.driver.route_rejected(prefix, next_hop, []))
        self.after_reject_assertions(prefix, next_hop)

    def test_route_removed(self):
        next_hop = netaddr.IPAddress('1.1.1.1')
        prefix = netaddr.IPNetwork('10.0.0.0/24')
        self.assertIsNone(self.driver.route_removed(prefix, next_hop, []))
        self.after_remove_assertions(prefix, next_hop)

    def test_route_accepted_remove_rejected_accepted_removed(self):
        next_hop = netaddr.IPAddress('1.1.1.1')
        prefix = netaddr.IPNetwork('10.0.0.0/24')
        self.assertIsNone(self.driver.route_accepted(prefix, next_hop, []))
        self.after_accept_assertions(prefix, next_hop)
        self.assertIsNone(self.driver.route_removed(prefix, next_hop, []))
        self.after_remove_assertions(prefix, next_hop)
        self.assertIsNone(self.driver.route_rejected(prefix, next_hop, []))
        self.after_reject_assertions(prefix, next_hop)
        self.assertIsNone(self.driver.route_accepted(prefix, next_hop, []))
        self.after_accept_assertions(prefix, next_hop)
        self.assertIsNone(self.driver.route_removed(prefix, next_hop, []))
        self.after_remove_assertions(prefix, next_hop)

    def test_200_routes_accepted_and_removed(self):
        next_hop = netaddr.IPAddress('1.1.1.1')
        prefix = netaddr.IPNetwork('10.0.0.0/24')
        for i in range(200):
            prefix = prefix.next()
            self.assertIsNone(self.driver.route_accepted(prefix, next_hop, []))
            self.after_accept_assertions(prefix, next_hop)
        for i in range(200):
            prefix = prefix.previous()
            self.assertIsNone(self.driver.route_removed(prefix, next_hop, []))
            self.after_remove_assertions(prefix, next_hop)
