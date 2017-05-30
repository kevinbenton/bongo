from datetime import datetime
import os
import sys

from bongo_bgp.plugins.route_reactors import base

_THIS_DIR = os.path.dirname(sys.modules[__name__].__file__)
_LOG_DIR = os.path.join(_THIS_DIR, '..', '..', '..', 'logs')


class LOGToFile(base.ReactorBase):
    """Logs to a file on events.

    The default log file is in the repo 'logs' folder.
    """
    file_path = os.path.join(_LOG_DIR, 'logged_events.log')

    def __init__(self):
        with open(self.file_path, "w+") as f:
            f.truncate()

    def route_accepted(self, prefix, next_hop, as_path):
        self._log("Route to %s via %s was accepted. Path: %s"
                  % (prefix, next_hop, as_path))

    def route_removed(self, prefix, next_hop, as_path):
        self._log("Route to %s via %s was removed. Path: %s"
                  % (prefix, next_hop, as_path))

    def route_rejected(self, prefix, next_hop, as_path):
        self._log("Route to %s via %s was rejected. Path: %s"
                  % (prefix, next_hop, as_path))

    def _log(self, msg):
        formated = "%s: %s\n" % (str(datetime.now()), msg)
        with open(self.file_path, 'a+') as f:
            f.write(formated)
