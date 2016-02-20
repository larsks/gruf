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

## Streaming

Gruf supports the Gerrit `stream-events` command.  The default
template produces several lines of output for each event; for more
compact output try:

    gruf -t short stream-events

The output will look something like:

<pre>
[<span style="color:#00f0f0;">PATCH</span>     ] 240944,24 openstack/python-ironicclient sturivnyi <span style="color:#0000f0;">https://review.openstack.org/240944</span>
             Add sanity tests for testing actions with Port
[<span style="color:#f0f000;">COMMENT</span>   ] 282334,1 openstack/fuel-octane gelbuhos <span style="color:#0000f0;">https://review.openstack.org/282334</span>
             Workflow 1 Code-Review 2 
[<span style="color:#f0f000;">COMMENT</span>   ] 282334,1 openstack/fuel-octane gelbuhos <span style="color:#0000f0;">https://review.openstack.org/282334</span>
[<span style="color:#f0f000;">COMMENT</span>   ] 275844,23 openstack/kolla elemoine <span style="color:#0000f0;">https://review.openstack.org/275844</span>
             Workflow 1 Code-Review 2 
[<span style="color:#f0f000;">COMMENT</span>   ] 279478,3 openstack/fuel-octane gelbuhos <span style="color:#0000f0;">https://review.openstack.org/279478</span>
             Verified 2 
[<span style="color:#00f000;">MERGED</span>    ] 279478,3 openstack/fuel-octane gelbuhos <span style="color:#0000f0;">https://review.openstack.org/279478</span>
[<span style="color:#f0f000;">COMMENT</span>   ] 248938,29 openstack/neutron slaweq <span style="color:#0000f0;">https://review.openstack.org/248938</span>
[<span style="color:#f0f000;">COMMENT</span>   ] 279478,3 openstack/fuel-octane gelbuhos <span style="color:#0000f0;">https://review.openstack.org/279478</span>
[<span style="color:#f0f000;">COMMENT</span>   ] 279478,3 openstack/fuel-octane gelbuhos <span style="color:#0000f0;">https://review.openstack.org/279478</span>
[<span style="color:#f0f000;">COMMENT</span>   ] 276419,1 openstack/glance siuzannatb <span style="color:#0000f0;">https://review.openstack.org/276419</span>
             Workflow 1 Code-Review 2 
[<span style="color:#f0f000;">COMMENT</span>   ] 276814,18 openstack/fuel-web vkramskikh <span style="color:#0000f0;">https://review.openstack.org/276814</span>
             Verified 1 
[<span style="color:#f0f000;">COMMENT</span>   ] 276419,1 openstack/glance siuzannatb <span style="color:#0000f0;">https://review.openstack.org/276419</span>
[<span style="color:#f0f000;">COMMENT</span>   ] 281472,2 openstack/ironic-webclient krotscheck <span style="color:#0000f0;">https://review.openstack.org/281472</span>
             Verified 1 
[<span style="color:#f0f000;">COMMENT</span>   ] 282331,1 openstack/fuel-qa apanchenko <span style="color:#0000f0;">https://review.openstack.org/282331</span>
</pre>

## Filtering

You can filter the items returned from Gerrit by passing a
[jsonpointer][] expression and expected value to the `--filter` (`-F`)
option.  For example, to stream only events from the `openstack/nova`
project:

    gruf -F /change/project=openstack/nova stream-events

The expected values can use simple [fnmatch][] style wildcards:

    gruf -F /change/project=redhat-openstack/* stream-events

[jsonpointer]: https://tools.ietf.org/html/rfc6901
[fnmatch]: https://docs.python.org/2/library/fnmatch.html

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
