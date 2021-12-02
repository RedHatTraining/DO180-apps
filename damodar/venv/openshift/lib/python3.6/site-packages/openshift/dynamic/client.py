#!/usr/bin/env python

import os
import sys
import copy
import json
import hashlib
import tempfile
from collections import defaultdict
from functools import partial
from six import PY2, PY3

import yaml
from pprint import pformat

from kubernetes import config, watch
from kubernetes.client.api_client import ApiClient
from kubernetes.client.rest import ApiException

from openshift import __version__
from openshift.dynamic.exceptions import (
    api_exception,
    ResourceNotFoundError,
    ResourceNotUniqueError,
    KubernetesValidateMissing
)

try:
    import kubernetes_validate
    HAS_KUBERNETES_VALIDATE = True
except ImportError:
    HAS_KUBERNETES_VALIDATE = False


__all__ = [
    'DynamicClient',
    'ResourceInstance',
    'Resource',
    'ResourceList',
    'Subresource',
    'ResourceContainer',
    'ResourceField',
]

class CacheEncoder(json.JSONEncoder):

    def default(self, o):
        return o.to_dict()

def cache_decoder(client):

    class CacheDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

        def object_hook(self, obj):
            if '_type' not in obj:
                return obj
            _type = obj.pop('_type')
            if _type == 'Resource':
                return Resource(client=client, **obj)
            elif _type == 'ResourceList':
                return ResourceList(obj['resource'])
            return obj

    return CacheDecoder

def meta_request(func):
    """ Handles parsing response structure and translating API Exceptions """
    def inner(self, resource, *args, **kwargs):
        serialize_response = kwargs.pop('serialize', True)
        try:
            resp = func(self, resource, *args, **kwargs)
        except ApiException as e:
            raise api_exception(e)
        if serialize_response:
            return serialize(resource, resp)
        return resp

    return inner

def serialize(resource, response):
    try:
        return ResourceInstance(resource, load_json(response))
    except ValueError:
        if PY2:
            return response.data
        return response.data.decode('utf8')

def load_json(response):
    if PY2:
        return json.loads(response.data)
    return json.loads(response.data.decode('utf8'))


