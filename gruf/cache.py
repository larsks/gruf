import os
import time
import contextlib
import logging

LOG = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = os.environ.get('GRUF_CACHE_DIR',
        os.path.join(os.environ.get('HOME', ''), '.cache', 'gruf-cache'))
DEFAULT_CACHE_LIFETIME = 600

def line_iterator(fd):
    with contextlib.closing(fd) as fd:
        for line in fd:
            yield line

class Cache (object):
    def __init__(self, appid, cachedir=None, lifetime=None):
        self.cachedir = cachedir or DEFAULT_CACHE_DIR
        self.lifetime = lifetime or DEFAULT_CACHE_LIFETIME
        self.mydir = os.path.join(self.cachedir, appid)

        if not os.path.isdir(self.cachedir):
            os.mkdir(self.cachedir, 0700)

        if not os.path.isdir(self.mydir):
            os.mkdir(self.mydir, 0700)

    def store(self, key, content):
        path = os.path.join(self.mydir, key)
        with open(path, 'w') as fd:
            fd.write(content)

    def load_fd(self, key):
        path = os.path.join(self.mydir, key)
        try:
            stat = os.stat(path)
            if stat.st_mtime < time.time() - self.lifetime:
                os.unlink(path)
                raise KeyError(key)

            LOG.debug('found %s in cache', key)
            return open(path)
        except OSError:
            raise KeyError(key)

    def load_iter(self, key):
        return line_iterator(self.load_fd(key))

    def load_lines(self, key):
        return list(self.load_iter(key))

    def load_raw(self, key):
        with self.load_fd(key) as fd:
            return fd.read()
