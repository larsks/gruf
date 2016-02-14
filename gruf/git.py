import subprocess
import logging

LOG = logging.getLogger(__name__)

def rev_parse(rev):
    LOG.debug('looking up rev %s', rev)
    cid = subprocess.check_output(['git', 'rev-parse', rev])
    return cid.strip()

def get_config(k):
    LOG.debug('looking up config val %s', k)
    return subprocess.check_output([
        'git', 'config', '--get', k]).strip()
