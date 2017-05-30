class ReactorBase(object):
    """A route reactor performs actions after routes are accepted/rejected.

    The Bongo code will call the loaded route reactor plugins every time a
    route is accepted or rejected by the bongo route acceptors and whenever
    a route is withdrawn from BGP. The reactor can then take action
    (install/remove ACL entries, firewall rules, etc).

    Any exceptions thrown by the route reactors are currently ignored.
    """

    def route_accepted(self, prefix, next_hop, as_path):
        """Called on route acceptance.

        :param prefix: a netaddr IPNetwork of the accepted route.
        :param nexthop: a netaddr IPAddress of the next hop.
        :param as_path: a list of ASNs in the BGP path
        """

    def route_rejected(self, prefix, next_hop, as_path):
        """Called on route rejection.

        :param prefix: a netaddr IPNetwork of the rejected route.
        :param nexthop: a netaddr IPAddress of the next hop.
        :param as_path: a list of ASNs in the BGP path
        """

    def route_removed(self, prefix, next_hop, as_path):
        """Called when a route is no longer advertised.

        :param prefix: a netaddr IPNetwork of the removed route.
        :param nexthop: a netaddr IPAddress of the next hop.
        :param as_path: a list of ASNs in the BGP path
        """

    def process_thread(self):
        """Called from a separate thread.

        Drivers can put long running tasks in this method.
        """
