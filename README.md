Gruf (which may stand for "Gerrit Reviews Ur Files", or "Gerrit
Review, U Fools", or maybe even "Giant Rodents Under Fireswamp) is a
wrapper for the Gerrit command-line ssh interface.

## Installation

For the latest and greatest:

    pip install git+https://github.com/larsks/gruf

## Configuration

Gruf will attempt to read `$XDG_CONFIG_DIR/gruf/gruf.yml` (which
normally means `$HOME/.config/gruf/gruf.yml`), which is a [YAML][]
format file that can contain a `querymap` key that maps terms in your
query to alias expansions.  So if you have:

    querymap:
       oooq: project:redhat-openstack/tripleo-quickstart

You can ask for:

    $ gruf query oooq status:open

And end up executing:

    query project:redhat-openstack/tripleo-quickstart status:open

Additionally, `gruf` will replace any argument prefixed with `git:`
with the result of calling `git rev-parse` on the rest of the
argument, so you can use `git:HEAD` or `git:mytag` any place that
gerrit will accept a commit id.

### Templates

The `gruf query` command produces results by passing the query results
through a [Jinja2][] template.  You can override this by passing a
literal template as an argument to the `-t` option, or a named
template by prefixing the argument with `@`, as in:

    gruf query -t @summary ...

Gruf will look for templates in the `templates` directory of your
configuration directory.  There are a few examples in the
`gruf/templates` directory in the source distribution.

## Examples

- Get a list of open reviews for the current project:

        $ gruf query open here

- Get a list of reviews including information about the latest
  patch set from a specific project:

        $ gruf query -t @summary \
          open project:redhat-openstack/tripleo-quickstart \
          --current-patch-set
        [  263006] Fedora support for qemu emulation
                   ryansb https://review.gerrithub.io/263006

                   Patch set 1:
                   Code-Review 2
                   Verified -1

        [  262882] introduce global "nodes" configuration role
                   larsks https://review.gerrithub.io/262882

                   Patch set 6:
                   Verified -1
        ...

- Approve the current commit:

        $ gruf review --code-review +2 --verified +1 git:HEAD

## License

GRUF, a gerrit command-line wrapper
Copyright (C) 2016 Lars Kellogg-Stedman

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

[yaml]: http://yaml.org/
[jinja2]: http://jinja.pocoo.org/
