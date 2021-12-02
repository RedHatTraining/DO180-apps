import io
import os
import sys

from constants import PACKAGE_NAME

SCRIPT_DIR = os.path.dirname(__file__)
LIB_DIR = os.path.join(SCRIPT_DIR, '..', PACKAGE_NAME)


def module_exists(module_name, base_dir):
    filename = module_name + '.py'
    if filename in os.listdir(base_dir):
        return True
    return False


def model_exists(module_name):
    model_dir= os.path.join(LIB_DIR, 'client', 'models')
    return module_exists(module_name, model_dir)


def api_exists(module_name):
    api_dir = os.path.join(LIB_DIR, 'client', 'apis')
    return module_exists(module_name, api_dir)


def module_name_from_import(line, idx):
    return line.split(' ')[1].split('.')[idx]


def process_package(package_file, skip_method):
    with io.open(package_file) as f:
        lines = f.read().splitlines()

    output_lines = []

    for line in lines:
        if skip_method(line):
            continue

        output_lines.append(line)

    with io.open(package_file, mode='w') as f:
        f.write('\n'.join(output_lines))


def process_client_package():
    def skip_method(line):
        if line.startswith('from .models') and not model_exists(module_name_from_import(line, 2)):
            return True
        elif line.startswith('from .apis') and not api_exists(module_name_from_import(line, 2)):
            return True
        return False
    process_package(os.path.join(LIB_DIR, 'client', '__init__.py'), skip_method)


def process_models_package():
    def skip_method(line):
        if line.startswith('from .') and not model_exists(module_name_from_import(line, 1)):
            return True
        return False
    process_package(os.path.join(LIB_DIR, 'client', 'models', '__init__.py'), skip_method)


def process_apis_package():
    def skip_method(line):
        if line.startswith('from .') and not api_exists(module_name_from_import(line, 1)):
            return True
        return False
    process_package(os.path.join(LIB_DIR, 'client', 'apis', '__init__.py'), skip_method)


def main():
    process_client_package()
    process_apis_package()
    process_models_package()

    return 0


sys.exit(main())
