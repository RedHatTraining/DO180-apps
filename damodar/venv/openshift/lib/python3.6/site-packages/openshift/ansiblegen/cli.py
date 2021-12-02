# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import argparse
import logging
import sys

from logging import config

from .. import __version__
from ..helper.exceptions import KubernetesException

from .docstrings import KubernetesDocStrings, OpenShiftDocStrings
from .modules import Modules

logger = logging.getLogger(__name__)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'openshift.ansiblegen': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        },
        'openshift.helper.ansible': {
            'level': 'ERROR',
            'propogate': False
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR'
    }
}

AVAILABLE_COMMANDS = {
    'help':       'Display this help message',
    'version':    'Display version information',
    'modules':    'Generates and writes to the filesystem one or more Ansible modules.',
    'docstrings': 'Displays Ansible module doc strings for one or more models.',
}


def subcmd_modules_parser(_, subparser):
    subparser.add_argument('models', action='store',
                           help=u'Optional list of models for which to generate modules. Specify '
                                u'the model Kind using either CamelCase or snake_case.',
                           nargs='*', )
    subparser.add_argument('-v', '--api-version', action='store',
                           help=u'When specified, Modules will only be generated for models '
                                u'that are part of API version.',
                           dest='api_version', default=None)
    subparser.add_argument('-o', '--output-path', action='store',
                           help=u'Specify a path to a directory where modules will be written. '
                                u'Defaults to ./_modules. If the directory does not exist, it '
                                u'will be created.',
                           dest='output_path', default="./_modules")
    subparser.add_argument('-s', '--suppress-stdout', action='store_true',
                           help=u'Suppress writing progress messages to stdout.',
                           dest='suppress_stdout', default=False)


def subcmd_docstrings_parser(_, subparser):
    subparser.add_argument('models', action='store',
                           help=u'List of models for which doc strings will be generated. Specify '
                                u'the model Kind using either CamelCase or snake_case.',
                           nargs='*', )
    subparser.add_argument('-v', '--api-version', action='store',
                           help=u'API version. Defaults to v1.',
                           dest='api_version', default='v1')


def subcmd_version_parser(parser, subparser):
    pass


def subcmd_help_parser(parser, subparser):
    pass


def run_docstrings_cmd(**kwargs):
    """
    Send documentation string and return string to stdout for each model requested

    :param kwargs: parser arguments
    :return: None
    """
    models = kwargs.pop('models')
    api_version = kwargs.pop('api_version')

    if not models:
        raise KubernetesException(
            "ERROR: you must provide one or more models for the docstrings command."
        )

    for model in models:
        try:
            strings = KubernetesDocStrings(model=model, api_version=api_version)
        except KubernetesException:
            try:
                strings = OpenShiftDocStrings(model=model, api_version=api_version)
            except KubernetesException:
                raise
        print("DOCUMENTATION = '''")
        print(strings.documentation)
        print("'''\n")
        print("RETURN = '''")
        print(strings.return_block)
        print("'''\n")


def run_modules_cmd(**kwargs):
    """
    Generate modules
    :param kwargs: parser arguments
    :return: None
    """
    modules = Modules(**kwargs)
    modules.generate_modules()


def commandline():
    """
    Entrypoint for openshift-ansible-gen

    :return: None
    """
    parser = argparse.ArgumentParser(description=u'Uses the OpenShift API models to generate Ansible artifacts')
    parser.add_argument('--debug', action='store_true', dest='debug',
                        help=u'enable debug output', default=False)

    subparsers = parser.add_subparsers(title='subcommand', dest='subcommand')
    subparsers.required = True
    for subcommand in AVAILABLE_COMMANDS:
        if globals().get('subcmd_%s_parser' % subcommand):
            subparser = subparsers.add_parser(subcommand, help=AVAILABLE_COMMANDS[subcommand])
            globals()['subcmd_%s_parser' % subcommand](parser, subparser)

    args = parser.parse_args()

    if args.debug:
        # enable debug output
        LOGGING['loggers']['openshift.ansiblegen']['level'] = 'DEBUG'

    config.dictConfig(LOGGING)

    if args.subcommand == 'help':
        parser.print_help()
        sys.exit(0)
    elif args.subcommand == 'version':
        logger.info("{0} version is {1}".format(__name__, __version__))
        sys.exit(0)
    elif args.subcommand == 'modules':
        if args.suppress_stdout:
            # disable output
            LOGGING['loggers']['openshift.ansiblegen']['level'] = 'CRITICAL'

    try:
        globals()['run_{}_cmd'.format(args.subcommand)](**vars(args))
    except Exception:
        raise
    sys.exit(0)
