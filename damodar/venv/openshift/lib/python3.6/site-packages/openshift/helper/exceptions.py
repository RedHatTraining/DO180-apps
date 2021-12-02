# -*- coding: utf-8 -*-

import json

class KubernetesException(Exception):
    """
    Raised when there is an error inside of an Ansible module.
    """

    def __init__(self, message, **kwargs):
        """
        Creates an instance of the AnsibleModuleError class.
        :param message: The friendly error message.
        :type message: basestring
        :param kwargs: All other keyword arguments.
        :type kwargs: dict
        """
        self.message = message
        self.value = kwargs
        self.value['message'] = message

    def __str__(self):
        """
        String representation of the instance.
        """
        return json.dumps(self.value)


class OpenShiftException(KubernetesException):
    pass
