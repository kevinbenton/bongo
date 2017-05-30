from bongo_bgp import log
import netaddr
from six.moves import queue
import sys
import threading


def import_drivers(acceptors, reactors):
    a_drivers, r_drivers = [], []
    for paths, insts in ((acceptors, a_drivers), (reactors, r_drivers)):
        for p in paths:
            insts.append(_import_class(p)())

    return a_drivers, r_drivers


def _import_class(class_path):
    module, dot, cls = class_path.rpartition('.')
    try:
        __import__(module)
        return getattr(sys.modules[module], cls)
    except Exception as e:
        log.error("Could not import %s due to %s." % (class_path, e))
        raise SystemExit(1)


def load_core(acceptor_strings, reactor_strings):
    a_drivers, r_drivers = import_drivers(acceptor_strings, reactor_strings)
    return BongoCore(a_drivers, r_drivers)


class BongoCore(object):
    """Receives route updates and controls interactions with drivers.

    Routes are sent to the core with queue_route_update.
    process_and_wait will drain from the queue indefinitely and pass
    route updates to the acceptor drivers. The resulting accept/reject
    is then passed onto the reactor drivers.
    """

    def __init__(self, acceptors, reactors, wait_on_queue=True):
        self.acceptors = acceptors or []
        self.reactors = reactors or []
        self.route_process_queue = queue.Queue()
        self.wait_on_queue = wait_on_queue

    def queue_route_update(self, prefix, next_hop, as_path, action):
        assert isinstance(prefix, netaddr.IPNetwork)
        assert isinstance(next_hop, netaddr.IPAddress)
        assert isinstance(as_path, list)
        assert action in ('add', 'remove')
        route = (prefix, next_hop, as_path, action)
        self.route_process_queue.put(route)

    def process(self):
        while True:
            try:
                job = self.route_process_queue.get(timeout=1000)
                self._process_route(*job)
            except queue.Empty:
                pass
            if not self.wait_on_queue:
                return

    def start_driver_process_threads(self):
        for drv in self.reactors + self.acceptors:
            t = threading.Thread(target=drv.process_thread)
            t.daemon = True
            t.start()

    def _process_route(self, prefix, next_hop, as_path, action):
        if action == 'add':
            if self._is_route_accepted(prefix, next_hop, as_path):
                self._send_accept_to_reactors(prefix, next_hop, as_path)
            else:
                self._send_reject_to_reactors(prefix, next_hop, as_path)
        else:
            self._send_remove_to_reactors(prefix, next_hop, as_path)

    def _send_remove_to_reactors(self, prefix, next_hop, as_path):
        log.debug("Route to %s via %s was removed" % (prefix, next_hop))
        self._call_on_reactors('route_removed', prefix, next_hop, as_path)

    def _send_accept_to_reactors(self, prefix, next_hop, as_path):
        log.debug("Route to %s via %s was accepted" % (prefix, next_hop))
        self._call_on_reactors('route_accepted', prefix, next_hop, as_path)

    def _send_reject_to_reactors(self, prefix, next_hop, as_path):
        log.warning("Route to %s via %s was rejected" % (prefix, next_hop))
        self._call_on_reactors('route_rejected', prefix, next_hop, as_path)

    def _call_on_reactors(self, method, *args):
        for drv in self.reactors:
            m = getattr(drv, method)
            try:
                m(*args)
            except Exception as e:
                log.error("Route reactor %s raise an exception while "
                          "processing a %s call with args %s: %s"
                          % (drv, method, args, e))

    def _is_route_accepted(self, prefix, next_hop, as_path):
        for drv in self.acceptors:
            try:
                if not drv.is_route_acceptable(prefix, next_hop, as_path):
                    return False
            except Exception as e:
                log.warning("Driver %s raise an exception while checking "
                            "if a route was acceptable so the route has "
                            "been rejected. %s" % (drv, e))
                return False
        return True