class DynamicClient(object):
    """ A kubernetes client that dynamically discovers and interacts with
        the kubernetes API
    """

    def __init__(self, client, cache_file=None):
        self.client = client
        self.configuration = client.configuration
        default_cache_id = self.configuration.host
        if PY3:
            default_cache_id = default_cache_id.encode('utf-8')
        default_cachefile_name = 'osrcp-{0}.json'.format(hashlib.md5(default_cache_id).hexdigest())
        self.__resources = ResourceContainer({}, client=self)
        self.__cache_file = cache_file or os.path.join(tempfile.gettempdir(), default_cachefile_name)
        self.__init_cache()

    def __init_cache(self, refresh=False):
        if refresh or not os.path.exists(self.__cache_file):
            self.__cache = {'library_version': __version__}
            refresh = True
        else:
            try:
                with open(self.__cache_file, 'r') as f:
                    self.__cache = json.load(f, cls=cache_decoder(self))
                if self.__cache.get('library_version') != __version__:
                    # Version mismatch, need to refresh cache
                    self.invalidate_cache()
            except Exception:
                self.invalidate_cache()
        self._load_server_info()
        self.__resources.update(self.parse_api_groups())

        if refresh:
            self.__write_cache()

    def __write_cache(self):
        with open(self.__cache_file, 'w') as f:
            json.dump(self.__cache, f, cls=CacheEncoder)

    def invalidate_cache(self):
        self.__init_cache(refresh=True)

    def _load_server_info(self):
        if not self.__cache.get('version'):
            self.__cache['version'] = {'kubernetes': load_json(self.request('get', '/version'))}
            try:
                self.__cache['version']['openshift'] = load_json(self.request('get', '/version/openshift'))
            except ApiException:
                pass
        self.__version = self.__cache['version']

    @property
    def resources(self):
        return self.__resources

    @property
    def version(self):
        return self.__version

    def default_groups(self):
        groups = {}
        groups['api'] = { '': {
            'v1': self.get_resources_for_api_version('api', '', 'v1', True)
        }}

        if self.version.get('openshift'):
            groups['oapi'] = { '': {
                'v1': self.get_resources_for_api_version('oapi', '', 'v1', True)
            }}

        return groups

    def parse_api_groups(self):
        """ Discovers all API groups present in the cluster """
        if not self.__cache.get('resources'):
            prefix = 'apis'
            groups_response = load_json(self.request('GET', '/{}'.format(prefix)))['groups']

            groups = self.default_groups()
            groups[prefix] = {}

            for group in groups_response:
                try:
                    new_group = {}
                    for version_raw in group['versions']:
                        version = version_raw['version']
                        preferred = version_raw == group['preferredVersion']
                        new_group[version] = self.get_resources_for_api_version(prefix, group['name'], version, preferred)
                except ApiException:
                    continue
                groups[prefix][group['name']] = new_group
            self.__cache['resources'] = groups
        return self.__cache['resources']

    def get_resources_for_api_version(self, prefix, group, version, preferred):
        """ returns a dictionary of resources associated with provided groupVersion"""

        resources = defaultdict(list)
        subresources = {}

        path = '/'.join(filter(None, [prefix, group, version]))
        resources_response = load_json(self.request('GET', path))['resources']

        resources_raw = list(filter(lambda resource: '/' not in resource['name'], resources_response))
        subresources_raw = list(filter(lambda resource: '/' in resource['name'], resources_response))
        for subresource in subresources_raw:
            resource, name = subresource['name'].split('/')
            if not subresources.get(resource):
                subresources[resource] = {}
            subresources[resource][name] = subresource

        for resource in resources_raw:
            # Prevent duplicate keys
            for key in ('prefix', 'group', 'api_version', 'client', 'preferred'):
                resource.pop(key, None)

            resourceobj = Resource(
                prefix=prefix,
                group=group,
                api_version=version,
                client=self,
                preferred=preferred,
                subresources=subresources.get(resource['name']),
                **resource
            )
            resources[resource['kind']].append(resourceobj)
            resources['{}List'.format(resource['kind'])].append(ResourceList(resourceobj))
        return resources

    def ensure_namespace(self, resource, namespace, body):
        namespace = namespace or body.get('metadata', {}).get('namespace')
        if not namespace:
            raise ValueError("Namespace is required for {}.{}".format(resource.group_version, resource.kind))
        return namespace

    def serialize_body(self, body):
        if isinstance(body, ResourceInstance):
            return body.to_dict()
        return body or {}

    @meta_request
    def get(self, resource, name=None, namespace=None, **kwargs):
        path = resource.path(name=name, namespace=namespace)
        return self.request('get', path, **kwargs)

    @meta_request
    def create(self, resource, body=None, namespace=None, **kwargs):
        body = self.serialize_body(body)
        if resource.namespaced:
            namespace = self.ensure_namespace(resource, namespace, body)
        path = resource.path(namespace=namespace)
        return self.request('post', path, body=body, **kwargs)

    @meta_request
    def delete(self, resource, name=None, namespace=None, label_selector=None, field_selector=None, **kwargs):
        if not (name or label_selector or field_selector):
            raise ValueError("At least one of name|label_selector|field_selector is required")
        if resource.namespaced and not (label_selector or field_selector or namespace):
            raise ValueError("At least one of namespace|label_selector|field_selector is required")
        path = resource.path(name=name, namespace=namespace)
        return self.request('delete', path, label_selector=label_selector, field_selector=field_selector, **kwargs)

    @meta_request
    def replace(self, resource, body=None, name=None, namespace=None, **kwargs):
        body = self.serialize_body(body)
        name = name or body.get('metadata', {}).get('name')
        if not name:
            raise ValueError("name is required to replace {}.{}".format(resource.group_version, resource.kind))
        if resource.namespaced:
            namespace = self.ensure_namespace(resource, namespace, body)
        path = resource.path(name=name, namespace=namespace)
        return self.request('put', path, body=body, **kwargs)

    @meta_request
    def patch(self, resource, body=None, name=None, namespace=None, **kwargs):
        body = self.serialize_body(body)
        name = name or body.get('metadata', {}).get('name')
        if not name:
            raise ValueError("name is required to patch {}.{}".format(resource.group_version, resource.kind))
        if resource.namespaced:
            namespace = self.ensure_namespace(resource, namespace, body)

        content_type = kwargs.pop('content_type', 'application/strategic-merge-patch+json')
        path = resource.path(name=name, namespace=namespace)

        return self.request('patch', path, body=body, content_type=content_type, **kwargs)

    def watch(self, resource, namespace=None, name=None, label_selector=None, field_selector=None, resource_version=None, timeout=None):
        """
        Stream events for a resource from the Kubernetes API

        :param resource: The API resource object that will be used to query the API
        :param namespace: The namespace to query
        :param name: The name of the resource instance to query
        :param label_selector: The label selector with which to filter results
        :param label_selector: The field selector with which to filter results
        :param resource_version: The version with which to filter results. Only events with
                                 a resource_version greater than this value will be returned
        :param timeout: The amount of time in seconds to wait before terminating the stream

        :return: Event object with these keys:
                   'type': The type of event such as "ADDED", "DELETED", etc.
                   'raw_object': a dict representing the watched object.
                   'object': A ResourceInstance wrapping raw_object.

        Example:
            client = DynamicClient(k8s_client)
            v1_pods = client.resources.get(api_version='v1', kind='Pod')

            for e in v1_pods.watch(resource_version=0, namespace=default, timeout=5):
                print(e['type'])
                print(e['object'].metadata)
        """
        watcher = watch.Watch()
        for event in watcher.stream(
            resource.get,
            namespace=namespace,
            name=name,
            field_selector=field_selector,
            label_selector=label_selector,
            resource_version=resource_version,
            serialize=False,
            timeout_seconds=timeout
        ):
            event['object'] = ResourceInstance(resource, event['object'])
            yield event

    def request(self, method, path, body=None, **params):

        if not path.startswith('/'):
            path = '/' + path

        path_params = params.get('path_params', {})
        query_params = params.get('query_params', [])
        if params.get('pretty') is not None:
            query_params.append(('pretty', params['pretty']))
        if params.get('_continue') is not None:
            query_params.append(('continue', params['_continue']))
        if params.get('include_uninitialized') is not None:
            query_params.append(('includeUninitialized', params['include_uninitialized']))
        if params.get('field_selector') is not None:
            query_params.append(('fieldSelector', params['field_selector']))
        if params.get('label_selector') is not None:
            query_params.append(('labelSelector', params['label_selector']))
        if params.get('limit') is not None:
            query_params.append(('limit', params['limit']))
        if params.get('resource_version') is not None:
            query_params.append(('resourceVersion', params['resource_version']))
        if params.get('timeout_seconds') is not None:
            query_params.append(('timeoutSeconds', params['timeout_seconds']))
        if params.get('watch') is not None:
            query_params.append(('watch', params['watch']))

        header_params = params.get('header_params', {})
        form_params = []
        local_var_files = {}
        # HTTP header `Accept`
        header_params['Accept'] = self.client.select_header_accept([
            'application/json',
            'application/yaml',
            'application/vnd.kubernetes.protobuf'
        ])

        # HTTP header `Content-Type`
        if params.get('content_type'):
            header_params['Content-Type'] = params['content_type']
        else:
            header_params['Content-Type'] = self.client.select_header_content_type(['*/*'])

        # Authentication setting
        auth_settings = ['BearerToken']

        return self.client.call_api(
            path,
            method.upper(),
            path_params,
            query_params,
            header_params,
            body=body,
            post_params=form_params,
            async_req=params.get('async_req'),
            files=local_var_files,
            auth_settings=auth_settings,
            _preload_content=False,
            _return_http_data_only=params.get('_return_http_data_only', True)
        )


    def validate(self, definition, version=None, strict=False):
        """validate checks a kubernetes resource definition

        Args:
            definition (dict): resource definition
            version (str): version of kubernetes to validate against
            strict (bool): whether unexpected additional properties should be considered errors

        Returns:
            warnings (list), errors (list): warnings are missing validations, errors are validation failures
        """
        if not HAS_KUBERNETES_VALIDATE:
            raise KubernetesValidateMissing()

        errors = list()
        warnings = list()
        try:
            if version is None:
                try:
                    version = self.version['kubernetes']['gitVersion']
                except KeyError:
                    version = kubernetes_validate.latest_version()
            kubernetes_validate.validate(definition, version, strict)
        except kubernetes_validate.utils.ValidationError as e:
            errors.append("resource definition validation error at %s: %s" % ('.'.join([str(item) for item in e.path]), e.message))  # noqa: B306
        except kubernetes_validate.utils.SchemaNotFoundError as e:
            warnings.append("Could not find schema for object kind %s with API version %s in Kubernetes version %s (possibly Custom Resource?)" %
                            (e.kind, e.api_version, e.version))
        return warnings, errors


