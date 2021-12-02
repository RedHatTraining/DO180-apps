from kubernetes.config import load_kube_config
from openshift.client import ApiClient, Configuration


def new_client_from_config(config_file=None, context=None):
    """Loads configuration the same as load_kube_config but returns an ApiClient
    to be used with any API object. This will allow the caller to concurrently
    talk with multiple clusters."""
    client_config = type.__call__(Configuration)
    load_kube_config(config_file=config_file, context=context,
                     client_configuration=client_config)
    return ApiClient(configuration=client_config)
