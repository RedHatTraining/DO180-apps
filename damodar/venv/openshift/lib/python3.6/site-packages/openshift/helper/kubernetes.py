# -*- coding: utf-8 -*-
from __future__ import absolute_import

from kubernetes import config
from kubernetes.client import models as k8s_models
from kubernetes.client import apis as k8s_apis
from kubernetes.client import ApiClient, Configuration

from . import VERSION_RX
from .base import BaseObjectHelper
from .exceptions import KubernetesException


class KubernetesObjectHelper(BaseObjectHelper):
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
        return [x for x in dir(k8s_apis) if VERSION_RX.search(x)]

    @staticmethod
    def get_exception_class():
        return KubernetesException

    @staticmethod
    def model_class_from_name(model_name):
        return getattr(k8s_models, model_name)

    @staticmethod
    def api_class_from_name(api_name):
        return getattr(k8s_apis, api_name)
