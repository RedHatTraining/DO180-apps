# -*- coding: utf-8 -*-
from __future__ import absolute_import

import copy
import json
import base64
import logging
from keyword import kwlist

import string_utils

from . import PRIMITIVES
from .kubernetes import KubernetesObjectHelper
from .openshift import OpenShiftObjectHelper

# Attributes in argspec not needed by Ansible
ARG_ATTRIBUTES_BLACKLIST = ('description', 'auth_option', 'property_path')
PYTHON_KEYWORD_MAPPING = dict(zip(map('_{}'.format, kwlist), kwlist))
PYTHON_KEYWORD_MAPPING.update(dict([reversed(item) for item in PYTHON_KEYWORD_MAPPING.items()]))

logger = logging.getLogger(__name__)


class AnsibleMixin(object):
    _argspec_cache = None

    @property
    def argspec(self):
        """
        Introspect the model properties, and return an Ansible module arg_spec dict.

        :return: dict
        """
        if self._argspec_cache:
            return self._argspec_cache

        argument_spec = {
            'state': {
                'default': 'present',
                'choices': ['present', 'absent'],
                'description': [
                    "Determines if an object should be created, patched, or deleted. When set to "
                    "C(present), the object will be created, if it does not exist, or patched, if parameter "
                    "values differ from the existing object's attributes, and deleted, if set to C(absent). A patch "
                    "operation results in merging lists and updating dictionaries, with lists being merged into a "
                    "unique set of values. If a list contains a dictionary with a I(name) or I(type) attribute, "
                    "a strategic merge is performed, where individual elements with a matching I(name_) or I(type) are "
                    "merged. To force the replacement of lists, set the I(force) option to C(True)."
                ]
            },
            'force': {
                'type': 'bool',
                'default': False,
                'description': [
                    "If set to C(True), and I(state) is C(present), an existing object will updated, and lists will "
                    "be replaced, rather than merged."
                ]
            },
            'kubeconfig': {
                'type': 'path',
                'auth_option': True,
                'description': [
                    "Path to an existing Kubernetes config file. If not provided, and no other connection "
                    "options are provided, the openshift client will attempt to load the default configuration "
                    "file from I(~/.kube/config.json)."
                ]},

            'context': {
                'auth_option': True,
                'description': [
                    "The name of a context found in the Kubernetes config file."
                ]
            },
            'host': {
                'auth_option': True,
                'description': ["Provide a URL for acessing the Kubernetes API."]
            },
            'api_key': {
                'auth_option': True,
                'no_log': True,
                'description': ["Token used to connect to the API."]
            },
            'username': {
                'auth_option': True,
                'description': [
                    "Provide a username for connecting to the API."
                ]
            },
            'password': {
                'auth_option': True,
                'no_log': True,
                'description': [
                    "Provide a password for connecting to the API. Use in conjunction with I(username)."
                ]
            },
            'verify_ssl': {
                'type': 'bool',
                'auth_option': True,
                'description': [
                    "Whether or not to verify the API server's SSL certificates."
                ]
            },
            'ssl_ca_cert': {
                'type': 'path',
                'auth_option': True,
                'description': [
                    "Path to a CA certificate used to authenticate with the API."
                ]
            },
            'cert_file': {
                'type': 'path',
                'auth_option': True,
                'description': [
                    "Path to a certificate used to authenticate with the API."
                ]
            },
            'key_file': {
                'type': 'path',
                'auth_option': True,
                'description': [
                    "Path to a key file used to authenticate with the API."
                ]
            },
            'debug': {
                'type': 'bool',
                'default': False,
                'description': [
                    "Enable debug output from the OpenShift helper. Logging info is written "
                    "to KubeObjHelper.log"
                ]
            },
            'resource_definition': {
                'type': 'dict',
                'description': [
                    "Provide the YAML definition for the object, bypassing any modules parameters intended to "
                    "define object attributes."
                ]
            },
            'src': {
                'type': 'path',
                'description': [
                    "Provide a path to a file containing the YAML definition of the object. Mutually exclusive "
                    "with I(resource_definition)."
                ]
            }
        }

        argument_spec.update(self.__transform_properties(self.properties))

        if not self.has_method('delete'):
            # if no delete method, then we likely don't need these options
            argument_spec.pop('state')
            argument_spec.pop('src')
            argument_spec.pop('resource_definition')

        if self.kind.lower() == 'project':
            argument_spec['display_name'] = {
                'description': [
                    "Provides a descriptive name for the project."
                ]
            }
            argument_spec['description'] = {
                'description': [
                    "Provides a brief overview or narrative for the project."
                ]
            }

        used_names = set(argument_spec.keys())
        for _, arg_options in sorted(argument_spec.items()):
            for alias in arg_options.get('aliases', []):
                if alias in used_names:
                    arg_options['aliases'].remove(alias)
                else:
                    used_names.add(alias)

        self._argspec_cache = argument_spec
        self.log_argspec()
        return self._argspec_cache

    def log_argspec(self):
        """ Safely logs the argspec by not including any params with the no_log attribute. """
        logger.debug("arg_spec:")
        tmp_arg_spec = copy.deepcopy(self._argspec_cache)
        pop_keys = []
        for key, value in tmp_arg_spec.items():
            if value.get('no_log'):
                pop_keys.append(key)
        for key in pop_keys:
            tmp_arg_spec.pop(key)
        logger.debug(json.dumps(tmp_arg_spec, indent=4, sort_keys=True))

    def object_from_params(self, module_params, obj=None):
        """
        Update a model object with Ansible module param values. Optionally pass an object
        to update, otherwise a new object will be created.
        :param module_params: dict of key:value pairs
        :param obj: model object to update
        :return: updated model object
        """
        if not obj:
            obj = self.model()
            obj.kind = string_utils.snake_case_to_camel(self.kind, upper_case_first=False)
            obj.api_version = self.api_version.lower()
        for param_name, param_value in module_params.items():
            spec = self.find_arg_spec(param_name)
            if param_value is not None and spec.get('property_path'):
                prop_path = copy.copy(spec['property_path'])
                self.__set_obj_attribute(obj, prop_path, param_value, param_name)

        if self.kind.lower() == 'project' and (module_params.get('display_name') or
                                               module_params.get('description')):
            if not obj.metadata.annotations:
                obj.metadata.annotations = {}
            if module_params.get('display_name'):
                obj.metadata.annotations['openshift.io/display-name'] = module_params['display_name']
            if module_params.get('description'):
                obj.metadata.annotations['openshift.io/description'] = module_params['description']
        elif (self.kind.lower() == 'secret' and getattr(obj, 'string_data', None)
                and hasattr(obj, 'data')):
            if obj.data is None:
                obj.data = {}

            # Do a base64 conversion of `string_data` and place it in
            # `data` so that later comparisons to existing objects
            # (if any) do not result in requiring an unnecessary change.
            for key, value in obj.string_data.items():
                obj.data[key] = base64.b64encode(value)

            obj.string_data = None

        logger.debug("Object from params:")
        logger.debug(obj.to_str())
        return obj

    def request_body_from_params(self, module_params):
        request = {
            'kind': self.base_model_name,
        }
        for param_name, param_value in module_params.items():
            spec = self.find_arg_spec(param_name)
            if spec and spec.get('property_path') and param_value is not None:
                self.__add_path_to_dict(request, param_name, param_value, spec['property_path'])

        if self.kind.lower() == 'project' and (module_params.get('display_name') or
                                               module_params.get('description')):
            if not request.get('metadata'):
                request['metadata'] = {}
            if not request['metadata'].get('annotations'):
                request['metadata']['annotations'] = {}
            if module_params.get('display_name'):
                request['metadata']['annotations']['openshift.io/display-name'] = module_params['display_name']
            if module_params.get('description'):
                request['metadata']['annotations']['openshift.io/description'] = module_params['description']

        logger.debug('request_body:')
        logger.debug(json.dumps(request, indent=4))
        return request

    def find_arg_spec(self, module_param_name):
        """For testing, allow the param_name value to be an alias"""
        if self.argspec.get(module_param_name):
            return self.argspec[module_param_name]
        result = None
        for key, value in self.argspec.items():
            if value.get('aliases'):
                for alias in value['aliases']:
                    if alias == module_param_name:
                        result = self.argspec[key]
                        break
                if result:
                    break
        if not result:
            raise self.get_exception_class()(
                "Error: received unrecognized module parameter {}".format(module_param_name)
            )
        return result

    @staticmethod
    def log(msg):
        """ Allow Ansible module to add debug messages to the log """
        logger.debug(msg)

    @staticmethod
    def __convert_params_to_choices(properties):
        def snake_case(name):
            result = string_utils.snake_case_to_camel(name.replace('_params', ''), upper_case_first=True)
            return result[:1].upper() + result[1:]
        choices = {}
        for x in list(properties.keys()):
            if x.endswith('params'):
                choices[x] = snake_case(x)
        return choices

    def __add_path_to_dict(self, request_dict, param_name, param_value, path):
        local_path = copy.copy(path)
        spec = self.find_arg_spec(param_name)
        while len(local_path):
            p = string_utils.snake_case_to_camel(local_path.pop(0), upper_case_first=False)
            if len(local_path):
                if request_dict.get(p, None) is None:
                    request_dict[p] = {}
                self.__add_path_to_dict(request_dict[p], param_name, param_value, local_path)
                break
            else:
                param_type = spec.get('type', 'str')
                if param_type == 'dict':
                    request_dict[p] = self.__dict_keys_to_camel(param_name, param_value)
                elif param_type == 'list':
                    request_dict[p] = self.__list_keys_to_camel(param_name, param_value)
                else:
                    request_dict[p] = param_value

    def __dict_keys_to_camel(self, param_name, param_dict):
        result = {}
        for item, value in param_dict.items():
            key_name = self.__property_name_to_camel(param_name, item)
            if value:
                if isinstance(value, list):
                    result[key_name] = self.__list_keys_to_camel(param_name, value)
                elif isinstance(value, dict):
                    result[key_name] = self.__dict_keys_to_camel(param_name, value)
                else:
                    result[key_name] = value
        return result

    @staticmethod
    def __property_name_to_camel(param_name, property_name):
        new_name = property_name
        if 'annotations' not in param_name and 'labels' not in param_name and 'selector' not in param_name:
            camel_name = string_utils.snake_case_to_camel(property_name, upper_case_first=False)
            new_name = camel_name[1:] if camel_name.startswith('_') else camel_name
        return new_name

    def __list_keys_to_camel(self, param_name, param_list):
        result = []
        if isinstance(param_list[0], dict):
            for item in param_list:
                result.append(self.__dict_keys_to_camel(param_name, item))
        else:
            result = param_list
        return result

    def __set_obj_attribute(self, obj, property_path, param_value, param_name):
        """
        Recursively set object properties
        :param obj: The object on which to set a property value.
        :param property_path: A list of property names in the form of strings.
        :param param_value: The value to set.
        :return: The original object.
        """

        logger.debug("set_obj_attribute {0}, {1} to {2}".format(obj.__class__.__name__,
                                                                json.dumps(property_path),
                                                                json.dumps(param_value)))

        while len(property_path) > 0:
            raw_prop_name = property_path.pop(0)
            prop_name = PYTHON_KEYWORD_MAPPING.get(raw_prop_name, raw_prop_name)
            prop_kind = obj.swagger_types[prop_name]
            if prop_kind in PRIMITIVES:
                try:
                    setattr(obj, prop_name, param_value)
                except ValueError as exc:
                    msg = str(exc)
                    if param_value is None and 'None' in msg:
                        pass
                    else:
                        raise self.get_exception_class()(
                            "Error setting {0} to {1}: {2}".format(prop_name, param_value, msg)
                        )
            elif prop_kind.startswith('dict('):
                if not getattr(obj, prop_name):
                    setattr(obj, prop_name, param_value)
                else:
                    self.__compare_dict(getattr(obj, prop_name), param_value, param_name)
            elif prop_kind.startswith('list['):
                if getattr(obj, prop_name) is None:
                    setattr(obj, prop_name, [])
                obj_type = prop_kind.replace('list[', '').replace(']', '')
                if obj_type not in PRIMITIVES and obj_type not in ('list', 'dict'):
                    self.__compare_obj_list(getattr(obj, prop_name), param_value, obj_type, param_name)
                else:
                    self.__compare_list(getattr(obj, prop_name), param_value, param_name)
            else:
                # prop_kind is an object class
                sub_obj = getattr(obj, prop_name)
                if not sub_obj:
                    sub_obj = self.model_class_from_name(prop_kind)()
                setattr(obj, prop_name, self.__set_obj_attribute(sub_obj, property_path, param_value, param_name))
        return obj

    def __compare_list(self, src_values, request_values, param_name):
        """
        Compare src_values list with request_values list, and ppend any missing
        request_values to src_values.
        """
        if not request_values:
            return

        if not src_values:
            src_values += request_values

        if type(src_values[0]).__name__ in PRIMITIVES:
            if set(src_values) >= set(request_values):
                # src_value list includes request_value list
                return
            # append the missing elements from request value
            src_values += list(set(request_values) - set(src_values))
        elif type(src_values[0]).__name__ == 'dict':
            missing = []
            for request_dict in request_values:
                match = False
                for src_dict in src_values:
                    if '__cmp__' in dir(src_dict):
                        # python < 3
                        if src_dict >= request_dict:
                            match = True
                            break
                    elif src_dict.items() == request_dict.items():
                        # python >= 3
                        match = True
                        break
                if not match:
                    missing.append(request_dict)
            src_values += missing
        elif type(src_values[0]).__name__ == 'list':
            missing = []
            for request_list in request_values:
                match = False
                for src_list in src_values:
                    if set(request_list) >= set(src_list):
                        match = True
                        break
                if not match:
                    missing.append(request_list)
            src_values += missing
        else:
            raise self.get_exception_class()(
                "Evaluating {0}: encountered unimplemented type {1} in "
                "__compare_list()".format(param_name, type(src_values[0]).__name__)
            )

    def __compare_dict(self, src_value, request_value, param_name):
        """
        Compare src_value dict with request_value dict, and update src_value with any differences.
        Does not remove items from src_value dict.
        """
        if not request_value:
            return
        for item, value in request_value.items():
            if type(value).__name__ in ('str', 'int', 'bool'):
                src_value[item] = value
            elif type(value).__name__ == 'list':
                self.__compare_list(src_value[item], value, param_name)
            elif type(value).__name__ == 'dict':
                self.__compare_dict(src_value[item], value, param_name)
            else:
                raise self.get_exception_class()(
                    "Evaluating {0}: encountered unimplemented type {1} in "
                    "__compare_dict()".format(param_name, type(value).__name__)
                )

    def __compare_obj_list(self, src_value, request_value, obj_class, param_name):
        """
        Compare a src_value (list of ojects) with a request_value (list of dicts), and update
        src_value with differences. Assumes each object and each dict has a 'name' attributes,
        which can be used for matching. Elements are not removed from the src_value list.
        """
        if not request_value:
            return

        model_class = self.model_class_from_name(obj_class)

        # Try to determine the unique key for the array
        key_names = [
            'name',
            'type'
        ]
        key_name = None
        for key in key_names:
            if hasattr(model_class, key):
                key_name = key
                break

        if key_name:
            # If the key doesn't exist in the request values, then ignore it, rather than throwing an error
            for item in request_value:
                if not item.get(key_name):
                    key_name = None
                    break

        if key_name:
            # compare by key field
            for item in request_value:
                if not item.get(key_name):
                    # Prevent user from creating something that will be impossible to patch or update later
                    logger.debug("FAILED on: {}".format(item))
                    raise self.get_exception_class()(
                        "Evaluating {0} - expecting parameter {1} to contain a `{2}` attribute "
                        "in __compare_obj_list().".format(param_name,
                                                          self.get_base_model_name_snake(obj_class),
                                                          key_name)
                    )
                found = False
                for obj in src_value:
                    if not obj:
                        continue
                    if getattr(obj, key_name) == item[key_name]:
                        # Assuming both the src_value and the request value include a name property
                        found = True
                        for key, value in item.items():
                            snake_key = self.attribute_to_snake(key)
                            item_kind = model_class.swagger_types.get(snake_key)
                            if item_kind and item_kind in PRIMITIVES or type(value).__name__ in PRIMITIVES:
                                setattr(obj, snake_key, value)
                            elif item_kind and item_kind.startswith('list['):
                                obj_type = item_kind.replace('list[', '').replace(']', '')
                                if getattr(obj, snake_key) is None:
                                    setattr(obj, snake_key, [])
                                if obj_type not in ('str', 'int', 'bool', 'object'):
                                    self.__compare_obj_list(getattr(obj, snake_key), value, obj_type, param_name)
                                else:
                                    # Straight list comparison
                                    self.__compare_list(getattr(obj, snake_key), value, param_name)
                            elif item_kind and item_kind.startswith('dict('):
                                self.__compare_dict(getattr(obj, snake_key), value, param_name)
                            elif item_kind and type(value).__name__ == 'dict':
                                # object
                                param_obj = getattr(obj, snake_key)
                                if not param_obj:
                                    setattr(obj, snake_key, self.model_class_from_name(item_kind)())
                                    param_obj = getattr(obj, snake_key)
                                self.__update_object_properties(param_obj, value)
                            else:
                                if item_kind:
                                    raise self.get_exception_class()(
                                        "Evaluating {0}: encountered unimplemented type {1} in "
                                        "__compare_obj_list() for model {2}".format(
                                            param_name,
                                            item_kind,
                                            self.get_base_model_name_snake(obj_class))
                                    )
                                else:
                                    raise self.get_exception_class()(
                                        "Evaluating {}: unable to get swagger_type for {} in "
                                        "__compare_obj_list() for item {} in model {}".format(
                                            param_name,
                                            snake_key,
                                            str(item),
                                            self.get_base_model_name_snake(obj_class))
                                    )
                if not found:
                    # Requested item not found. Adding.
                    obj = self.model_class_from_name(obj_class)(**item)
                    src_value.append(obj)
        else:
            # There isn't a key, or we don't know what it is, so check for all properties to match
            for item in request_value:
                found = False
                for obj in src_value:
                    match = True
                    for item_key, item_value in item.items():
                        # TODO: this should probably take the property type into account
                        snake_key = self.attribute_to_snake(item_key)
                        if getattr(obj, snake_key) != item_value:
                            match = False
                            break
                    if match:
                        found = True
                        break
                if not found:
                    obj = self.model_class_from_name(obj_class)(**item)
                    src_value.append(obj)

    def __update_object_properties(self, obj_class, item):
        """ Recursively update an class's properties. Returns a pointer to the class. """

        for key, value in item.items():
            snake_key = self.attribute_to_snake(key)
            try:
                kind = obj_class.swagger_types[snake_key]
            except (AttributeError,KeyError):
                possible_matches = ', '.join(list(obj_class.swagger_types.keys()))
                class_snake_name = self.get_base_model_name_snake(obj_class.__name__)
                raise self.get_exception_class()(
                    "Unable to find '{0}' in {1}. Valid property names include: {2}".format(snake_key,
                                                                                            class_snake_name,
                                                                                            possible_matches)
                )
            if kind in PRIMITIVES or kind.startswith('list[') or kind.startswith('dict('):
                self.__set_obj_attribute(obj_class, [snake_key], value, snake_key)
            else:
                # kind is an object, hopefully
                if not getattr(obj_class, snake_key):
                    setattr(obj_class, snake_key, self.model_class_from_name(kind)())
                self.__update_object_properties(getattr(obj_class, snake_key), value)

        return obj_class

    def __transform_properties(self, properties, prefix='', path=None, alternate_prefix='', parent_property_classes=None):
        """
        Convert a list of properties to an argument_spec dictionary

        :param properties: List of properties from self.properties_from_model_class()
        :param prefix: String to prefix to argument names.
        :param path: List of property names providing the recursive path through the model to the property
        :param alternate_prefix: a more minimal version of prefix
        :return: dict
        """
        parent_property_classes = parent_property_classes or set()
        primitive_types = list(PRIMITIVES) + ['list', 'dict']
        args = {}

        if path is None:
            path = []

        def add_meta(prop_name, prop_prefix, prop_alt_prefix):
            """ Adds metadata properties to the argspec """
            if prop_alt_prefix != prop_prefix:
                if prop_alt_prefix:
                    args[prop_prefix + prop_name]['aliases'] = [prop_alt_prefix + prop_name]
                elif prop_prefix:
                    args[prop_prefix + prop_name]['aliases'] = [prop_name]
            prop_paths = copy.copy(path)  # copy path from outer scope
            prop_paths.append('metadata')
            prop_paths.append(prop_name)
            args[prop_prefix + prop_name]['property_path'] = prop_paths

        for raw_prop, prop_attributes in properties.items():
            prop = PYTHON_KEYWORD_MAPPING.get(raw_prop, raw_prop)
            logger.debug("Prop: {0} attributes: {1}".format(prop, str(prop_attributes)))
            if prop in ('api_version', 'status', 'kind', 'items') and not prefix:
                # Don't expose these properties
                continue
            elif prop_attributes['immutable']:
                # Property cannot be set by the user
                continue
            elif prop == 'metadata' and prop_attributes['class'].__name__ == 'UnversionedListMeta':
                args['namespace'] = {
                    'description': [
                        'Namespaces provide a scope for names. Names of resources need to be unique within a '
                        'namespace, but not across namespaces. Provide the namespace for the object.'
                    ]
                }
            elif prop == 'metadata' and prop_attributes['class'].__name__ != 'UnversionedListMeta':
                meta_prefix = prefix + '_metadata_' if prefix else ''
                meta_alt_prefix = alternate_prefix + '_metadata_' if alternate_prefix else ''
                if meta_prefix and not meta_alt_prefix:
                    meta_alt_prefix = meta_prefix
                if 'labels' in dir(prop_attributes['class']):
                    args[meta_prefix + 'labels'] = {
                        'type': 'dict',
                    }
                    add_meta('labels', meta_prefix, meta_alt_prefix)
                if 'annotations' in dir(prop_attributes['class']):
                    args[meta_prefix + 'annotations'] = {
                        'type': 'dict',
                    }
                    add_meta('annotations', meta_prefix, meta_alt_prefix)
                if 'namespace' in dir(prop_attributes['class']):
                    args[meta_prefix + 'namespace'] = {}
                    add_meta('namespace', meta_prefix, meta_alt_prefix)
                if 'name' in dir(prop_attributes['class']):
                    args[meta_prefix + 'name'] = {}
                    add_meta('name', meta_prefix, meta_alt_prefix)
            elif prop_attributes['class'].__name__ not in primitive_types and not prop.endswith('params'):
                # prevents infinite recursion
                if prop_attributes['class'] in parent_property_classes:
                    return args
                else:
                    property_classes = parent_property_classes.copy()
                    property_classes.add(prop_attributes['class'])
                # Adds nested properties recursively

                label = prop

                # Provide a more human-friendly version of the prefix
                alternate_label = label\
                    .replace('spec', '')\
                    .replace('template', '')\
                    .replace('config', '')

                p = prefix
                p += '_' + label if p else label
                a = alternate_prefix
                paths = copy.copy(path)
                paths.append(prop)

                if alternate_prefix:
                    # Prevent the last prefix from repeating. In other words, avoid things like 'pod_pod'
                    pieces = alternate_prefix.split('_')
                    alternate_label = alternate_label.replace(pieces[len(pieces) - 1] + '_', '', 1)
                if alternate_label != self.base_model_name and alternate_label not in a:
                    a += '_' + alternate_label if a else alternate_label
                if prop.endswith('params') and 'type' in properties:
                    sub_props = dict()
                    sub_props[prop] = {
                        'class': dict,
                        'immutable': False
                    }
                    args.update(self.__transform_properties(sub_props, prefix=p, path=paths, alternate_prefix=a, parent_property_classes=property_classes))
                else:
                    sub_props = self.properties_from_model_class(prop_attributes['class'])
                    args.update(self.__transform_properties(sub_props, prefix=p, path=paths, alternate_prefix=a, parent_property_classes=property_classes))
            else:
                # Adds a primitive property
                arg_prefix = prefix + '_' if prefix else ''
                arg_alt_prefix = alternate_prefix + '_' if alternate_prefix else ''
                paths = copy.copy(path)
                paths.append(prop)

                property_type = prop_attributes['class'].__name__
                if property_type == 'object':
                    property_type = 'str'

                args[arg_prefix + prop] = {
                    'required': False,
                    'type': property_type,
                    'property_path': paths
                }

                if prop.endswith('params') and 'type' in properties:
                    args[arg_prefix + prop]['type'] = 'dict'

                # Use the alternate prefix to construct a human-friendly alias
                if arg_alt_prefix and arg_prefix != arg_alt_prefix:
                    args[arg_prefix + prop]['aliases'] = [arg_alt_prefix + prop]
                elif arg_prefix:
                    args[arg_prefix + prop]['aliases'] = [prop]

                if prop == 'type':
                    choices = self.__convert_params_to_choices(properties)
                    if len(choices) > 0:
                        args[arg_prefix + prop]['choices'] = choices
        return args


class KubernetesAnsibleModuleHelper(AnsibleMixin, KubernetesObjectHelper):
    pass


class OpenShiftAnsibleModuleHelper(AnsibleMixin, OpenShiftObjectHelper):
    pass
