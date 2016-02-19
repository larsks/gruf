#!/usr/bin/python

import argparse
import logging
import os
import shlex
import sys
import urlparse
import yaml
import jinja2
import jsonpointer

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

CMDALIAS = {
        'confirm': {'cmd': 'review --code-review 2 --verified 1'},
        'submit': {'cmd': 'review --submit'},
        'abandon': {'cmd': 'review --abandon'},
        'url-for': {
            'cmd': 'query',
            'template': 'url',
            },
        'show': {
            'cmd': 'query',
            'template': 'detailed',
            }
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
    p.add_argument('--template', '-t')
    p.add_argument('--inline-template', '-T')
    p.add_argument('--template-dir')
    p.add_argument('--cache-lifetime', '-L',
            type=int)
    p.add_argument('--filter', '-F')
    p.add_argument('cmd', nargs=argparse.REMAINDER)

    return p.parse_args()

def main():
    args = parse_args()
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

    cache_lifetime = (
            args.cache_lifetime 
            if args.cache_lifetime is not None
            else config.get('cache', {}).get('lifetime'))

    g = gruf.gerrit.Gerrit(
            remote=args.remote,
            querymap=config.get('querymap'),
            cache_lifetime=cache_lifetime)
    LOG.debug('remote %s', g.remote)

    if args.filter:
        filter_expr, filter_val = args.filter.split('=')
        LOG.debug('filter %s = "%s"', filter_expr, filter_val)

    cmd = args.cmd.pop(0)
    cmdargs = args.cmd

    cmdalias = CMDALIAS
    cmdalias.update(config.get('cmdalias', {}))

    if cmd in cmdalias:
        alias = CMDALIAS[cmd]
        if 'cmd' in alias:
            newcmd = shlex.split(alias['cmd'])
            cmd = newcmd.pop(0)
            cmdargs = newcmd + cmdargs
        if 'template' in alias:
            args.template = alias['template']
        if 'inline_template' in alias:
            args.inline_template = alias['inline_template']

    # handle some administrative commands here
    if cmd == 'invalidate-cache':
        g.cache.invalidate_all()
        return

    cmd_func = cmd.replace('-', '_')
    try:
        res = getattr(g, cmd_func)(*cmdargs)
    except AttributeError:
        res = g.raw(cmd, *cmdargs)

    env = jinja2.Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            loader = jinja2.FileSystemLoader([
                args.template_dir,
                pkg_resources.resource_filename(
                    __name__,
                    'templates'),
                ]))

    env.filters['to_json'] = gruf.filters.to_json
    env.filters['to_yaml'] = gruf.filters.to_yaml
    env.filters['strftime'] = gruf.filters.strftime

    template_name = args.template or 'default'
    template_name_qualified = '{}/{}'.format(
            res.__class__.__name__, template_name)

    if args.inline_template:
        t = env.from_string(args.inline_template)
    else:
        try:
            t = env.get_template(template_name_qualified + '.j2')
        except jinja2.TemplateNotFound:
            t = env.get_template(template_name + '.j2')

    for item in res:
        if args.filter and (
                jsonpointer.resolve_pointer(item, filter_expr, None)
                != filter_val):
            continue

        try:
            out = t.render(item=item, **item).encode('utf-8')
        except TypeError:
            # we get here if item is not a mapping (which will
            # happen currently for UnstructuredResponse
            # results).
            out = t.render(item=item).encode('utf-8')

        sys.stdout.write(out)

        # this is mostly to support inline templates, but I haven't found 
        # a situation in which it causes a problem with file-based
        # templates.
        if args.inline_template and not out.endswith('\n'):
            sys.stdout.write('\n')

if __name__ == '__main__':
    main()
