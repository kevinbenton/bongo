#!/usr/bin/env python
import netaddr
import random
import sys
import time


"""
Script to be used with ExaBGP as an announce-routes script to announce
and withdraw a passed in prefix in an endless loop with short random
intervals in between.
"""


def _expand(routes):
    expanded = []
    for r in routes:
        if '*' not in r:
            expanded.append(r)
            continue
        prefix, multiplier = r.split('*')
        for r in list(netaddr.IPNetwork(prefix).
                      subnet(24))[0:int(multiplier):2]:
            expanded.append(r)
    return expanded


if __name__ == "__main__":
    routes = sys.argv[1:]
    perm_routes = _expand([x[1:] for x in routes if x.startswith('P')])
    flapping_routes = _expand([x for x in routes if not x.startswith('P')])

    # wait for startup
    time.sleep(5)

    # announce all routes
    for route in perm_routes + flapping_routes:
        sys.stdout.write('announce route %s next-hop self\n' % route)
        sys.stdout.flush()
        time.sleep(0.1)

    # Loop endlessly to allow ExaBGP to continue running
    while True:
        time.sleep(random.randint(30, 60))
        # withdraw and re-add route
        route = random.choice(flapping_routes)
        sys.stdout.write('withdraw route %s next-hop self\n' % route)
        sys.stdout.flush()
        time.sleep(random.randint(30, 60))
        sys.stdout.write('announce route %s next-hop self\n' % route)
        sys.stdout.flush()
