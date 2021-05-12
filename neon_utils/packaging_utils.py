# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import sys
import re
import importlib.util
import pkg_resources
import sysconfig

from os.path import exists, join


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
