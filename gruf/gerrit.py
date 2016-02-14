import json
import logging
import os
import shlex
import subprocess
import sys
import urlparse
import yaml

from gruf.exc import *
from gruf.git import get_config, rev_parse

LOG = logging.getLogger(__name__)

class Gerrit(object):
    def __init__(self, remote=None):
        if remote is None:
            remote = self.get_gerrit_remote()

        LOG.debug('remote %s', remote)
        self.remote = self.parse_gerrit_remote(remote)

    def __str__(self):
        return '<Gerrit @ {host}>'.format(**self.remote)

    def __repr__(self):
        return str(self)

    def get_gerrit_remote(self):
        try:
            url = get_config('remote.gerrit.url')
        except subprocess.CalledProcessError as err:
            raise NoGerritRemote()

        return url

    def parse_gerrit_remote(self, url):
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

    def run(self, *args):
        return subprocess.check_output([
            'ssh', '-p', self.remote['port'],
            '-o', 'BatchMode=yes',
            '-o', 'ForwardX11=no',
            '-o', 'ForwardX11Trusted=no',
            '{user}@{host}'.format(**self.remote),
            'gerrit'] + list(args))

    def query(self, *args):
        res = self.run('query', '--format', 'JSON', *args)
        changes = []
        for line in res.splitlines()[:-1]:
            changes.append(json.loads(line))

        return changes

    def lookup_by_rev(self, rev):
        cid = rev_parse(rev)
        return self.query(cid)
