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

    $ gruf query oooq open

And end up executing:

    query project:redhat-openstack/tripleo-quickstart status:open

The following aliases are built-in:

- `mine`: `owner:self`
- `here`: `project:<current project name>`
- `open`: `status:open`

Additionally, `gruf` will replace any argument prefixed with `git:`
with the result of calling `git rev-parse` on the rest of the
argument, so you can use `git:HEAD` or `git:mytag` any place that
gerrit will accept a commit id.

### Templates

The `gruf query` command produces results by passing the query results
through a [Jinja2][] template.  You can override this by passing a
template name with the `-t` option.  Gruf will first search for
templates in a directory named after the class of the result, and then
without the class prefix.  For example, if you run:

    gruf -t yaml query open here

Gruf will first attempt to load the template `QueryResponse/yaml.j2`, and
if that fails it will look for `yaml.j2`.

## Examples

- Get a list of open changes for the current project:

        $ gruf query open here

- Get a list of URLs for the same thing:

        $ gruf url-for open here

- Approve the change associated with the current commit:

        $ gruf confirm git:HEAD

  This is actually shorthand for:

        $ gruf review --code-review 2 --verified 1 git:HEAD

- Abandon a change with a comment:

        $ gruf abandon -m "this was a terrible idea" 263262,1

  This is actually shorthand for:

        $ gruf review --abandon 263262,1

- See detailed information about changes:

        $ gruf show open here

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
