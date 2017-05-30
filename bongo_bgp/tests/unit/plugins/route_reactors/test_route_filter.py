from bongo_bgp.plugins.route_reactors import route_filter
from bongo_bgp.tests.unit.plugins.route_reactors import test_base


class TestLoggerPlugin(test_base.TestBaseReactor):
    DRIVER_CLASS = route_filter.FilteredAnnouncer
