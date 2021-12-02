# -*- coding: utf-8 -*-

"""That is shim pure-python module that detects and loads the original selinux
package from outside the current virtualenv, avoiding a very common error
inside virtualenvs: ModuleNotFoundError: No module named 'selinux'
"""

__author__ = """Sorin Sbarnea"""
__email__ = "sorin.sbarnea@gmail.com"
__version__ = "0.1.4"

import json
import os
import platform
import subprocess
import sys

try:
    from importlib import reload  # type: ignore  # noqa
except ImportError:  # py < 34
    from imp import reload  # type: ignore  # noqa

import distro


class add_path(object):
    """Context manager for adding path to sys.path"""

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            sys.path.remove(self.path)
        except ValueError:
            pass


def is_selinux_enabled():
    return 0


def is_selinux_mls_enabled():
    return 0


def should_have_selinux():
    if platform.system() == "Linux" and os.path.isfile("/etc/selinux/config"):
        if distro.id() not in ["ubuntu", "debian"]:
            return True
    return False


# selinux python library should be loaded only on selinux systems
if should_have_selinux():

    def add_location(location):
        """Try to add a possible location for the selinux module"""
        if os.path.isdir(os.path.join(location, "selinux")):
            with add_path(location):
                # And now we replace outselves with the original selinux module
                reload(sys.modules["selinux"])
                # Validate that we can perform libselinux calls
                if sys.modules["selinux"].is_selinux_enabled() not in [0, 1]:
                    raise RuntimeError("is_selinux_enabled returned error.")
                return True
        return False

    def get_system_sitepackages():
        """Get sitepackage locations from system python"""
        # Do not ever use sys.executable here
        # See https://github.com/pycontribs/selinux/issues/17 for details
        system_python = "/usr/bin/python%s" % platform.python_version_tuple()[0]

        system_sitepackages = json.loads(
            subprocess.check_output(
                [
                    system_python,
                    "-c",
                    "import json, site; print(json.dumps(site.getsitepackages()))",
                ]
            ).decode("utf-8")
        )
        return system_sitepackages

    def check_system_sitepackages():
        """Try add selinux module from any of the python site-packages"""

        success = False
        system_sitepackages = get_system_sitepackages()
        for candidate in system_sitepackages:
            success = add_location(candidate)
            if success:
                break

        if not success:
            raise Exception(
                "Failed to detect selinux python bindings at %s" % system_sitepackages
            )

    check_system_sitepackages()
