import yaml
import json

def to_json(value, indent=2):
    return json.dumps(value, indent=indent)

def to_yaml(value):
    return yaml.safe_dump(value, default_flow_style=False)

