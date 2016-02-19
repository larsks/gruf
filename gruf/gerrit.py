from __future__ import absolute_import

import functools
import hashlib
import json
import logging
import os
import shlex
import subprocess
import sys
import time
import urlparse
import yaml

from gruf.exc import *  # NOQA
from gruf.models import *  # NOQA
from . import git
from . import cache

LOG = logging.getLogger(__name__)

DEFAULT_REMOTE = 'gerrit'
DEFAULT_GERRIT_PORT = 29418
DEFAULT_CACHE_LIFETIME = 300  # 5 minutes

def parse_gerrit_remote(url):
    if not url.startswith('ssh://'):
        raise ValueError('This code only works with ssh:// repository urls')
    parsed = urlparse.urlparse(url)

    try:
        userhost, port = parsed.netloc.split(':')
    except ValueError:
        userhost = parsed.netloc
        port = None

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

def model(obj):
    def outside(func):
        def inside(*args, **kwargs):
            p = func(*args, **kwargs)
            return obj(p)

        return inside
    return outside

class Gerrit(object):
    json_iterator_result = ('query',)
    json_result = ('ls-projects',)
    raw_result = ('version', 'apropos',)
    unimplemented = ('stream-events',)

    default_querymap = {
            'mine': 'owner:self',
            'here': 'project:{project}',
            'open': 'status:open',
            }

    reconnect_interval = 5

    def __init__(self,
            remote=None,
            querymap=None,
            cache_lifetime=None):

        remote = remote or DEFAULT_REMOTE
        cache_lifetime = cache_lifetime or DEFAULT_CACHE_LIFETIME

        self.cache = cache.Cache(__name__, lifetime=cache_lifetime)

        self.remote = dict(zip(
            ('user', 'host', 'port', 'project'),
            git.get_remote_info(remote)))
        self.querymap = self.default_querymap
        if querymap is not None:
            self.querymap.update(querymap)

    def _ssh(self, args):
        '''Run the given command on the gerrit server, and
        return the subprocess.Popen object for the ssh connection.'''

        cmdvec = [
            'ssh',
            '-n',
            '-T',
            '-e', 'none',
            '-o', 'BatchMode=yes',
            '-o', 'ForwardAgent=no',
            '-o', 'ForwardX11=no',
            '-p', '{port}'.format(**self.remote),
            ]

        if self.remote.get('user'):
            cmdvec.append('{user}@{host}'.format(**self.remote))
        else:
            cmdvec.append('{host}'.format(**self.remote))

        cmdvec.append('gerrit')
        cmdvec.extend(args)

        p = subprocess.Popen(cmdvec,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        return p

    def ssh(self, *args, **kwargs):
        '''Ensure properly quoted arguments and then hand off command
        to the apppropriate connection handler depending on whether or
        not we need streaming support.
        
        Returns an iterator that iterates over lines returned by the
        server.'''

        streaming = kwargs.get('streaming')

        args = ['"{}"'.format(arg) if ' ' in arg else arg
                for arg in args]
        LOG.debug('gerrit %s', args)

        if not streaming:
            return self._return_cache(args)
        else:
            return self._return_stream(args)

    def _return_cache(self, args):
        '''return a cached value if available; otherwise fetch data
        from the server, cache the result, and return an iterator to
        the caller.'''

        # build a cache key from the arguments *and* our connection
        # credentials (because different users may get different
        # results).
        cachekey = hashlib.sha1('{user}:{host}:{port}'.format(**self.remote))
        for arg in args:
            cachekey.update(arg)

        cachekey = cachekey.hexdigest()
        LOG.debug('cache key %s', cachekey)

        try:
            res = self.cache.load_iter(cachekey)
        except KeyError:
            p = self._ssh(args)
            content = p.stdout.read()
            p.wait()

            if p.returncode != 0:
                raise GerritCommandError(p.stderr.read())

            self.cache.store(cachekey, content)
            res = self.cache.load_iter(cachekey)

        return res

    def _return_stream(self, args):
        '''This is a generator function that iterates over the lines
        returned by the server.  It will reconnect automatically if
        the connection drops.'''

        while True:
            p = self._ssh(args)
            while True:
                line = p.stdout.readline()
                if not line:
                    break

                yield line

            p.wait()
            if p.returncode == 0:
                break

            LOG.warn('lost connection (%d): %s',
                    p.returncode, p.stderr.read())
            time.sleep(self.reconnect_interval)

    def query_alias(self, k):
        '''subsitute query terms with replacements from
        self.querymap.'''

        return shlex.split(self.querymap.get(k, k).format(**self.remote))

    def xform_query_args(self, args):
        # this slightly funky looking use of sum() here is to flatten 
        # the result of the list comprehension, which is a list of
        # of lists explicitly to support expansions from query_alias
        return sum([
                self.query_alias(arg) if arg in self.querymap
                else [git.rev_parse(arg[4:])] if arg.startswith('git:')
                else [arg]
                for arg in args
                ], [])

    @model(QueryResponse)
    def query(self, *args, **kwargs):
        # transform any keyword arguments in
        # k:v strings, useful in queries.
        args = args + tuple('{}:{}'.format(k,v) for k,v in kwargs.items())

        args = self.xform_query_args(args)
        return self.ssh(*[
            'query',
            '--format', 'json',
            '--current-patch-set',
            '--comments',
            '--all-approvals',
            ] + args, **kwargs)

    @model(ProjectListResponse)
    def ls_projects(self, *args):
        return self.ssh('ls-projects', '--format', 'json', *args)

    @model(MemberListResponse)
    def ls_members(self, *args):
        return self.ssh('ls-members', *args)

    @model(UnstructuredResponse)
    def version(self, *args):
        return self.ssh('version', *args)

    @model(GroupListResponse)
    def ls_groups(self, *args):
        return self.ssh('ls-groups', '-v', *args)

    @model(UnstructuredResponse)
    def ban_commit(self, *args):
        return self.ssh('ban-commit', *args)

    @model(UnstructuredResponse)
    def create_branch(self, *args):
        return self.ssh('create-branch', *args)

    @model(UnstructuredResponse)
    def set_reviewers(self, *args):
        return self.ssh('set-reviewers', *args)

    @model(UnstructuredResponse)
    def rename_group(self, *args):
        return self.ssh('rename-group', *args)

    @model(UnstructuredResponse)
    def review(self, *args):
        args = self.xform_query_args(args)
        return self.ssh('review', *args)

    @model(EventStream)
    def stream_events(self, *args):
        return self.ssh('stream-events', *args, streaming=True)

    @model(UnstructuredResponse)
    def raw(self, *args):
        return self.ssh(*args)
