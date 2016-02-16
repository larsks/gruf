import time
import yaml
import json

def to_json(value, indent=2):
    return json.dumps(dict(value), indent=indent)

def to_yaml(value):
    return yaml.safe_dump(dict(value), default_flow_style=False)

def strftime(value, fmt='%D %T'):
    return time.strftime(fmt, time.gmtime(int(value)))
