# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import logging
import inspect
import os
import shutil
import string_utils
import tempfile

from jinja2 import Environment, FileSystemLoader
from kubernetes.client import models as k8s_models

from ..client import models as openshift_models
from ..helper import VERSION_RX
from ..helper.exceptions import OpenShiftException

from .docstrings import KubernetesDocStrings, OpenShiftDocStrings

logger = logging.getLogger(__name__)

# Once the modules land in Ansible core, this should not change
ANSIBLE_VERSION_ADDED = "2.3.0"

JINJA2_TEMPLATE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), 'templates'))


class Modules(object):

    def __init__(self, **kwargs):
        self.api_version = kwargs.pop('api_version')
        self.output_path = os.path.normpath(kwargs.pop('output_path'))
        logger.debug("output_path: {}".format(self.output_path))

        # Evaluate openshift.models.*, and determine which models should be a module
        requested_models = kwargs.pop('models')
        self._k8s_models = self.__get_models_for_package(k8s_models, self.api_version, requested_models)
        self._openshift_models = self.__get_models_for_package(openshift_models, self.api_version, requested_models)

    @staticmethod
    def __get_models_for_package(model_package, api_version, requested_models):
        models = []
        for model, model_class in inspect.getmembers(model_package):
            if model == 'V1ProjectRequest':
                continue
            if 'kind' in dir(model_class) and ('metadata' in dir(model_class) or
                                               'spec' in dir(model_class)):
                # models with a 'kind' are top-level objects that we care about
                matches = VERSION_RX.match(model)
                if not matches:
                    # exclude unversioned models
                    continue
                model_api = matches.group(0)
                base_model_name = model.replace(model_api, '')
                model_name_snake = string_utils.camel_case_to_snake(base_model_name).lower()
                model_api_snake = string_utils.camel_case_to_snake(model_api).lower()
                if requested_models and \
                   base_model_name not in requested_models and \
                   model_name_snake not in requested_models:
                    continue
                if api_version:
                    # only include models for the requested API version
                    if model_api == api_version.capitalize():
                        models.append({
                            'model': model,
                            'model_api': model_api,
                            'model_api_snake': model_api_snake,
                            'base_model_name': base_model_name,
                            'model_name_snake': model_name_snake
                        })
                else:
                    models.append({
                        'model': model,
                        'model_api': model_api,
                        'model_api_snake': model_api_snake,
                        'base_model_name': base_model_name,
                        'model_name_snake': model_name_snake
                    })
        return models

    def generate_modules(self):
        """
        Create requested Ansible modules, writing them to self.output_path.

        :return: None
        """
        self.__generate_modules_impl(self._k8s_models, 'k8s', self.output_path)
        if len(self._k8s_models):
            print("Generated {} k8s_ modules".format(len(self._k8s_models)))

        self.__generate_modules_impl(self._openshift_models, 'openshift', self.output_path)
        if len(self._openshift_models):
            print("Generated {} openshift modules".format(len(self._openshift_models)))

    @classmethod
    def __generate_modules_impl(cls, models, prefix, output_path):
        """
        Create requested Ansible modules, writing them to output_path.

        :return: None
        """
        module_path = output_path
        cls.__create_output_path(module_path)
        temp_dir = os.path.realpath(tempfile.mkdtemp())  # jinja temp dir
        for model in models:
            module_name = "{}_{}_{}.py".format(prefix,
                                               model['model_api_snake'],
                                               model['model_name_snake'])
            if prefix == 'openshift':
                docs = OpenShiftDocStrings(model['model_name_snake'], model['model_api_snake'])
            else:
                docs = KubernetesDocStrings(model['model_name_snake'], model['model_api_snake'])
            context = {
                'documentation_string': docs.documentation,
                'return_string': docs.return_block,
                'examples_string': docs.examples,
                'kind': model['model_name_snake'],
                'api_version': model['model_api_snake']
            }
            template_file = prefix + '_module.j2'
            cls.__jinja_render_to_file(JINJA2_TEMPLATE_PATH, template_file,
                                       module_name, temp_dir, module_path,
                                       **context)
        shutil.rmtree(temp_dir)

    @classmethod
    def __jinja_render_to_file(cls, template_path, template_file, module_name,
                               temp_dir, module_path, **context):
        """
        Create the module from a jinja template.

        :param template_file: name of the template file
        :param module_name: the destination file name
        :param temp_dir: a temporary working dir for jinja
        :param context: dict of substitution variables
        :return: None
        """
        j2_tmpl_path = template_path
        j2_env = Environment(loader=FileSystemLoader(j2_tmpl_path), keep_trailing_newline=True)
        j2_tmpl = j2_env.get_template(template_file)
        rendered = j2_tmpl.render(dict(temp_dir=temp_dir, **context))
        with open(os.path.normpath(os.path.join(module_path, module_name)), 'wb') as f:
            f.write(rendered.encode('utf8'))

    @classmethod
    def __create_output_path(cls, output_path):
        """
        Attempt to create the output path, if it does not already exist

        :return: None
        """
        if os.path.exists(output_path):
            if not os.path.isdir(output_path):
                raise OpenShiftException("ERROR: expected {} to be a directory.".format(output_path))
        else:
            try:
                os.makedirs(output_path, 0o775)
            except os.error as exc:
                raise OpenShiftException("ERROR: could not create {0} - {1}".format(output_path, str(exc)))
