class AcceptorBase(object):
    """A route acceptor decides whether or not a route should be accepted.

    The Bongo code will call the loaded route acceptor plugins every time an
    update is received from a neighbor that results in a new preferred path
    to a prefix. If any loaded acceptor returns False the route will be treated
    as rejected and sent to the route_reactors as rejected routes.

    Any exceptions thrown by the route rejector are currently ignored.
    """

    def is_route_acceptable(self, prefix, next_hop, as_path):
        """Called on new route causing topology change.

        :param prefix: a netaddr IPNetwork of the rejected route.
        :param nexthop: a netaddr IPAddress of the next hop.
        :param as_path: a list of autonomous systems for the route.
        """

    def process_thread(self):
        """Called from a separate thread.

        Drivers can put long running tasks in this method.
        """
