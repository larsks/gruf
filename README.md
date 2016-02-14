Gruf (which may stand for "Gerrit Reviews Ur Files", or "Gerrit
Review, U Fools", or maybe even "Giant Rodents Under Fireswamp) is a
wrapper for the Gerrit command-line ssh interface.

## Installation

For the latest and greatest:

    pip install git+https://github.com/larsks/gruf

## Examples

- Get the URL of the gerrit server for the current git repository:

        $ gerrit get url
        ssh://yourname@review.gerrithub.io:29418/yourproject/yourrepo.git

- Get the URL for the Gerrit review associated with a particular git
  revision:

        $ gerrit url-for -g HEAD
        https://review.gerrithub.io/263041

- Get a list of open reviews for the current project:

        $ gerrit query open here

- Get a list of reviews including information about the latest
  patch set from a specific project:

        $ gerrit query -t @summary \
          status:open project:redhat-openstack/tripleo-quickstart \
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

