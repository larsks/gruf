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
from prettytable import PrettyTable

import pkg_resources

import gruf.models
import gruf.exc
import gruf.gerrit
import gruf.filters

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

    g = gruf.gerrit.Gerrit('.',
            remote=args.remote,
            querymap=config.get('querymap'))
    LOG.debug('remote %s', g.remote)

    cmd = args.cmd.pop(0)
    cmdargs = args.cmd

    cmd_func = cmd.replace('-', '_')
    try:
        res = getattr(g, cmd_func)(*cmdargs)
    except AttributeError:
        res = g.raw(cmd, *cmdargs)

    env = jinja2.Environment(
            loader = jinja2.FileSystemLoader([
                args.template_dir,
                pkg_resources.resource_filename(
                    __name__,
                    'templates'),
                ]))

    env.filters['to_json'] = gruf.filters.to_json
    env.filters['to_yaml'] = gruf.filters.to_yaml
    env.filters['strftime'] = gruf.filters.strftime

    template_name='{}/{}'.format(
            res.__class__.__name__,
            args.template or 'default')
    t = env.get_template(template_name)

    if res.streaming:
        for item in res:
            sys.stdout.write(
                t.render(item=item, config=config, args=args).encode('utf-8'))
    else:
        sys.stdout.write(
                t.render(result=res, config=config, args=args).encode('utf-8'))

if __name__ == '__main__':
    main()
