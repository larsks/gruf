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

from gruf.exc import *
from gruf.gerrit import Gerrit
from gruf.git import rev_parse

LOG = logging.getLogger(__name__)
XDG_CONFIG_DIR = os.environ.get(
    'XDG_CONFIG_DIR',
    os.path.join(os.environ['HOME'], '.config'))
DEFAULT_CONFIG_DIR=os.path.join(XDG_CONFIG_DIR, 'gruf')
DEFAULT_TEMPLATE = '''{{number}} {{owner.username}} {{subject}}
'''

QUERYMAP = {
        'mine': 'owner:self',
        'open': 'status:open',
        'here': 'project:{project}',
        }

RAW_COMMANDS = [
    'ban-commit', 'create-branch',
    'ls-groups', 'ls-members', 'ls-projects',
    'rename-group', 'set-head', 'set-reviewers',
    'version',
    ]

def handle_url_for(args, extra_args, remote, config):
    if args.git:
        res = remote.lookup_by_rev(args.rev)
    else:
        res = remote.query(*[args.rev])

    if len(res) == 1:
        print res[0]['url']
    else:
        raise TooManyChanges()

def handle_view(args, extra_args, remote, config):
    if args.git:
        res = remote.lookup_by_rev(args.rev)
    else:
        res = remote.query(*[args.rev])

    if len(res) == 1:
        subprocess.call(['xdg-open', res[0]['url']])
    else:
        raise TooManyChanges()

def handle_get(args, extra_args, remote, config):
    print remote.remote.get(args.attr, '')

def handle_raw(args, extra_args, remote, config):
    if args.args and args.args[0] == '--':
        args.args = args.args[1:]

    res = remote.run(*[args._command] + extra_args + args.args)
    sys.stdout.write(res)

def handle_review(args, extra_args, remote, config):
    if args.git:
        args.rev = rev_parse(args.rev)

    LOG.debug('review %s', args.rev)

    sys.stdout.write(remote.run(*['review'] + extra_args + [args.rev]))

def handle_query(args, extra_args, remote, config):
    LOG.debug('pre-parsed %s', args.query)

    QUERYMAP.update(config.get('queries', {}))
    query = [
            (shlex.split(QUERYMAP[term].format(**remote.remote))
                if term in QUERYMAP
                else [term.format(**remote.remote)])
                for term in args.query]

    query = sum(query, [])
    LOG.debug('post-parsed %s', query)

    res = remote.query(*(extra_args + query))

    if args.format == 'json':
        sys.stdout.write(json.dumps(res, indent=2))
    elif args.format == 'yaml':
        sys.stdout.write(yaml.safe_dump(res, default_flow_style=False))
    else:
        env = jinja2.Environment(
                loader = jinja2.FileSystemLoader([
                    args.template_dir,
                    pkg_resources.resource_filename(
                        __name__,
                        'templates'),
                    ]))

        if args.template.startswith('@'):
            try:
                t = env.get_template(args.template[1:])
            except jinja2.exceptions.TemplateNotFound:
                t = env.get_template(args.template[1:] + '.j2')
        else:
            t = env.from_string(args.template)

        for change in res:
            out = t.render(**change)
            sys.stdout.write(out)
            if not out.endswith('\n'):
                sys.stdout.write('\n')

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
    p.add_argument('--config', '-f',
            default=os.path.join(DEFAULT_CONFIG_DIR, 'gruf.yml'))

    sub = p.add_subparsers(help='Subcommands')
    p_query = sub.add_parser('query')
    p_query.add_argument('--json', '-j',
            action='store_const',
            const='json',
            dest='format')
    p_query.add_argument('--yaml', '-y',
            action='store_const',
            const='yaml',
            dest='format')
    p_query.add_argument('--template-dir', '-T')
    p_query.add_argument('--template', '-t',
            default=DEFAULT_TEMPLATE)
    p_query.add_argument('query', nargs='*')
    p_query.set_defaults(_command='query', format='summary')

    p_get = sub.add_parser('get')
    p_get.add_argument('attr')
    p_get.set_defaults(_command='get')

    p_url_for = sub.add_parser('url-for')
    p_url_for.add_argument('--git', '-g',
            action='store_true')
    p_url_for.add_argument('rev')
    p_url_for.set_defaults(_command='url-for')

    p_view = sub.add_parser('view')
    p_view.add_argument('--git', '-g',
            action='store_true')
    p_view.add_argument('rev')
    p_view.set_defaults(_command='view')

    p_review = sub.add_parser('review')
    p_review.add_argument('--git', '-g',
            action='store_true')
    p_review.add_argument('rev')
    p_review.set_defaults(_command='review')

    for cmd in RAW_COMMANDS:
        p_raw = sub.add_parser(cmd)
        p_raw.add_argument('args', nargs=argparse.REMAINDER)
        p_raw.set_defaults(_command=cmd)

    return p.parse_known_args()


def main():
    args, extra_args = parse_args()
    if hasattr(args, 'template_dir'):
        if args.template_dir is None:
            args.template_dir = os.path.join(
                    os.path.dirname(args.config), 'templates')

    logging.basicConfig(
        level=args.loglevel)

    LOG.debug('args %s', args)
    LOG.debug('extra_args %s', extra_args)

    try:
        with open(args.config) as fd:
            config = yaml.load(fd)
    except IOError:
        config = {}

    remote = Gerrit()
    LOG.debug('gerrit remote %s', remote.remote)

    try:
        if args._command == 'url-for':
            handle_url_for(args, extra_args, remote, config)
        elif args._command == 'view':
            handle_view(args, extra_args, remote, config)
        elif args._command == 'get':
            handle_get(args, extra_args, remote, config)
        elif args._command == 'query':
            handle_query(args, extra_args, remote, config)
        elif args._command == 'review':
            handle_review(args, extra_args, remote, config)
        else:
            handle_raw(args, extra_args, remote, config)
    except GrufError as err:
        LOG.error(err)
        sys.exit(1)
    except subprocess.CalledProcessError as err:
        sys.exit(1)

if __name__ == '__main__':
    main()

