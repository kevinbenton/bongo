import mock
from bongo_bgp.plugins.route_acceptors import shell_call
from bongo_bgp.tests.unit import base


class TestShellCall(base.BaseTestCase):

    def setup_method(self, test_method):
        self.plugin = shell_call.ShellCall()
        self.executor = mock.patch.object(self.plugin, '_do_exec',
                                          return_value=('', 0)).start()

    def test_is_route_acceptable_true(self):
        self.assertTrue(self.plugin.is_route_acceptable('1', '2', ['a', 's']))
        self.executor.assert_called_once_with(
            [self.plugin.path_to_external, '1', '2', 'a', 's'])

    def test_is_route_acceptable_False(self):
        self.executor.return_value = ('', 1)
        self.assertFalse(self.plugin.is_route_acceptable('1', '2', ['a', 's']))
        self.executor.assert_called_once_with(
            [self.plugin.path_to_external, '1', '2', 'a', 's'])
