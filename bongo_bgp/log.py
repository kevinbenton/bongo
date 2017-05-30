import logging
import sys


DEBUG = True

kw = {'format': '%(asctime)s %(message)s',
      'stream': sys.stderr}
if DEBUG:
    kw['level'] = logging.DEBUG

logging.basicConfig(**kw)
debug = logging.debug
info = logging.info
warning = logging.warning
error = logging.error
