import netaddr

from bongo_bgp.plugins.route_reactors import logger
from bongo_bgp.tests.unit.plugins.route_reactors import test_base


class TestLoggerPlugin(test_base.TestBaseReactor):
    DRIVER_CLASS = logger.LOGToFile

    def test_file_contents(self):
        next_hop = netaddr.IPAddress('1.1.1.1')
        prefix = netaddr.IPNetwork('10.0.0.0/24')
        self.driver.route_rejected(prefix, next_hop, [])
        with open(self.driver.file_path, 'r') as f:
            for line in f:
                self.assertIn("rejected", line)
                self.assertIn("10.0.0.0/24", line)
                self.assertIn("1.1.1.1", line)
