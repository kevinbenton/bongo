#!/usr/bin/env python

"""Exabgp doesn't redistribute routes so this small script does it for us."""

import sys
import time

from bongo_bgp import log
from bongo_bgp import route_parser


while True:
    line = sys.stdin.readline().strip()
    if not line:
        time.sleep(1)
        continue
    actions = route_parser.parse_exabgp_line(line)
    if not actions:
        continue
    for next_hop, myasn, action, prefix, path in actions:
        if action == 'announce':
            if myasn in path:
                # don't make a loop
                continue
            log.debug("AS %s not in %s" % (type(myasn), map(type, path)))
            message = ('announce route %s next-hop self as-path [ %s ]' %
                       (prefix, ' '.join(map(str, [myasn] + path))))
        elif action == 'withdraw':
            message = ('withdraw route %s next-hop self' % prefix)
        else:
            raise RuntimeError('bad action %s' % action)
    sys.stdout.write(message + '\n')
    sys.stdout.flush()
