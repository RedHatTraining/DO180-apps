# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json

from kubernetes.client import models as k8s_models
from kubernetes.client import apis as k8s_apis
from kubernetes.client.rest import ApiException
from urllib3.exceptions import MaxRetryError

from . import VERSION_RX
from .. import config
from ..client import models as openshift_models
from ..client import apis as openshift_apis
from ..client import ApiClient, Configuration
from .base import BaseObjectHelper
from .exceptions import OpenShiftException


class OpenShiftObjectHelper(BaseObjectHelper):
    @staticmethod
    def client_from_config(config_file, context):
        # TODO(fabianvf): probably want to break this branch out or refactor method names
        try:
            return config.new_client_from_config(config_file, context)
        except (IOError, config.ConfigException):
            if not config_file:
                return ApiClient(configuration=Configuration())
            else:
                raise

    @classmethod
    def available_apis(cls):
        apis = ['OapiApi']
        apis.extend([x for x in dir(openshift_apis) if VERSION_RX.search(x)])
        apis.extend([x for x in dir(k8s_apis) if VERSION_RX.search(x)])
        return apis

    @staticmethod
    def get_exception_class():
        return OpenShiftException

    @staticmethod
    def model_class_from_name(model_name):
        try:
            return getattr(openshift_models, model_name)
        except AttributeError:
            return getattr(k8s_models, model_name)

    @staticmethod
    def api_class_from_name(api_name):
        try:
            return getattr(openshift_apis, api_name)
        except AttributeError:
            return getattr(k8s_apis, api_name)

    def create_project(self, metadata, display_name=None, description=None):
        """ Creating a project requires using the project_request endpoint. """

        # TODO: handle admin-level project creation

        w, stream = self._create_stream(None)
        try:
            proj_req = openshift_models.V1ProjectRequest(metadata=metadata, display_name=display_name, description=description)
            openshift_apis.OapiApi(self.api_client).create_project_request(proj_req)
        except ApiException as exc:
            msg = json.loads(exc.body).get('message', exc.reason) if exc.body.startswith('{') else exc.body
            raise OpenShiftException(msg, status=exc.status)
        except MaxRetryError as ex:
            raise OpenShiftException(str(ex.reason))

        self._read_stream(w, stream, metadata.name)

        return self._wait_for_response(metadata.name, None, 'create')
