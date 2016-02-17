from __future__ import absolute_import

import json
import logging
import os
import shlex
import subprocess
import sys
import urlparse
import yaml
import functools

from gruf.exc import *  # NOQA
from gruf.models import *  # NOQA
from gruf.git import get_remote_info, rev_parse

LOG = logging.getLogger(__name__)
GERRIT_PORT = 29418

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

def stdout_reader(p):
    while True:
        line = p.stdout.readline().decode('utf-8')
        LOG.debug('line %s', line)
        if not line:
            break

        yield line.strip()

    p.wait()
    if p.returncode != 0:
        raise GerritCommandError(p.stderr.read())

def model(obj):
    def outside(func):
        def inside(*args, **kwargs):
            p = func(*args, **kwargs)
            return obj(stdout_reader(p))

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

    def __init__(self, remote=None, querymap=None):
        remote = remote if remote is not None else 'gerrit'

        self.remote = dict(zip(
            ('user', 'host', 'port', 'project'),
            get_remote_info(remote)))
        self.querymap = self.default_querymap
        if querymap is not None:
            self.querymap.update(querymap)

    def ssh(self, *args, **kwargs):
        # quote any arguments containing spaces.
        args = ['"{}"'.format(arg) if ' ' in arg else arg
                for arg in args]

        LOG.debug('running %s', args)

        port = self.remote.get('port', GERRIT_PORT)
        cmdvec = [
            'ssh',
            '-n',
            '-T',
            '-e', 'none',
            '-o', 'BatchMode=yes',
            '-o', 'ForwardAgent=no',
            '-o', 'ForwardX11=no',
            '-p', '{}'.format(port),
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

    def query_alias(self, k):
        return shlex.split(self.querymap.get(k, k).format(**self.remote))

    def xform_query_args(self, args):
        # this slightly funky looking use of sum() here is to flatten 
        # the result of the list comprehension, which is a list of
        # of lists explicitly to support expansions from query_alias
        return sum([
                self.query_alias(arg) if arg in self.querymap
                else [rev_parse(arg[4:])] if arg.startswith('git:')
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
        return self.ssh('stream-events', *args)

    @model(UnstructuredResponse)
    def raw(self, *args):
        return self.ssh(*args)
