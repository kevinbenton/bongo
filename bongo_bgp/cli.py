import argparse
from bongo_bgp import bongo_core
from bongo_bgp import log
from bongo_bgp import route_parser
import threading


def main():
    parser = argparse.ArgumentParser(description='Bongo Route Processor.')
    parser.add_argument('--acceptor', action='append',
                        help="Class path to an acceptor driver. "
                             "(repeat multiple times to load multiple)")
    parser.add_argument('--reactor', action='append',
                        help="Class path to a reactor driver."
                             "(repeat multiple times to load multiple)")
    parser.add_argument('--route-updates-path',
                        help="Path to file to watch for ExaBGP route updates."
                             "If no path is specified, updates are expected "
                             "via STDIN")
    args = parser.parse_args()
    core = bongo_core.load_core(args.acceptor or [], args.reactor or [])
    route_watcher = route_parser.FileWatcher(
        path=args.route_updates_path,
        route_receiver=core.queue_route_update)
    try:
        core.start_driver_process_threads()
        core_thread = threading.Thread(target=core.process)
        core_thread.daemon = True
        core_thread.start()
        route_watcher.watch()
    except KeyboardInterrupt:
        log.error("Keyboard Interrupt")
    core.wait_on_queue = False


if __name__ == '__main__':
    main()
