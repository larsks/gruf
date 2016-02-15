import json
import logging
import os
import shlex
import subprocess
import sys
import urlparse
import yaml
import functools

from gruf.exc import *
from gruf.git import get_config, rev_parse

LOG = logging.getLogger(__name__)

def parse_gerrit_remote(url):
    parsed = urlparse.urlparse(url)
    userhost, port = parsed.netloc.split(':')

    try:
        user, host = userhost.split('@')
    except ValueError:
        user = None
        host = userhost

    project = parsed.path[1:]
    if project.endswith('.git'):
        project = project[:-4]

    return {'user': user,
            'host': host,
            'port': port,
            'project': project,
            'url': url,
            }

def jsoniterator(func):
    def _(*args, **kwargs):
        res = func(*args, **kwargs)
        LOG.debug('%s res %s', func.__name__, res)
        items = (json.loads(line)
                for line in res.splitlines())
        return (item
                for item in items
                if item.get('type') != 'stats')

    return _

def lineiterator(func):
    def _(*args, **kwargs):
        res = func(*args, **kwargs)
        return res.splitlines()

    return _

def mapiterator(func):
    def _(*args, **kwargs):
        res = func(*args, **kwargs)
        items = json.loads(res)
        return (dict(name=k, **v) for k,v in items.items())

    return _

class Gerrit(object):
    json_line_result = ('query',)
    json_map_result = ('ls-projects',)
    unimplemented = ('stream-events',)

    default_querymap = {
            'mine': 'owner:self',
            'here': 'project:{project}',
            'open': 'status:open',
            }

    def __init__(self, url, querymap=None):
        self.remote = parse_gerrit_remote(url)
        self.querymap = self.default_querymap
        if querymap is not None:
            self.querymap.update(querymap)

    def ssh(self, *args, **kwargs):
        # transform any keyword arguments in
        # k:v strings, useful in queries.
        args = args + tuple('{}:{}'.format(k,v) for k,v in kwargs.items())

        # quote any arguments containing spaces.
        args = ['"{}"'.format(arg) if ' ' in arg else arg
                for arg in args]

        LOG.debug('running %s', args)
        return subprocess.check_output([
            'ssh',
            '-o', 'ForwardAgent=no',
            '-o', 'ForwardX11=no',
            '-p', '{port}'.format(**self.remote),
            '{user}@{host}'.format(**self.remote),
            'gerrit',
            ] + list(args))

    def query_alias(self, k):
        return self.querymap.get(k, k).format(**self.remote)

    @jsoniterator
    def query(self, *args, **kwargs):
        args = [self.query_alias(arg) for arg in args]
        return self.ssh(*['query', '--format', 'json'] + args, **kwargs)

    def __getattr__(self, k):
        k = k.replace('_', '-')
        if k in self.unimplemented:
            raise NotImplementedError(k)
        elif k in self.json_line_result:
            return functools.partial(
                    jsoniterator(self.ssh), k, '--format', 'json')
        elif k in self.json_map_result:
            return functools.partial(
                    mapiterator(self.ssh), k, '--format', 'json')
        else:
            return functools.partial(
                    lineiterator(self.ssh), k)
