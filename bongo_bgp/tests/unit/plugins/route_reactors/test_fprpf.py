import mock
import netaddr

from bongo_bgp.plugins.route_reactors import fprpf
from bongo_bgp.tests.unit.plugins.route_reactors import test_base


class TestFPRPFPlugin(test_base.TestBaseReactor):
    DRIVER_CLASS = fprpf.FPRPFReactor

    def setup_method(self, test_method):
        self.DRIVER_CLASS.PEER_IP_MAC_MAP[
            netaddr.IPAddress('1.1.1.1')] = '00:11:22:33:44:55'
        super(TestFPRPFPlugin, self).setup_method(test_method)
        self._of_exec = mock.patch.object(self.driver, '_of_exec').start()

    def after_accept_assertions(self, prefix, next_hop):
        self.driver.process_thread(wait_for_more=False)

    def after_remove_assertions(self, prefix, next_hop):
        self.driver.process_thread(wait_for_more=False)

    def after_reject_assertions(self, prefix, next_hop):
        self.driver.process_thread(wait_for_more=False)
