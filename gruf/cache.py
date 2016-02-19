import contextlib
import hashlib
import logging
import os
import time
import pathlib

LOG = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = os.environ.get('GRUF_CACHE_DIR',
        os.path.join(os.environ.get('HOME', ''), '.cache', 'gruf-cache'))
DEFAULT_CACHE_LIFETIME = 300

def line_iterator(fd):
    with contextlib.closing(fd) as fd:
        for line in fd:
            yield line

class Cache (object):
    def __init__(self, appid, cachedir=None, lifetime=None):
        # sanitize the appid
        appid = appid.replace('/', '_')

        self.cachedir = pathlib.Path(cachedir or DEFAULT_CACHE_DIR)
        self.appid = appid
        self.lifetime = (
                lifetime if lifetime is not None
                else DEFAULT_CACHE_LIFETIME)

        self.create_cache_dirs()

        LOG.debug('initialized cache with lifetime = %d',
                self.lifetime)

    def get_app_cache(self):
        return pathlib.Path(self.cachedir, self.appid)

    def path(self, key):
        return pathlib.Path(
                self.get_app_cache(),
                key[:2],
                key)

    def create_cache_dirs(self):
        if not self.cachedir.is_dir():
           self.cachedir.mkdir(mode=0700)

        appcache = self.get_app_cache()
        if not appcache.is_dir():
            appcache.mkdir(mode=0700)

        for prefix in range(256):
            prefixdir = pathlib.Path(appcache, '{:02x}'.format(prefix))
            if not prefixdir.is_dir():
                prefixdir.mkdir(mode=0700)

    def xform_key(self, key):
        '''we transform cache keys by taking their sha1 hash so that
        we don't need to worry about cache keys containing invalid
        characters'''

        newkey = hashlib.sha1(key)
        return newkey.hexdigest()

    def invalidate(self, key):
        '''Clear an item from the cache'''
        path = self.path(self.xform_key(key))
        try:
            LOG.debug('invalidate %s (%s)', key, path)
            path.unlink()
        except OSError:
            pass

    def invalidate_all(self):
        '''Clear all items from the cache'''

        LOG.debug('clearing cache')
        appcache = str(self.get_app_cache())
        for dirpath, dirnames, filenames in os.walk(appcache):
            for name in filenames:
                try:
                    pathlib.Path(dirpath, name).unlink()
                except OSError:
                    pass

    def store(self, key, content):
        path = self.path(self.xform_key(key))

        # ensure parent directories exist
        for prefix in path.parents:
            if prefix == self.cachedir:
                break

            if not prefix.is_dir():
                prefix.mkdir(parents=True)

        with path.open('wb') as fd:
            fd.write(content)
        LOG.debug('%s stored in cache', key)

    def load_fd(self, key, noexpire=False):
        '''Look up an item in the cache and return an open file
        descriptor for the object.  It is the caller's responsibility
        to close the file descriptor.'''

        path = self.path(self.xform_key(key))
        try:
            stat = path.stat()
            if not noexpire and stat.st_mtime < time.time() - self.lifetime:
                path.unlink()
                raise KeyError(key)

            LOG.debug('%s found in cache', key)
            return path.open('rb')
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