class Resource(object):
    """ Represents an API resource type, containing the information required to build urls for requests """

    def __init__(self, prefix=None, group=None, api_version=None, kind=None,
                 namespaced=False, verbs=None, name=None, preferred=False, client=None,
                 singularName=None, shortNames=None, categories=None, subresources=None, **kwargs):

        if None in (api_version, kind, prefix):
            raise ValueError("At least prefix, kind, and api_version must be provided")

        self.prefix = prefix
        self.group = group
        self.api_version = api_version
        self.kind = kind
        self.namespaced = namespaced
        self.verbs = verbs
        self.name = name
        self.preferred = preferred
        self.client = client
        self.singular_name = singularName or (name[:-1] if name else "")
        self.short_names = shortNames
        self.categories = categories
        self.subresources = {
            k: Subresource(self, **v) for k, v in (subresources or {}).items()
        }

        self.extra_args = kwargs

    def to_dict(self):
        return {
            '_type': 'Resource',
            'prefix': self.prefix,
            'group': self.group,
            'api_version': self.api_version,
            'kind': self.kind,
            'namespaced': self.namespaced,
            'verbs': self.verbs,
            'name': self.name,
            'preferred': self.preferred,
            'singular_name': self.singular_name,
            'short_names': self.short_names,
            'categories': self.categories,
            'subresources': {k: sr.to_dict() for k, sr in self.subresources.items()},
            'extra_args': self.extra_args,
        }

    @property
    def group_version(self):
        if self.group:
            return '{}/{}'.format(self.group, self.api_version)
        return self.api_version

    def __repr__(self):
        return '<{}({}/{})>'.format(self.__class__.__name__, self.group_version, self.name)

    @property
    def urls(self):
        full_prefix = '{}/{}'.format(self.prefix, self.group_version)
        resource_name = self.name.lower()
        return {
            'base': '/{}/{}'.format(full_prefix, resource_name),
            'namespaced_base': '/{}/namespaces/{{namespace}}/{}'.format(full_prefix, resource_name),
            'full': '/{}/{}/{{name}}'.format(full_prefix, resource_name),
            'namespaced_full': '/{}/namespaces/{{namespace}}/{}/{{name}}'.format(full_prefix, resource_name)
        }

    def path(self, name=None, namespace=None):
        url_type = []
        path_params = {}
        if self.namespaced and namespace:
            url_type.append('namespaced')
            path_params['namespace'] = namespace
        if name:
            url_type.append('full')
            path_params['name'] = name
        else:
            url_type.append('base')
        return self.urls['_'.join(url_type)].format(**path_params)

    def __getattr__(self, name):
        if name in self.subresources:
            return self.subresources[name]
        return partial(getattr(self.client, name), self)


