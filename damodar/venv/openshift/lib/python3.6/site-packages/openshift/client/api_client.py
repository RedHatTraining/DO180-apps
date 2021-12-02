from __future__ import absolute_import

import json
from base64 import b64encode

from kubernetes.client.api_client import ApiClient as K8sApiClient
from kubernetes.client import models as k8s_models

from . import models

class ApiClient(K8sApiClient):
    def _ApiClient__deserialize(self, data, klass):
        if klass == 'RuntimeRawExtension':
            data = {'Raw': b64encode(json.dumps(data).encode()).decode()}
        try:
            return super(ApiClient, self).__deserialize(data, klass)
        except AttributeError:
            try:
                klass = getattr(models, klass)
            except AttributeError:
                klass = getattr(k8s_models, klass)
            return super(ApiClient, self).__deserialize_model(data, klass)

