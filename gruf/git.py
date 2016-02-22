import subprocess
import urlparse


def get_git_config(key):
    '''Read a git configuration value use "git config --get ..."'''
    val = subprocess.check_output([
        'git', 'config', '--get', key]).strip()

    return val


def rev_parse(rev):
    '''Read a git configuration value use "git config --get ..."'''
    val = subprocess.check_output([
        'git', 'rev-parse', '--verify', rev]).strip()

    return val


def get_remote_info(remote):
    url = get_git_config('remote.%s.url' % remote)
    if not url:
        return

    # only ssh urls make sense.  arguably this should support the
    # user@host:path syntax as well, but remotes configured using
    # "git review -s" will never look like that.
    if not url.startswith('ssh://'):
        return

    url = urlparse.urlparse(url)

    try:
        userhost, port = url.netloc.split(':')
    except ValueError:
        port = None
        userhost = url.netloc

    try:
        user, host = userhost.split('@')
    except ValueError:
        user = None
        host = url.netloc

    project = url.path[1:]
    if project.endswith('.git'):
        project = project[:-4]

    return (user, host, port, project)
