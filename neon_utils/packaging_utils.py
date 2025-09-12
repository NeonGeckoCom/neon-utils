# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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
import subprocess
import importlib.util
from typing import Tuple, Optional, List
from tempfile import mkstemp

import sysconfig

from os.path import exists, join, isfile
from ovos_utils.log import LOG, deprecated


def parse_version_string(ver: str) -> Tuple[int, int, int, Optional[int]]:
    """
    Parse a semver string into its component versions as ints
    :param ver: Version string to parse
    :returns: Tuple major, minor, patch, Optional(revision)
    """
    parts = ver.split('.')
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = parts[2] if len(parts) > 2 else '0'
    if not patch.isnumeric():
        patch, alpha = re.split(r"\D+", patch, 1)
        alpha = int(alpha)
    else:
        alpha = None
    patch = int(patch)
    return major, minor, patch, alpha


def get_package_version_spec(pkg: str):
    """
    Locate an installed package and return its reported version
    :param pkg: string package name to locate
    :returns: Version string as reported by importlib.metadata
    :raises: PackageNotFoundError if requested package isn't installed
    """
    try:
        from importlib.metadata import version
    except ImportError:
        # Fallback for Python < 3.8
        from importlib_metadata import version
    
    return version(pkg)


def get_package_dependencies(pkg: str):
    """
    Get the dependencies for an installed package
    :param pkg: string package name to evaluate
    :returns: list of string dependencies (equivalent to requirements.txt)
    :raises PackageNotFoundError if requested package isn't installed
    """
    try:
        from importlib.metadata import requires
    except ImportError:
        # Fallback for Python < 3.8
        from importlib_metadata import requires
    
    requirements = requires(pkg)
    if requirements is None:
        return []
    constraints_spec = [req.split('[', 1)[0].split(';', 1)[0] for req in requirements]
    LOG.debug(constraints_spec)
    return constraints_spec


@deprecated("Reference `neon_core.version.__version__` directly", "2.0.0")
def get_packaged_core_version() -> str:
    """
    Get the version of the packaged core in use.
    Supports Neon, Mycroft, and OVOS default packages.
    Returns:
        Version of the installed core package
    """
    if importlib.util.find_spec("neon-core"):
        return get_package_version_spec("neon-core")
    elif importlib.util.find_spec("mycroft-core"):
        return get_package_version_spec("mycroft-core")
    elif importlib.util.find_spec("mycroft-lib"):
        return get_package_version_spec("mycroft-lib")
    raise ImportError("No Core Package Found")


@deprecated("Reference `neon_core.version.__version__` directly", "2.0.0")
def get_neon_core_version() -> str:
    """
    Gets the current version of the installed Neon Core.
    Returns:
        Version of the available/active Neon Core or
        0.0 if no release info is found
    """
    try:
        from neon_core.version import __version__
        return __version__
    except ImportError:
        pass
    try:
        return get_packaged_core_version()
    except ImportError:
        pass
    return "0.0"


@deprecated("Use system modules to locate packages and resources", "2.0.0")
def get_core_root():
    """
    Depreciated 2020.09.01
    :return:
    """
    return get_mycroft_core_root()


@deprecated("Use system modules to locate packages and resources", "2.0.0")
def get_neon_core_root():
    """
    Determines the root of the available/active Neon Core.
    Directory returned is the root of the `neon_core` package
    Returns:
        Path to the 'neon_core' directory
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


@deprecated("Use system modules to locate packages and resources", "2.0.0")
def get_mycroft_core_root():
    """
    Determines the root of the available/active Neon Core.
    Should be the immediate parent directory of 'mycroft' dir
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


@deprecated("Use neon_utils.skill_utils.get_skill_metadata", "2.0.0")
def build_skill_spec(skill_dir: str) -> dict:
    """
    Build dict contents of a skill.json file.
    :param skill_dir: path to skill directory to parse
    :returns: dict skill.json spec
    """
    from neon_utils.skill_utils import get_skill_metadata

    # Non-packaged skills are deprecated. Support is patched in here for
    # Backwards-compatibility only

    def get_skill_license():
        try:
            with open(join(skill_dir, "LICENSE.md")) as f:
                contents = f.read()
        except FileNotFoundError:
            return "Unknown"
        except Exception as e:
            LOG.error(e)
            return "Unknown"
        if "BSD-3" in contents:
            return "BSD-3-Clause"
        if "Apache License" in contents:
            return "Apache 2.0"
        if "Neon AI Non-commercial Friendly License 2.0" in contents:
            return "Neon 2.0"
        if "Neon AI Non-commercial Friendly License" in contents:
            return "Neon 1.0"

    skill_meta = get_skill_metadata(skill_dir)
    if skill_meta.get("license") is None:
        skill_meta["license"] = get_skill_license()

    if skill_meta["requirements"].get("python") is None and \
            isfile(join(skill_dir, "requirements.txt")):
        try:
            with open(join(skill_dir, "requirements.txt")) as f:
                requirements = f.read().split('\n')
            requirements = [r for r in requirements
                            if r and not r.startswith('#')]
            skill_meta["requirements"]["python"] = requirements
        except Exception as e:
            LOG.error(e)
            skill_meta["requirements"]["python"] = []

    return skill_meta

def install_packages_from_pip(core_module: str, packages: List[str],
                              force_reinstall: bool = False) -> int:
    """
    Install a Python package using pip
    :param core_module: string neon core module to install dependency for
    :param packages: List(string) list of packages to install
    :param force_reinstall: force re-installation of packages
    :returns: int pip exit code
    """
    def _pip_install(command_args: List[str]) -> int:
        try:
            result = subprocess.check_call([sys.executable, '-m', 'pip'] + command_args)
            return result
        except subprocess.CalledProcessError as e:
            LOG.error(f"Error installing {command_args}: {e}")
            return e.returncode

    _, tmp_constraints_file = mkstemp()
    _, tmp_requirements_file = mkstemp()

    with open(tmp_constraints_file, 'w', encoding="utf8") as f:
        constraints = '\n'.join(get_package_dependencies(core_module))
        f.write(constraints)
        LOG.info(f"Constraints={constraints}")

    with open(tmp_requirements_file, "w", encoding="utf8") as f:
        for pkg in packages:
            f.write(f"{pkg}\n")

    LOG.info(f"Requested installation of plugins: {packages}")
    pip_args = ['install', '-r', tmp_requirements_file, '-c', tmp_constraints_file]
    if stat := _pip_install(pip_args) != 0:
        return stat

    if force_reinstall:
        LOG.info(f"Requested forced re-installation of plugins: {packages}")
        pip_args.extend(['--no-deps', '--force-reinstall'])
        stat = _pip_install(pip_args)

    return stat


def get_installed_prereleases() -> List[Tuple[str, str]]:
    """
    Get a list of installed pre-release packages.
    @return: List of tuple (pkg_name, version)
    """
    from subprocess import run
    packages = run(["pip", "list"],
                   capture_output=True).stdout.decode("utf-8")
    prerelease_pkgs = list()
    for line in packages.split('\n'):
        if not line:
            continue
        name, version = line.split()
        if name == "Package" or not name.replace('-', ''):
            continue
        if not version.replace('.', '').isnumeric():
            if "post" in version:
                LOG.debug(f"post release {name}:{version}")
                continue
            prerelease_pkgs.append((name, version))
    return prerelease_pkgs

