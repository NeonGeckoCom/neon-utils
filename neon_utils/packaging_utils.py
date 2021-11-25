# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import re
import importlib.util
import pkg_resources
import sysconfig

from os.path import exists, join
from neon_utils.logger import LOG


def get_packaged_core_version() -> str:
    """
    Get the version of the packaged core in use. Supports Neon, Mycroft, and OVOS default packages.
    Returns:
        Version of the installed core package
    """
    if importlib.util.find_spec("neon-core"):
        return pkg_resources.get_distribution("neon-core")
    elif importlib.util.find_spec("mycroft-core"):
        return pkg_resources.get_distribution("mycroft-core")
    elif importlib.util.find_spec("mycroft-lib"):
        return pkg_resources.get_distribution("mycroft-lib")
    raise ImportError("No Core Package Found")


def get_version_from_file() -> str:
    """
    Get the core version from a .release file, Provides legacy support for Neon
    Returns:
        Version of the cloned core repository
    """
    import glob
    import os
    from neon_utils.configuration_utils import get_neon_local_config
    release_files = glob.glob(
        f'{get_neon_local_config().get("dirVars", {}).get("ngiDir") or os.path.expanduser("~/.neon")}'
        f'/*.release')
    if len(release_files):
        return os.path.splitext(os.path.basename(release_files[0]))[0]
    raise FileNotFoundError("No Version File Found")


def get_neon_core_version() -> str:
    """
    Gets the current version of the installed Neon Core.
    Returns:
        Version of the available/active Neon Core or 0.0 if no release info is found
    """
    try:
        return get_packaged_core_version()
    except ImportError:
        pass

    try:
        return get_version_from_file()
    except FileNotFoundError:
        pass

    return "0.0"


def get_core_root():
    """
    Depreciated 2020.09.01
    :return:
    """
    LOG.warning(f"This method is depreciated, please update to use get_neon_core_root()")
    return get_mycroft_core_root()


def get_neon_core_root():
    """
    Determines the root of the available/active Neon Core. Should be the immediate parent directory of 'neon_core' dir
    Returns:
        Path to the core directory containing 'neon_core'
    """
    site = sysconfig.get_paths()['platlib']
    if exists(join(site, 'neon_core')):
        return join(site, 'neon_core')
    for p in [path for path in sys.path if path != ""]:
        if exists(join(p, "neon_core")):
            return join(p, "neon_core")
        if re.match(".*/lib/python.*/site-packages", p):
            clean_path = "/".join(p.split("/")[0:-4])
            if exists(join(clean_path, "neon_core")):
                return join(clean_path, "neon_core")
            elif exists(join(p, "neon_core")):
                return join(p, "neon_core")
    raise FileNotFoundError("Could not determine core directory")


def get_mycroft_core_root():
    """
    Determines the root of the available/active Neon Core. Should be the immediate parent directory of 'mycroft' dir
    Returns:
        Path to the core directory containing 'mycroft'
    """
    site = sysconfig.get_paths()['platlib']
    if exists(join(site, 'mycroft')):
        return site
    for p in [path for path in sys.path if path != ""]:
        if exists(join(p, "mycroft")):
            return p
        if re.match(".*/lib/python.*/site-packages", p):
            clean_path = "/".join(p.split("/")[0:-4])
            if exists(join(clean_path, "mycroft")):
                return clean_path
            # TODO: Other packages (Neon Core)? DM
            elif exists(join(p, "mycroft")):
                return p
    raise FileNotFoundError("Could not determine core directory")
