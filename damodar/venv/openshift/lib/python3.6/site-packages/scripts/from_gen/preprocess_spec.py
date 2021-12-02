# Copyright 2016 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import json
import operator
import os.path
import sys
import argparse
from collections import OrderedDict

import urllib3

# these four constants are shown as part of this example in []:
# "[watch]Pod[List]" is the deprecated version of "[list]Pod?[watch]=True"
WATCH_OP_PREFIX = "watch"
WATCH_OP_SUFFIX = "List"
LIST_OP_PREFIX = "list"
WATCH_QUERY_PARAM_NAME = "watch"

CUSTOM_OBJECTS_SPEC_PATH = os.path.join(
    os.path.dirname(__file__),
    'custom_objects_spec.json')

_ops = ['get', 'put', 'post', 'delete', 'options', 'head', 'patch']


class PreprocessingException(Exception):
    pass


def _title(s):
    if len(s) == 0:
        return s
    return s[0].upper() + s[1:]


def _to_camel_case(s):
    return ''.join(_title(y) for y in s.split("_"))


def apply_func_to_spec_operations(spec, func, *params):
    """Apply func to each operation in the spec.

    :param spec: The OpenAPI spec to apply func to.
    :param func: the function to apply to the spec's operations. It should be
                 a func(operation, parent) where operation will be each
                 operation of the spec and parent would be the parent object of
                 the given operation.
                 If the return value of the func is True, then the operation
                 will be deleted from the spec.
    """
    for k, v in spec['paths'].items():
        for op in _ops:
            if op not in v:
                continue
            if func(v[op], v, *params):
                del v[op]


def _has_property(prop_list, property_name):
    for prop in prop_list:
        if prop["name"] == property_name:
            return True


def remove_watch_operations(op, parent, operation_ids):
    op_id = op['operationId']
    if not op_id.startswith(WATCH_OP_PREFIX):
        return
    list_id = (LIST_OP_PREFIX +
               op_id.replace(WATCH_OP_SUFFIX, "")[len(WATCH_OP_PREFIX):])
    if list_id not in operation_ids:
        raise PreprocessingException("Cannot find %s" % list_id)
    list_op = operation_ids[list_id]
    params = []
    if 'parameters' in list_op:
        params += list_op['parameters']
    if 'parameters' in parent:
        params += parent['parameters']
    if not _has_property(params, WATCH_QUERY_PARAM_NAME):
        raise PreprocessingException("%s has no watch query param" % list_id)
    return True


def strip_tags_from_operation_id(operation, _):
    operation_id = operation['operationId']
    if 'tags' in operation:
        for t in operation['tags']:
            operation_id = operation_id.replace(_to_camel_case(t), '')
        operation['operationId'] = operation_id

def add_custom_objects_spec(spec):
    with open(CUSTOM_OBJECTS_SPEC_PATH, 'r') as custom_objects_spec_file:
        custom_objects_spec = json.loads(custom_objects_spec_file.read())
    for path in custom_objects_spec.keys():
        if path not in spec['paths'].keys():
            spec['paths'][path] = custom_objects_spec[path]
    return spec


def process_swagger(spec, client_language):
    spec = add_custom_objects_spec(spec)

    apply_func_to_spec_operations(spec, strip_tags_from_operation_id)

    operation_ids = {}
    apply_func_to_spec_operations(spec, lambda op, _: operator.setitem(
        operation_ids, op['operationId'], op))

    try:
        apply_func_to_spec_operations(
            spec, remove_watch_operations, operation_ids)
    except PreprocessingException as e:
        print(e)

    remove_model_prefixes(spec, 'io.k8s')

    inline_primitive_models(spec, preserved_primitives_for_language(client_language))

    return spec

def preserved_primitives_for_language(client_language):
    if client_language == "java":
        return ["intstr.IntOrString", "resource.Quantity"]
    elif client_language == "csharp":
        return ["intstr.IntOrString", "resource.Quantity", "v1.Patch"]
    else:
        return []

def rename_model(spec, old_name, new_name):
    if new_name in spec['definitions']:
        raise PreprocessingException(
            "Cannot rename model %s. new name %s exists." %
            (old_name, new_name))
    find_rename_ref_recursive(spec,
                              "#/definitions/" + old_name,
                              "#/definitions/" + new_name)
    spec['definitions'][new_name] = spec['definitions'][old_name]
    del spec['definitions'][old_name]


def find_rename_ref_recursive(root, old, new):
    if isinstance(root, list):
        for r in root:
            find_rename_ref_recursive(r, old, new)
    if isinstance(root, dict):
        if "$ref" in root:
            if root["$ref"] == old:
                root["$ref"] = new
        for k, v in root.items():
            find_rename_ref_recursive(v, old, new)


def is_model_deprecated(m):
    """
    Check if a mode is deprecated model redirection.

    A deprecated mode redirecation has only two members with a
    description starts with "Deprecated." string.
    """
    if len(m) != 2:
        return False
    if "$ref" not in m or "description" not in m:
        return False
    return m["description"].startswith("Deprecated.")


