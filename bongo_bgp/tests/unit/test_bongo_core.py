import mock
import netaddr

from bongo_bgp import bongo_core
from bongo_bgp.tests.unit import base


class TestCore(base.BaseTestCase):

    def setup_method(self, test_method):
        self.acceptor = mock.Mock()
        self.reactor = mock.Mock()
        self.core = bongo_core.BongoCore([self.acceptor], [self.reactor],
                                         wait_on_queue=False)

    def _update_data(self):
        as_path = [1111, 2222, 3333, 4444]
        prefix = netaddr.IPNetwork('1.1.1.0/24')
        next_hop = netaddr.IPAddress('2.2.2.2')
        return as_path, prefix, next_hop

    def test_load_core(self):
        acceptors = ['bongo_bgp.plugins.route_acceptors.asn_country_check.'
                     'ASNCountryCheck']
        reacts = ['bongo_bgp.plugins.route_reactors.logger.LOGToFile']
        self.core = bongo_core.load_core(acceptors, reacts)
        self.assertTrue(isinstance(self.core, bongo_core.BongoCore))
        as_path, prefix, next_hop = self._update_data()
        self.core.queue_route_update(prefix, next_hop, as_path, 'add')
        self.core.wait_on_queue = False
        self.core.process()
        last = ''
        with open(self.core.reactors[0].file_path, 'r') as r:
            for l in r:
                last = l
        self.assertIn("accepted", last)

        # this update will be rejected by the asn_country_check sample policy
        prefix = netaddr.IPNetwork('99.0.0.128/25')
        as_path = [65002]
        self.core.queue_route_update(prefix, next_hop, as_path, 'add')
        self.core.process()
        with open(self.core.reactors[0].file_path, 'r') as r:
            for l in r:
                last = l
        self.assertIn("rejected", last)

    def test_process_route_update_add(self):
        as_path, prefix, next_hop = self._update_data()
        self.core.queue_route_update(prefix, next_hop, as_path, 'add')
        self.core.process()
        self.assertFalse(self.reactor.route_removed.called)
        self.assertFalse(self.reactor.route_rejected.called)
        self.reactor.route_accepted.assert_called_once_with(
            prefix, next_hop, as_path)

    def test_process_route_update_add_reject(self):
        self.acceptor.is_route_acceptable.return_value = False
        as_path, prefix, next_hop = self._update_data()
        self.core.queue_route_update(prefix, next_hop, as_path, 'add')
        self.core.process()
        self.assertFalse(self.reactor.route_removed.called)
        self.assertFalse(self.reactor.route_accepted.called)
        self.reactor.route_rejected.assert_called_once_with(
            prefix, next_hop, as_path)

    def test_process_route_update_remove(self):
        as_path, prefix, next_hop = self._update_data()
        self.core.queue_route_update(prefix, next_hop, as_path, 'remove')
        self.core.process()
        self.assertFalse(self.reactor.route_accepted.called)
        self.assertFalse(self.reactor.route_rejected.called)
        self.reactor.route_removed.assert_called_once_with(
            prefix, next_hop, as_path)
