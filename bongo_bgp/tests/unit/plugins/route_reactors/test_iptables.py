import mock

from bongo_bgp.plugins.route_reactors import iptables
from bongo_bgp.tests.unit.plugins.route_reactors import test_base


class TestFPRPFPlugin(test_base.TestBaseReactor):
    DRIVER_CLASS = iptables.IptablesReactor

    def setup_method(self, test_method):
        super(TestFPRPFPlugin, self).setup_method(test_method)
        self._save = mock.patch.object(self.driver,
                                       '_iptables_save').start()
        self._restore = mock.patch.object(self.driver,
                                          '_iptables_restore').start()

    def after_reject_assertions(self, prefix, next_hop):
        # ensure prefix is banned
        found_block = False
        for call in self._restore.mock_calls:
            for rule in call[1][0]:
                if str(prefix) in rule:
                    found_block = True
                    break
        self.assertTrue(found_block)
        self._restore.reset_mock()