def remove_deprecated_models(spec):
    """
    In kubernetes 1.8 some of the models are renamed. Our remove_model_prefixes
    still creates the same model names but there are some models added to
    reference old model names to new names. These models broke remove_model_prefixes
    and need to be removed.
    """
    models = {}
    for k, v in spec['definitions'].items():
        if is_model_deprecated(v):
            print("Removing deprecated model %s" % k)
        else:
            models[k] = v
    spec['definitions'] = models


def remove_model_prefixes(spec, pattern):
    """Remove full package name from OpenAPI model names.

    Starting kubernetes 1.6, all models has full package name. This is
    verbose and inconvenient in python client. This function tries to remove
    parts of the package name but will make sure there is no conflicting model
    names. This will keep most of the model names generated by previous client
    but will change some of them.
    """

    remove_deprecated_models(spec)

    models = {}
    for k, v in spec['definitions'].items():
        if k.startswith(pattern):
            models[k] = {"split_n": 2}

    conflict = True
    while conflict:
        for k, v in models.items():
            splits = k.rsplit(".", v["split_n"])
            v["removed_prefix"] = splits.pop(0)
            v["new_name"] = ".".join(splits)

        conflict = False
        for k, v in models.items():
            for k2, v2 in models.items():
                if k != k2 and v["new_name"] == v2["new_name"]:
                    v["conflict"] = True
                    v2["conflict"] = True
                    conflict = True

        if conflict:
            for k, v in models.items():
                if "conflict" in v:
                    print("Resolving conflict for %s" % k)
                    v["split_n"] += 1
                    del v["conflict"]

    for k, v in models.items():
        if "new_name" not in v:
            raise PreprocessingException("Cannot rename model %s" % k)
        print("Removing prefix %s from %s...\n" % (v["removed_prefix"], k))
        rename_model(spec, k, v["new_name"])


def find_replace_ref_recursive(root, ref_name, replace_map):
    if isinstance(root, list):
        for r in root:
            find_replace_ref_recursive(r, ref_name, replace_map)
    if isinstance(root, dict):
        if "$ref" in root:
            if root["$ref"] == ref_name:
                del root["$ref"]
                for k, v in replace_map.items():
                    if k in root:
                        if k != "description":
                            raise PreprocessingException(
                                "Cannot inline model %s because of "
                                "conflicting key %s." % (ref_name, k))
                        continue
                    root[k] = v
        for k, v in root.items():
            find_replace_ref_recursive(v, ref_name, replace_map)


def inline_primitive_models(spec, excluded_primitives):
    to_remove_models = []
    for k, v in spec['definitions'].items():
        if k in excluded_primitives:
            continue
        if "properties" not in v:
            if k == "intstr.IntOrString":
                v["type"] = "object"
            if "type" not in v:
                v["type"] = "object"
            print("Making model `%s` inline as %s..." % (k, v["type"]))
            find_replace_ref_recursive(spec, "#/definitions/" + k, v)
            to_remove_models.append(k)

    for k in to_remove_models:
        del spec['definitions'][k]

def write_json(filename, object):
    with open(filename, 'w') as out:
        json.dump(object, out, sort_keys=False, indent=2, separators=(',', ': '), ensure_ascii=True)



def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'client_language',
        help='Client language to setup spec for'
    )
    argparser.add_argument(
        'kubernetes_branch',
        help='Branch of github.com/kubernetes/kubernetes to get spec from'
    )
    argparser.add_argument(
        'output_spec_path',
        help='Path to otput spec file to'
    )
    args = argparser.parse_args()

    spec_url = 'https://raw.githubusercontent.com/kubernetes/kubernetes/' \
               '%s/api/openapi-spec/swagger.json' % args.kubernetes_branch

    pool = urllib3.PoolManager()
    with pool.request('GET', spec_url, preload_content=False) as response:
        if response.status != 200:
            print("Error downloading spec file. Reason: %s" % response.reason)
            return 1
        in_spec = json.load(response, object_pairs_hook=OrderedDict)
        write_json(args.output_spec_path + ".unprocessed", in_spec)
        out_spec = process_swagger(in_spec, args.client_language)
        write_json(args.output_spec_path, out_spec)
    return 0


import re

import string_utils

VERSION_RX = re.compile(".*V\d((alpha|beta)\d)?")

DEFAULT_CODEGEN_IGNORE_LINES = {
  ".gitignore",
  "git_push.sh",
  "requirements.txt",
  "test-requirements.txt",
  "setup.py",
  ".travis.yml",
  "tox.ini",
  "client/api_client.py",
  "client/configuration.py",
  "client/rest.py",
  "config/kube_config.py",
}

conflicted_modules = set()

def snake_case_model(model):
    return '_'.join([string_utils.camel_case_to_snake(x) for x in model.split('.')])

def add_missing_openshift_tags_to_operation(op, _, path=None, **kwargs):
    tags = op.get('tags', [])
    if not tags and path:
        path_parts = path.split('/')
        if '.openshift.io' in path:
            api_group = path_parts[2].replace('.', '_')
            version = path_parts[3] if VERSION_RX.match(path_parts[3]) else None
        elif 'oapi' in path:
            api_group = path_parts[1]
            version = None
        else:
            raise Exception('Do not know how to process missing tag for path: {}'.format(path))

        tag = api_group
        if version is not None:
            tag += '_' + version
        op['tags'] = [tag]


