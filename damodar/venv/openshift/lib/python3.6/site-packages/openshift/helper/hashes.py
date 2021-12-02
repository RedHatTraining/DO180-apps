# Implement ConfigMapHash and SecretHash equivalents
# Based on https://github.com/kubernetes/kubernetes/pull/49961

import json
import hashlib

try:
    import string
    maketrans = string.maketrans
except AttributeError:
    maketrans = str.maketrans

try:
    from collections import OrderedDict
except ImportError:
    from orderreddict import OrderedDict


def sorted_dict(unsorted_dict):
    result = OrderedDict()
    for (k, v) in sorted(unsorted_dict.items()):
        if isinstance(v, dict):
            v = sorted_dict(v)
        result[k] = v
    return result


def generate_hash(resource):
    # Get name from metadata
    resource['name'] = resource.get('metadata', {}).get('name', '')
    if resource['kind'] == 'ConfigMap':
        marshalled = marshal(sorted_dict(resource), ['data', 'kind', 'name'])
        del(resource['name'])
        return encode(marshalled)
    if resource['kind'] == 'Secret':
        marshalled = marshal(sorted_dict(resource), ['data', 'kind', 'name', 'type'])
        del(resource['name'])
        return encode(marshalled)
    raise NotImplementedError


def marshal(data, keys):
    ordered = OrderedDict()
    for key in keys:
        ordered[key] = data.get(key, "")
    return json.dumps(ordered, separators=(',', ':')).encode('utf-8')


def encode(resource):
    return hashlib.sha256(resource).hexdigest()[:10].translate(maketrans("013ae", "ghkmt"))
