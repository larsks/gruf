#!/usr/bin/python

import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
import urlparse
import yaml
import jinja2

import pkg_resources

from gruf.gerrit import Gerrit
from gruf.exc import *
from gruf import git
from gruf import filters

LOG = logging.getLogger(__name__)
CONFIG_DIR = os.path.join(
        os.environ.get('XDG_CONFIG_DIR',
            os.path.join(os.environ['HOME'], '.config')),
        'gruf')
QUERYMAP = {
        'mine': 'owner:self',
        'open': 'status:open',
        'here': 'project:{project}',
        }

class ResultFilter(object):
    def __init__(self, args, config):
        self.config = config
        self.args = args

        self.env = jinja2.Environment(
                loader = jinja2.FileSystemLoader([
                    args.template_dir,
                    pkg_resources.resource_filename(
                        __name__,
                        'templates'),
                    ]))

        self.env.filters['to_json'] = filters.to_json
        self.env.filters['to_yaml'] = filters.to_yaml

    def handle_query(self, res):
        template = (self.args.template if self.args.template
                else '@default')

        if template.startswith('@'):
            try:
                t = self.env.get_template(template[1:])
            except jinja2.TemplateNotFound:
                t = self.env.get_template(template[1:] + '.j2')
        else:
            t = self.env.from_string(template)

        for change in res:
            out = t.render(change=change, **change)
            sys.stdout.write(out)
            if not out.endswith('\n'):
                sys.stdout.write('\n')

    def handle_ls_projects(self, res):
        for proj in res:
            print '{name} {state}'.format(**proj)

    def handle(self, cmd, results):
        try:
            filter = getattr(self, 'handle_%s' % cmd.replace('-', '_'))
        except AttributeError:
            raise NoFilter(cmd)

        filter(results)

def get_gerrit_remote():
    return git.get_config('remote.gerrit.url')

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--verbose', '-v',
                   action='store_const',
                   const='INFO',
                   dest='loglevel')
    p.add_argument('--debug', '-d',
                   action='store_const',
                   const='DEBUG',
                   dest='loglevel')
    p.add_argument('--remote', '-r')
    p.add_argument('--config', '-f',
            default=os.path.join(CONFIG_DIR, 'gruf.yml'))
    p.add_argument('-t', '--template')
    p.add_argument('--template-dir', '-T')
    p.add_argument('--yaml', '-y',
            action='store_true')
    p.add_argument('--json', '-j',
            action='store_true')
    p.add_argument('cmd', nargs=argparse.REMAINDER)

    return p.parse_args()

def main():
    args = parse_args()
    if hasattr(args, 'template_dir'):
        if args.template_dir is None:
            args.template_dir = os.path.join(
                    os.path.dirname(args.config), 'templates')

    logging.basicConfig(
        level=args.loglevel)

    LOG.debug('args %s', args)

    try:
        with open(args.config) as fd:
            config = yaml.load(fd)
    except IOError:
        config = {}

    filter = ResultFilter(args, config)

    if args.remote is None:
        args.remote = get_gerrit_remote()

    LOG.debug('remote %s', args.remote)
    g = Gerrit(args.remote,
            querymap=config.get('querymap'))

    cmd = args.cmd.pop(0)
    cmdargs = [git.rev_parse(arg[4:])
            if arg.startswith('git:')
            else arg
            for arg in args.cmd]

    try:
        res = getattr(g, cmd)(*cmdargs)
    except subprocess.CalledProcessError:
        LOG.error('gerrit command failed')
        sys.exit(1)

    # LKS: This is too hacky.
    if args.yaml:
        sys.stdout.write(yaml.safe_dump(list(res), default_flow_style=False))
    elif args.json:
        sys.stdout.write(json.dumps(list(res), indent=2))
    else:
        try:
            filter.handle(cmd, res)
        except NoFilter:
            for item in res:
                sys.stdout.write(item)
                sys.stdout.write('\n')

if __name__ == '__main__':
    main()
