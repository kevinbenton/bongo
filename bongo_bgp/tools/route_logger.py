#!/usr/bin/env python

"""Log ExaBGP events."""

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
    for values in actions:
        keys = ['next_hop', 'myasn', 'action', 'prefix', 'path']
        d = {x[0]: x[1] for x in zip(keys, values)}
        log.info("%s" % d)