def update_codegen_ignore(spec, output_path):
    import io
    import os
    import kubernetes

    codegen_ignore_path = os.path.join(os.path.dirname(output_path), '.swagger-codegen-ignore')
    ignore_lines = set()

    k8s_apis = dir(kubernetes.client.apis)
    k8s_models = dir(kubernetes.client.models)

    api_modules = set()
    model_modules = set()

    for path in list(spec['paths'].values()):
        for op_name in list(path.keys()):
            if op_name != 'parameters':
                op = path[op_name]
                for tag in op.get('tags', []):
                    tag = '_'.join([string_utils.camel_case_to_snake(x) for x in tag.split('_')])
                    api_modules.add(tag + '_api')

    for model in list(spec['definitions'].keys()):
        model_modules.add(snake_case_model(model))

    for api_module in api_modules:
        suffix = api_module.split('_')[-1]
        if suffix in ['0', 'pre012'] or api_module in k8s_apis:
            ignore_lines.add('client/apis/{}.py'.format(api_module))
            print("Skipping generation of client/apis/{}.py".format(api_module))
        else:
            print("Not skipping generation of client/apis/{}.py".format(api_module))

    for model_module in model_modules:
        if model_module in k8s_models and model_module not in conflicted_modules:
            ignore_lines.add('client/models/{}.py'.format(model_module))
            print("Skipping generation of client/models/{}.py".format(model_module))
        else:
            print("Not skipping generation of client/models/{}.py".format(model_module))

    for module in list(ignore_lines):
      module_name = module.split('/')[-1].split('.')[0]
      test_module_name = 'test_{}'.format(module_name)
      docs_module_name = "".join(map(lambda x: x.capitalize(), module_name.split('_')))
      ignore_lines.add("test/{}.py".format(test_module_name))
      ignore_lines.add('docs/{}.md'.format(docs_module_name))
      print("Skipping generation of test/{}.py".format(test_module_name))
      print("Skipping generation of docs/{}.md".format(docs_module_name))

    ignore_lines = ignore_lines.union(DEFAULT_CODEGEN_IGNORE_LINES)

    with open(codegen_ignore_path, 'w') as f:
        f.write('\n'.join(sorted(ignore_lines)))


def process_openshift_swagger(spec, output_path):
    remove_model_prefixes(spec, 'com.github.openshift')
    apply_func_to_openshift_spec_operations(spec, add_missing_openshift_tags_to_operation)

    # TODO: Kubernetes does not set a version for OpenAPI spec yet,
    # remove this when that is fixed.
    # spec['info']['version'] = SPEC_VERSION

    return spec


def rename_model(spec, old_name, new_name):
    find_rename_ref_recursive(spec,
                              "#/definitions/" + old_name,
                              "#/definitions/" + new_name)
    if new_name not in spec['definitions']:
        spec['definitions'][new_name] = spec['definitions'][old_name]
    else:
        # If we have a conflict here we should take the openshift version,
        # which is preprocessed first
        conflicted_modules.add(snake_case_model(new_name))
        print("Deleting {old} instead of renaming to {new}, {new} already exists".format(old=old_name, new=new_name))
    del spec['definitions'][old_name]

def apply_func_to_openshift_spec_operations(spec, func, **kwargs):
    """Apply func to each operation in the spec.

    :param spec: The OpenAPI spec to apply func to.
    :param func: the function to apply to the spec's operations. It should be
                 a func(operation, parent) where operation will be each
                 operation of the spec and parent would be the parent object of
                 the given operation.
                 If the return value of the func is True, then the operation
                 will be deleted from the spec.
    """
    for k, v in spec['paths'].items():
        for op in _ops:
            if op not in v:
                continue
            if func(v[op], v, path=k, **kwargs):
                del v[op]


def openshift_main():
    import sys
    import json
    import codecs
    import urllib3
    from collections import OrderedDict

    pool = urllib3.PoolManager()
    reader = codecs.getreader('utf-8')
    spec_url = 'https://raw.githubusercontent.com/openshift/origin/' \
               '%s/api/swagger-spec/openshift-openapi-spec.json' % sys.argv[2]
    output_path = sys.argv[3]
    print("writing to {}".format(output_path))

    with pool.request('GET', spec_url, preload_content=False) as response:
        if response.status != 200:
            print("Error downloading spec file. Reason: %s" % response.reason)
            return 1
        in_spec = json.load(reader(response), object_pairs_hook=OrderedDict)
        out_spec = process_swagger(process_openshift_swagger(in_spec, output_path), sys.argv[1])
        update_codegen_ignore(out_spec, output_path)
        with open(output_path, 'w') as out:
            json.dump(out_spec, out, sort_keys=True, indent=2,
                      separators=(',', ': '), ensure_ascii=True)
    return 0


if __name__ == '__main__':
    sys.exit(openshift_main())
