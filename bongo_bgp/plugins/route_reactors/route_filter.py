import sys

from bongo_bgp.plugins.route_reactors import base


class FilteredAnnouncer(base.ReactorBase):
    """Takes accepted routes and reannounces them prepending our asn."""

    MY_ASN = 65001

    def route_accepted(self, prefix, next_hop, as_path):
        """propagate route downstream with our ASN in first path slot."""
        if self.MY_ASN in as_path:
            # loop prevention
            return
        self._write_out(
            "announce route %s next-hop self as-path [ %s ]"
            % (prefix, ' '.join(map(str, [self.MY_ASN] + as_path)))
        )

    def route_removed(self, prefix, next_hop, as_path):
        self._write_out("withdraw route %s next-hop self" % prefix)

    def route_rejected(self, prefix, next_hop, as_path):
        self.route_removed(prefix, next_hop, as_path)

    def _write_out(self, message):
        sys.stdout.write(message + '\n')
        sys.stdout.flush()
