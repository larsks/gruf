import contextlib
import hashlib
import logging
import os
import time

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
        self.lifetime = (
                lifetime if lifetime is not None
                else DEFAULT_CACHE_LIFETIME)
        self.mydir = os.path.join(self.cachedir, appid)

        LOG.debug('initialized cache with lifetime = %d',
                self.lifetime)

        if not os.path.isdir(self.cachedir):
            os.mkdir(self.cachedir, 0700)

        if not os.path.isdir(self.mydir):
            os.mkdir(self.mydir, 0700)

    def xform_key(self, key):
        '''we transform cache keys by taking their sha1 hash so that
        we don't need to worry about cache keys containing invalid
        characters'''

        newkey = hashlib.sha1(key)
        return newkey.hexdigest()

    def invalidate(self, key):
        '''Clear an item from the cache'''
        path = os.path.join(self.mydir, self.xform_key(key))
        try:
            LOG.debug('invalidate %s (%s)', key, path)
            os.unlink(path)
        except OSError:
            pass

    def invalidate_all(self):
        '''Clear all items from the cache'''

        LOG.debug('clearing cache')
        for dirpath, dirnames, filenames in os.walk(self.mydir):
            for name in filenames:
                try:
                    os.unlink(os.path.join(dirpath, name))
                except OSError:
                    pass

    def store(self, key, content):
        path = os.path.join(self.mydir, self.xform_key(key))
        with open(path, 'w') as fd:
            fd.write(content)
        LOG.debug('%s stored in cache', key)

    def load_fd(self, key, noexpire=False):
        '''Look up an item in the cache and return an open file
        descriptor for the object.  It is the caller's responsibility
        to close the file descriptor.'''

        path = os.path.join(self.mydir, self.xform_key(key))
        try:
            stat = os.stat(path)
            if not noexpire and stat.st_mtime < time.time() - self.lifetime:
                os.unlink(path)
                raise KeyError(key)

            LOG.debug('%s found in cache', key)
            return open(path)
        except OSError:
            LOG.debug('%s not found in cache', key)
            raise KeyError(key)

    def load_iter(self, key, noexpire=None):
        '''Look up up an item in the cache and return a line iterator.
        The underlying file descriptor will be closed once all lines
        have been consumed.'''
        return line_iterator(self.load_fd(key, noexpire=noexpire))

    def load_lines(self, key, noexpire=None):
        '''Lookup an item in the cache and return a list of
        lines.'''
        return list(self.load_iter(key, noexpire=noexpire))

    def load_raw(self, key, noexpire=None):
        '''Lookup an item in the cache and return the raw content of
        the file as a string.'''
        with self.load_fd(key, noexpire=noexpire) as fd:
            return fd.read()
