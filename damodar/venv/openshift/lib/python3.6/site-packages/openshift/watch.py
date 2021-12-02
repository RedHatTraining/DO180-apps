from kubernetes.watch import Watch as K8sWatch

from openshift import client


class Watch(K8sWatch):

    def __init__(self, return_type=None):
        self._raw_return_type = return_type
        self._stop = False
        self._api_client = client.ApiClient()
        self.resource_version = 0