class ResourceList(Resource):
    """ Represents a list of API objects """

    def __init__(self, resource):
        self.resource = resource
        self.kind = '{}List'.format(resource.kind)

    def get(self, body=None, **kwargs):
        if body is None:
            return self.resource.get(**kwargs)
        response = copy.deepcopy(body)
        namespace = kwargs.pop('namespace', None)
        response['items'] = [
            self.resource.get(name=item['metadata']['name'], namespace=item['metadata'].get('namespace', namespace), **kwargs).to_dict()
            for item in body['items']
        ]
        return ResourceInstance(self, response)

    def delete(self, body=None, *args, **kwargs):
        response = copy.deepcopy(body)
        namespace = kwargs.pop('namespace', None)
        response['items'] = [
            self.resource.delete(name=item['metadata']['name'], namespace=item['metadata'].get('namespace', namespace), **kwargs).to_dict()
            for item in body['items']
        ]
        return ResourceInstance(self, response)

    def verb_mapper(self, verb, body=None, **kwargs):
        response = copy.deepcopy(body)
        response['items'] = [
            getattr(self.resource, verb)(body=item, **kwargs).to_dict()
            for item in body['items']
        ]
        return ResourceInstance(self, response)

    def create(self, *args, **kwargs):
        return self.verb_mapper('create', *args, **kwargs)

    def replace(self, *args, **kwargs):
        return self.verb_mapper('replace', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.verb_mapper('patch', *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.resource, name)

    def to_dict(self):
        return {
            '_type': 'ResourceList',
            'resource': self.resource.to_dict(),
        }


class Subresource(Resource):
    """ Represents a subresource of an API resource. This generally includes operations
        like scale, as well as status objects for an instantiated resource
    """

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.prefix = parent.prefix
        self.group = parent.group
        self.api_version = parent.api_version
        self.kind = kwargs.pop('kind')
        self.name = kwargs.pop('name')
        self.subresource = self.name.split('/')[1]
        self.namespaced = kwargs.pop('namespaced', False)
        self.verbs = kwargs.pop('verbs', None)
        self.extra_args = kwargs

    #TODO(fabianvf): Determine proper way to handle differences between resources + subresources
    def create(self, body=None, name=None, namespace=None, **kwargs):
        return self.__create(self, body=body, name=name, namespace=namespace, **kwargs)

    @meta_request
    def __create(self, resource, body=None, name=None, namespace=None, **kwargs):
        name = name or body.get('metadata', {}).get('name')
        body = self.parent.client.serialize_body(body)
        if resource.namespaced:
            namespace = self.parent.client.ensure_namespace(resource, namespace, body)
        path = self.path(name=name, namespace=namespace)
        return self.parent.client.request('post', path, body=body, **kwargs)


    @property
    def urls(self):
        full_prefix = '{}/{}'.format(self.prefix, self.group_version)
        return {
            'full': '/{}/{}/{{name}}/{}'.format(full_prefix, self.parent.name, self.subresource),
            'namespaced_full': '/{}/namespaces/{{namespace}}/{}/{{name}}/{}'.format(full_prefix, self.parent.name, self.subresource)
        }

    def __getattr__(self, name):
        return partial(getattr(self.parent.client, name), self)

    def to_dict(self):
        return {
            'kind': self.kind,
            'name': self.name,
            'subresource': self.subresource,
            'namespaced': self.namespaced,
            'verbs': self.verbs,
            'extra_args': self.extra_args,
        }


class ResourceContainer(object):
    """ A convenient container for storing discovered API resources. Allows
        easy searching and retrieval of specific resources
    """

    def __init__(self, resources, client=None):
        self.__resources = resources
        self.__client = client

    def update(self, resources):
        self.__resources = resources

    @property
    def api_groups(self):
        """ list available api groups """
        return [group['name'] for group in load_json(self.__client.request("GET", '/apis'))['groups']]

    def get(self, **kwargs):
        """ Same as search, but will throw an error if there are multiple or no
            results. If there are multiple results and only one is an exact match
            on api_version, that resource will be returned.
        """
        results = self.search(**kwargs)
        # If there are multiple matches, prefer exact matches on api_version
        if len(results) > 1 and kwargs.get('api_version'):
            results = [
                result for result in results if result.group_version == kwargs['api_version']
            ]
        # If there are multiple matches, prefer non-List kinds
        if len(results) > 1 and not all([isinstance(x, ResourceList) for x in results]):
            results = [result for result in results if not isinstance(result, ResourceList)]
        if len(results) == 1:
            return results[0]
        elif not results:
            raise ResourceNotFoundError('No matches found for {}'.format(kwargs))
        else:
            raise ResourceNotUniqueError('Multiple matches found for {}: {}'.format(kwargs, results))

    def search(self, **kwargs):
        """ Takes keyword arguments and returns matching resources. The search
            will happen in the following order:
                prefix: The api prefix for a resource, ie, /api, /oapi, /apis. Can usually be ignored
                group: The api group of a resource. Will also be extracted from api_version if it is present there
                api_version: The api version of a resource
                kind: The kind of the resource
                arbitrary arguments (see below), in random order

            The arbitrary arguments can be any valid attribute for an openshift.dynamic.Resource object
        """
        results = self.__search(self.__build_search(**kwargs), self.__resources)
        if not results:
            self.__client.invalidate_cache()
            results = self.__search(self.__build_search(**kwargs), self.__resources)
        return results

    def __build_search(self, kind=None, api_version=None, prefix=None, **kwargs):
        if api_version and '/' in api_version:
            group, version = api_version.split('/')
            items = [prefix, group, version, kind, kwargs]
        else:
            items = [prefix, '*', api_version, kind, kwargs]

        return list(map(lambda x: x or '*', items))

    def __search(self, parts, resources):
        part = parts[0]
        if part != '*' and resources.get(part):
            if isinstance(resources.get(part), dict):
                return self.__search(parts[1:], resources[part])
            else:
                if parts[1] != '*' and isinstance(parts[1], dict):
                    for resource in resources.get(part):
                        for term, value in parts[1].items():
                            if getattr(resource, term) == value:
                                return [resource]
                else:
                    return resources.get(part)
        elif part == '*':
            matches = []
            for key in resources.keys():
                matches.extend(self.__search([key] + parts[1:], resources))
            return matches
        return []

    def __iter__(self):
        for _, groups in self.__resources.items():
            for _, versions in groups.items():
                for _, resources in versions.items():
                    for _, resource in resources.items():
                        yield resource


class ResourceField(object):
    """ A parsed instance of an API resource attribute. It exists
        solely to ease interaction with API objects by allowing
        attributes to be accessed with '.' notation
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return pformat(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __getitem__(self, name):
        return self.__dict__.get(name)

    # Here resource.items will return items if available or resource.__dict__.items function if not
    # resource.get will call resource.__dict__.get after attempting resource.__dict__.get('get')
    def __getattr__(self, name):
        return self.__dict__.get(name, getattr(self.__dict__, name, None))

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __dir__(self):
        return dir(type(self)) + list(self.__dict__.keys())

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield (k, v)


class ResourceInstance(object):
    """ A parsed instance of an API resource. It exists solely to
        ease interaction with API objects by allowing attributes to
        be accessed with '.' notation.
    """

    def __init__(self, resource, instance):
        self.resource_type = resource
        # If we have a list of resources, then set the apiVersion and kind of
        # each resource in 'items'
        kind = instance['kind']
        if kind.endswith('List') and 'items' in instance:
            kind = instance['kind'][:-4]
            for item in instance['items']:
                if 'apiVersion' not in item:
                    item['apiVersion'] = instance['apiVersion']
                if 'kind' not in item:
                    item['kind'] = kind

        self.attributes = self.__deserialize(instance)

    def __deserialize(self, field):
        if isinstance(field, dict):
            return ResourceField(**{
                k: self.__deserialize(v) for k, v in field.items()
            })
        elif isinstance(field, (list, tuple)):
            return [self.__deserialize(item) for item in field]
        else:
            return field

    def __serialize(self, field):
        if isinstance(field, ResourceField):
            return {
                k: self.__serialize(v) for k, v in field.__dict__.items()
            }
        elif isinstance(field, (list, tuple)):
            return [self.__serialize(item) for item in field]
        elif isinstance(field, ResourceInstance):
            return field.to_dict()
        else:
            return field

    def to_dict(self):
        return self.__serialize(self.attributes)

    def to_str(self):
        return repr(self)

    def __repr__(self):
        return "ResourceInstance[{}]:\n  {}".format(
            self.attributes.kind,
            '  '.join(yaml.safe_dump(self.to_dict()).splitlines(True))
        )

    def __getattr__(self, name):
        return getattr(self.attributes, name)

    def __getitem__(self, name):
        return self.attributes[name]

    def __dir__(self):
        return dir(type(self)) + list(self.attributes.__dict__.keys())


def main():
    config.load_kube_config()
    client = DynamicClient(ApiClient())
    ret = []
    for resource in client.resources:
        key = '{}.{}'.format(resource.group_version, resource.kind)
        item = {}
        item[key] = {k: v for k, v in resource.__dict__.items() if k not in ('client', 'subresources', 'resource')}
        if isinstance(resource, ResourceList):
            item[key]["resource"] = '{}.{}'.format(resource.resource.group_version, resource.resource.kind)
        else:
            item[key]['subresources'] = {}
            for name, value in resource.subresources.items():
                item[key]['subresources'][name] = {k: v for k, v in value.__dict__.items() if k != 'parent'}
            item[key]['urls'] = resource.urls
        ret.append(item)

    print(yaml.safe_dump(sorted(ret, key=lambda x: x.keys()[0].replace('List', '1')), default_flow_style=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
