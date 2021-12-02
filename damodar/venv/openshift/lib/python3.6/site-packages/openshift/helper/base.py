# -*- coding: utf-8 -*-
from __future__ import absolute_import

import inspect
import json
import logging
import math
import os
import re
import time

from abc import ABCMeta, abstractmethod
from logging import config as logging_config

import string_utils

from dictdiffer import diff
from kubernetes import watch
from kubernetes.client.models import V1DeleteOptions
from kubernetes.client.rest import ApiException
from six import add_metaclass
from urllib3.exceptions import MaxRetryError

from . import VERSION_RX
from .exceptions import KubernetesException

from kubernetes.client import Configuration


@add_metaclass(ABCMeta)
class BaseObjectHelper(object):
    api_client = None
    model = None
    properties = None
    base_model_name = None
    base_model_name_snake = None

    logger = logging.getLogger(__name__)

    def __init__(self, api_version=None, kind=None, debug=False, reset_logfile=True, timeout=20, **auth):
        self.version_rx = re.compile("V\d((alpha|beta)\d)?")
        self.api_version = api_version
        self.kind = kind
        self.timeout = timeout  # number of seconds to wait for an API request

        if api_version and kind:
            self.set_model(api_version, kind)

        if debug:
            self.enable_debug(reset_logfile)

        self.set_client_config(**auth)

    @staticmethod
    @abstractmethod
    def client_from_config(config_file, context):
        pass

    @classmethod
    @abstractmethod
    def available_apis(cls):
        # TODO: do proper api discovery
        pass

    @staticmethod
    @abstractmethod
    def api_class_from_name(api_name):
        pass

    @staticmethod
    @abstractmethod
    def model_class_from_name(model_name):
        pass

    @staticmethod
    @abstractmethod
    def get_exception_class():
        pass

    @staticmethod
    def default_configuration_from_auth(**auth):
        """ set Configuration class defaults based on provided auth """
        configuration = Configuration()
        if auth.get('api_key'):
            configuration.api_key = {'authorization': "Bearer %s" % auth.pop('api_key')}
        for k, v in auth.items():
            setattr(configuration, k, v)
        Configuration.set_default(configuration)

    def set_model(self, api_version, kind):
        """ Switch the client's model """
        self.api_version = api_version
        self.kind = kind
        self.model = self.get_model(api_version, kind)
        self.properties = self.properties_from_model_class(self.model)
        self.base_model_name = self.get_base_model_name(self.model.__name__)
        self.base_model_name_snake = self.get_base_model_name_snake(self.base_model_name)

    def set_client_config(self, **auth):
        """ Convenience method for updating the configuration object, and instantiating a new client """
        auth_keys = ['api_key', 'ssl_ca_cert', 'cert_file', 'key_file', 'verify_ssl']

        for key in auth_keys + ['kubeconfig', 'context', 'host']:
            # If a key is not defined in auth, check the environment for a K8S_AUTH_ variable.
            if auth.get(key) is None:
                env_value = os.getenv('K8S_AUTH_{}'.format(key.upper()), None)
                if env_value is not None:
                    auth[key] = env_value

        config_file = auth.get('kubeconfig')
        context = auth.get('context')

        self.default_configuration_from_auth(**auth)

        self.api_client = self.client_from_config(config_file, context)

        if auth.get('host') is not None:
            self.api_client.host = auth['host']

        for key in auth_keys:
            if auth.get(key) is not None:
                if key == 'api_key':
                    self.api_client.configuration.api_key = {'authorization': "Bearer %s" % auth.pop('api_key')}
                else:
                    setattr(self.api_client.configuration, key, auth[key])

    @staticmethod
    def enable_debug(to_file=True, filename='KubeObjHelper.log', reset_logfile=True):
        logger_config = {
            'version': 1,
            'level': 'DEBUG',
            'propogate': False,
            'loggers': {
                'openshift.helper': {
                    'handlers': ['debug_logger'],
                    'level': 'DEBUG',
                    'propagate': False
                }
            }
        }
        if to_file:
            mode = 'w' if reset_logfile else 'a'
            logger_config['handlers'] = {
                'debug_logger': {
                    'class': 'logging.FileHandler',
                    'level': 'DEBUG',
                    'filename': filename,
                    'mode': mode,
                    'encoding': 'utf-8'
                }
            }
        else:
            logger_config['handlers'] = {
                'debug_logger': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG'
                }
            }
        logging_config.dictConfig(logger_config)

    def has_method(self, method_action):
        """
        Determine if the object has a particular method.

        :param method_action: string. one of 'create', 'update', 'delete', 'patch', 'list'
        """
        method = None
        try:
            method = self.lookup_method(method_action)
        except KubernetesException:
            try:
                method = self.lookup_method(method_action, namespace='namespace')
            except KubernetesException:
                return False
        return method is not None

    def fix_serialization(self, obj):
        if obj and obj.kind == "Service" and obj.spec.ports:
            for port in obj.spec.ports:
                try:
                    port.target_port = int(port.target_port)
                except ValueError:
                    pass
        elif obj and obj.kind == "Route" and obj.spec.port:
            try:
                obj.spec.port.target_port = int(obj.spec.port.target_port)
            except ValueError:
                pass
        return obj

    def get_object(self, name=None, namespace=None):
        k8s_obj = None
        method_name = 'list' if self.kind.endswith('list') else 'read'
        try:
            get_method = self.lookup_method(method_name, namespace)
            if name is None and namespace is None:
                k8s_obj = get_method()
            elif name and namespace is None:
                k8s_obj = get_method(name)
            elif namespace and not name:
                k8s_obj = get_method(namespace)
            else:
                k8s_obj = get_method(name, namespace)
        except ApiException as exc:
            if exc.status != 404:
                if self.base_model_name == 'Project' and exc.status == 403:
                    pass
                else:
                    msg = json.loads(exc.body).get('message', exc.reason) if exc.body.startswith('{') else exc.body
                    raise self.get_exception_class()(msg, status=exc.status)
        except MaxRetryError as ex:
            raise self.get_exception_class()(str(ex.reason))

        return k8s_obj

    def patch_object(self, name, namespace, k8s_obj):
        self.logger.debug('Starting patch object')

        k8s_obj.metadata.resource_version = None
        self.__remove_creation_timestamps(k8s_obj)
        w, stream = self._create_stream(namespace)
        return_obj = None
        self.logger.debug("Patching object: {}".format(k8s_obj.to_str()))
        try:
            patch_method = self.lookup_method('patch', namespace)
            if namespace:
                patch_method(name, namespace, k8s_obj)
            else:
                patch_method(name, k8s_obj)
        except ApiException as exc:
            msg = json.loads(exc.body).get('message', exc.reason) if exc.body.startswith('{') else exc.body
            raise self.get_exception_class()(msg, status=exc.status)

        if stream is not None:
            return_obj = self._read_stream(w, stream, name)

        if not return_obj or self.kind in ('project', 'namespace'):
            return_obj = self._wait_for_response(name, namespace, 'patch')

        return self.fix_serialization(return_obj)

    def create_object(self, namespace=None, k8s_obj=None, body=None):
        """
        Send a POST request to the API. Pass either k8s_obj or body.
        :param namespace: namespace value or None
        :param k8s_obj: optional k8s object model
        :param body: optional JSON dict
        :return: new object returned from the API
        """
        self.logger.debug('Starting create object')
        w, stream = self._create_stream(namespace)
        return_obj = None
        name = None
        if k8s_obj:
            name = k8s_obj.metadata.name
        elif body:
            name = body.get('metadata', {}).get('name', None)
        try:
            create_method = self.lookup_method('create', namespace)
            if namespace:
                if k8s_obj:
                    create_method(namespace, k8s_obj)
                else:
                    create_method(namespace, body=body)
            else:
                if k8s_obj:
                    create_method(k8s_obj)
                else:
                    create_method(body=body)
        except ApiException as exc:
            msg = json.loads(exc.body).get('message', exc.reason) if exc.body.startswith('{') else exc.body
            raise self.get_exception_class()(msg, status=exc.status)
        except MaxRetryError as ex:
            raise self.get_exception_class()(str(ex.reason))

        if stream is not None:
            return_obj = self._read_stream(w, stream, name)

        if not return_obj or self.kind in ('project', 'namespace'):
            return_obj = self._wait_for_response(name, namespace, 'create')

        return self.fix_serialization(return_obj)

    def delete_object(self, name, namespace):
        self.logger.debug('Starting delete object {0} {1} {2}'.format(self.kind, name, namespace))
        delete_method = self.lookup_method('delete', namespace)

        if not namespace:
            try:
                if 'body' in inspect.getargspec(delete_method).args:
                    status_obj = delete_method(name, body=V1DeleteOptions(propagation_policy='Foreground'))
                else:
                    status_obj = delete_method(name)
            except ApiException as exc:
                msg = json.loads(exc.body).get('message', exc.reason)
                raise self.get_exception_class()(msg, status=exc.status)
            except MaxRetryError as ex:
                raise self.get_exception_class()(str(ex.reason))
        else:
            try:
                if 'body' in inspect.getargspec(delete_method).args:
                    status_obj = delete_method(name, namespace, body=V1DeleteOptions(propagation_policy='Foreground'))
                else:
                    status_obj = delete_method(name, namespace)
            except ApiException as exc:
                msg = json.loads(exc.body).get('message', exc.reason) if exc.body.startswith('{') else exc.body
                raise self.get_exception_class()(msg, status=exc.status)
            except MaxRetryError as ex:
                raise self.get_exception_class()(str(ex.reason))

        if status_obj is None or status_obj.status == 'Failure':
            msg = 'Failed to delete {}'.format(name)
            if namespace is not None:
                msg += ' in namespace {}'.format(namespace)
            msg += ' status: {}'.format(status_obj)
            raise self.get_exception_class()(msg)

        self._wait_for_response(name, namespace, 'delete')

    def replace_object(self, name, namespace, k8s_obj=None, body=None):
        """ Replace an existing object. Pass in a model object or request dict().
            Will first lookup the existing object to get the resource version and
            update the request.
        """
        self.logger.debug('Starting replace object')

        existing_obj = self.get_object(name, namespace)
        if not existing_obj:
            msg = "Error: Replacing object. Unable to find {}".format(name)
            msg += " in namespace {}".format(namespace) if namespace else ""
            raise self.get_exception_class()(msg)

        if k8s_obj:
            k8s_obj.status = self.properties['status']['class']()
            self.__remove_creation_timestamps(k8s_obj)
            k8s_obj.metadata.resource_version = existing_obj.metadata.resource_version
        elif body:
            body['metadata']['resourceVersion'] = existing_obj.metadata.resource_version

        w, stream = self._create_stream(namespace)
        return_obj = None

        try:
            replace_method = self.lookup_method('replace', namespace)
            if k8s_obj:
                if namespace is None:
                    replace_method(name, k8s_obj)
                else:
                    replace_method(name, namespace, k8s_obj)
            else:
                if namespace is None:
                    replace_method(name, body=body)
                else:
                    replace_method(name, namespace, body=body)
        except ApiException as exc:
            msg = json.loads(exc.body).get('message', exc.reason) if exc.body.startswith('{') else exc.body
            raise self.get_exception_class()(msg, status=exc.status)
        except MaxRetryError as ex:
            raise self.get_exception_class()(str(ex.reason))

        if stream is not None:
            return_obj = self._read_stream(w, stream, name)

        if not return_obj or self.kind in ('project', 'namespace'):
            return_obj = self._wait_for_response(name, namespace, 'replace')

        return self.fix_serialization(return_obj)

    @staticmethod
    def objects_match(obj_a, obj_b):
        """ Test the equality of two objects. Returns bool, list(differences). """
        match = False
        diffs = []
        if obj_a is None and obj_b is None:
            match = True
        elif not obj_a or not obj_b:
            pass
        elif type(obj_a).__name__ != type(obj_b).__name__:
            pass
        else:
            dict_a = obj_a.to_dict()
            dict_b = obj_b.to_dict()
            diffs = list(diff(dict_a, dict_b))
            match = len(diffs) == 0
        return match, diffs

    @classmethod
    def properties_from_model_class(cls, model_class):
        """
        Introspect an object, and return a dict of 'name:dict of properties' pairs. The properties include: class,
        and immutable (a bool).

        :param model_class: An object instantiated from openshift.client.models
        :return: dict
        """
        # Create a list of model properties. Each property is represented as a dict of key:value pairs
        #  If a property does not have a setter, it's considered to be immutable
        properties = [
            {'name': x,
             'immutable': False if getattr(getattr(model_class, x), 'setter', None) else True
             }
            for x in model_class.attribute_map.keys() if isinstance(getattr(model_class, x), property)
        ]

        result = {}
        for prop in properties:
            prop_kind = model_class.swagger_types[prop['name']]
            if prop_kind == 'datetime':
                prop_kind = 'str'
            if prop_kind in ('str', 'int', 'bool', 'object', 'float'):
                prop_class = eval(prop_kind)
            elif prop_kind.startswith('list['):
                prop_class = list
            elif prop_kind.startswith('dict('):
                prop_class = dict
            else:
                try:
                    prop_class = cls.model_class_from_name(prop_kind)
                except AttributeError:
                    prop_class = cls.model_class_from_name(prop_kind)
            result[prop['name']] = {
                'class': prop_class,
                'immutable': prop['immutable']
            }
        return result

    def candidate_apis(self):
        api_match = self.api_version.replace('/', '_').lower()
        return [
            api for api in self.available_apis()
            if api_match in self.attribute_to_snake(api)
            or not VERSION_RX.match(api)
        ]

    def lookup_method(self, operation=None, namespace=None, method_name=None):
        """
        Get the requested method (e.g. create, delete, patch, update) for
        the model object.
        :param operation: one of create, delete, patch, update
        :param namespace: optional name of the namespace.
        :return: pointer to the method
        """
        if not method_name:
            method_name = operation
            method_name += '_namespaced_' if namespace else '_'
            method_name += self.kind.replace('_list', '') if self.kind.endswith('_list') else self.kind

        method = None
        for api in self.candidate_apis():
            api_class = self.api_class_from_name(api)
            method = getattr(api_class(self.api_client), method_name, None)
            if method is not None:
                break

        if method is None:
            msg = "Did you forget to include the namespace?" if not namespace else ""
            raise self.get_exception_class()(
                "Error: method {0} not found for model {1}. {2}".format(method_name, self.kind, msg)
            )
        return method

    @classmethod
    def get_base_model_name(cls, model_name):
        """
        Return model_name with API Version removed.
        :param model_name: string
        :return: string
        """
        return VERSION_RX.sub('', model_name)

    def get_base_model_name_snake(self, model_name):
        """
        Return base model name with API version removed, and remainder converted to snake case
        :param model_name: string
        :return: string
        """
        result = self.get_base_model_name(model_name)
        return self.attribute_to_snake(result)

    @staticmethod
    def attribute_to_snake(name):
        """
        Convert an object property name from camel to snake
        :param name: string to convert
        :return: string
        """
        def replace(m):
            m = m.group(0)
            return m[0] + '_' + m[1:]

        p = r'[a-z][A-Z]|' \
            r'[A-Z]{2}[a-z]'
        result = re.sub(p, replace, name)
        return result.lower()

    def get_model(self, api_version, kind):
        """
        Return the model class for the requested object.

        :param api_version: API version string
        :param kind: The name of object type (i.e. Service, Route, Container, etc.)
        :return: class
        """

        # Handle API paths. In the case of 'batch/', remove it completely, otherwise, replace '/' with '_'.
        api = re.sub(r'batch/', '', api_version, count=0, flags=re.IGNORECASE).replace('/', '_')

        camel_kind = string_utils.snake_case_to_camel(kind)
        camel_api_version = string_utils.snake_case_to_camel(api)

        # capitalize the first letter of the string without lower-casing the remainder
        name = (camel_kind[:1].capitalize() + camel_kind[1:]).replace("Api", "API")
        api = camel_api_version[:1].capitalize() + camel_api_version[1:]

        model_name = api + name
        try:
            model = self.model_class_from_name(model_name)
        except AttributeError:
            raise self.get_exception_class()(
                "Error: {} was not found in client.models. "
                "Did you specify the correct Kind and API Version?".format(model_name)
            )
        return model

    def __remove_creation_timestamps(self, obj):
        """ Recursively look for creation_timestamp property, and set it to None """
        if hasattr(obj, 'swagger_types'):
            for key, value in obj.swagger_types.items():
                if key == 'creation_timestamp':
                    obj.creation_timestamp = None
                    continue
                if value.startswith('dict(') or value.startswith('list['):
                    continue
                if value in ('str', 'int', 'bool'):
                    continue
                if getattr(obj, key) is not None:
                    self.__remove_creation_timestamps(getattr(obj, key))

    def _wait_for_response(self, name, namespace, action):
        """ Wait for an API response """
        tries = 0
        half = math.ceil(self.timeout / 2)
        obj = None

        if self.kind in ('project', 'namespace'):
            # Wait for annotations to be applied
            time.sleep(1)

        while tries <= half:
            obj = self.get_object(name, namespace)
            if action == 'delete':
                if not obj:
                    break
            elif obj and not hasattr(obj, 'status'):
                break
            elif obj and obj.status and hasattr(obj.status, 'phase'):
                if obj.status.phase == 'Active':
                    break
            elif obj and obj.status:
                break
            tries += 2
            time.sleep(2)
        return obj

    def _create_stream(self, namespace):
        """ Create a stream that gets events for the our model """
        w = None
        stream = None
        exception_class = self.get_exception_class()

        try:
            list_method = self.lookup_method('list', namespace)
            w = watch.Watch()
            w._api_client = self.api_client  # monkey patch for access to OpenShift models
            if namespace:
                stream = w.stream(list_method, namespace, _request_timeout=self.timeout)
            else:
                stream = w.stream(list_method, _request_timeout=self.timeout)
        except exception_class:
            pass
        except Exception:
            raise

        return w, stream

    def _read_stream(self, watcher, stream, name):

        return_obj = None

        try:
            for event in stream:
                obj = None
                if event.get('object'):
                    obj_json = event['object'].to_str()
                    self.logger.debug(
                        "EVENT type: {0} object: {1}".format(event['type'], obj_json)
                    )
                    obj = event['object']
                else:
                    self.logger.debug(repr(event))

                if event['object'].metadata.name == name:
                    if event['type'] == 'DELETED':
                        # Object was deleted
                        return_obj = obj
                        watcher.stop()
                        break
                    elif obj is not None:
                        # Object is either added or modified. Check the status and determine if we
                        #  should continue waiting
                        if hasattr(obj, 'status'):
                            if hasattr(obj.status, 'phase'):
                                if obj.status.phase == 'Active':
                                    # TODO other phase values ??
                                    # TODO test namespaces for OpenShift annotations if needed
                                    return_obj = obj
                                    watcher.stop()
                                    break
                            elif hasattr(obj.status, 'conditions'):
                                conditions = obj.status.conditions
                                if conditions and len(conditions) > 0:
                                    # We know there is a status, but it's up to the user to determine meaning.
                                    return_obj = obj
                                    watcher.stop()
                                    break
                            elif obj.kind == 'Service' and obj.status is not None:
                                return_obj = obj
                                watcher.stop()
                                break
                            elif obj.kind == 'Route':
                                route_statuses = set()
                                for route_ingress in obj.status.ingress:
                                    for condition in route_ingress.conditions:
                                        route_statuses.add(condition.type)
                                if route_statuses <= {'Ready', 'Admitted'}:
                                    return_obj = obj
                                    watcher.stop()
                                    break

        except Exception as exc:
            # A timeout occurred
            self.logger.debug('STREAM FAILED: {}'.format(exc))
            pass

        return self.fix_serialization(return_obj)
