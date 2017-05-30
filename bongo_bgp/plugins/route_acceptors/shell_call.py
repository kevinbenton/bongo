import subprocess

from bongo_bgp import log
from bongo_bgp.plugins.route_acceptors import base


class ShellCall(base.AcceptorBase):
    """Calls an external program by shelling out."""

    path_to_external = "./sample_external.sh"

    def is_route_acceptable(self, prefix, next_hop, as_path):
        """Return code of 0 is True, anything else is False."""
        cmd = [self.path_to_external, prefix, next_hop] + as_path
        output, returncode = self._do_exec(cmd)
        log.debug("Output received from %s is %s and returncode is %s"
                  % (cmd, output, returncode))
        return returncode == 0

    def _do_exec(self, cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = p.communicate()[0]
        return output, p.returncode
