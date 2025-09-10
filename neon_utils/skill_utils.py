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

from os import getcwd, chdir
from os.path import isfile, dirname, abspath, join
from mock import Mock, patch
from importlib.util import spec_from_file_location, module_from_spec

from ovos_utils.log import LOG


def get_skill_metadata(skill_dir: str) -> dict:
    """
    Get a metadata object for a skill in a given directory.
    """
    setup_py = join(skill_dir, "setup.py")
    pyproject_toml = join(skill_dir, "pyproject.toml")
    readme_md = join(skill_dir, "README.md")

    if isfile(pyproject_toml):
        meta = _get_skill_data_poetry(pyproject_toml)
    elif isfile(setup_py):
        meta = _get_skill_data_setuptools(setup_py)
    elif isfile(readme_md):
        with open(readme_md, encoding="utf-8") as f:
            readme_data = f.read()
        meta = _get_skill_data_readme(readme_data)
    else:
        raise FileNotFoundError(
            f"No setup.py or pyproject.toml found in {skill_dir}"
        )

    # Adding params for backwards-compat.
    meta["desktopFile"] = False
    meta["warning"] = ""
    meta["systemDeps"] = False
    meta.setdefault("requirements", {})
    meta["requirements"].setdefault("system", {})
    meta["requirements"].setdefault("skill", [])
    meta.setdefault("incompatible_skills", [])
    meta["platforms"] = ["i386", "x86_64", "ia64", "arm64", "arm"]
    meta["branch"] = "master"
    meta["foldername"] = None
    meta.setdefault("short_description", meta.get("summary"))

    return meta


def _get_skill_data_poetry(pyproject: str) -> dict:
    """
    Get skill metadata from a pyproject.toml file
    Args:
        pyproject: pyproject.toml file to evaluate
    Returns:
        dict: Skill metadata
    """
    from toml import load

    if not isfile(pyproject):
        raise FileNotFoundError(f"Not a Directory: {pyproject}")
    with open(pyproject, encoding="utf-8") as f:
        data = load(f)
    skill_data = {
        "package_name": data["tool"]["poetry"].get("name", "Unknown"),
        "name": data["tool"]["poetry"].get("name", "Unknown"),
        "description": data["tool"]["poetry"].get("name", "description"),
        "pip_spec": data["tool"]["poetry"].get("name", "Unknown"),
        "license": data["tool"]["poetry"].get("license", "Unknown"),
        "author": data["tool"]["poetry"].get(
            "authors", [""]
        ),  # List of authors
        "tags": data["tool"]["poetry"].get("keywords", []),
        "version": data["tool"]["poetry"].get("version", ""),
    }
    print(data["tool"]["poetry"]["plugins"])
    skill_data["skill_id"] = list(
        data["tool"]["poetry"]
        .get("plugins", {})
        .get("ovos.plugin.skill", {})
        .keys()
    )[0].strip('"')

    # Below match existing Neon skill metadata
    skill_data["title"] = skill_data["name"]
    skill_data["summary"] = skill_data["description"]
    skill_data["short_description"] = skill_data["description"]
    skill_data["credits"] = [skill_data["author"]]
    skill_data["skillname"] = skill_data["name"]

    python_requirements = data["tool"]["poetry"].get("dependencies", {})
    # Parse requirements into expected string format
    python_requirements.pop("python", None)  # Remove python version spec
    skill_data["requirements"] = {
        "python": [f"{k}{v}" for k, v in python_requirements.items()]
    }

    if data["tool"]["poetry"].get("readme"):
        readme_path = join(
            dirname(pyproject), data["tool"]["poetry"]["readme"]
        )
        with open(readme_path) as f:
            readme_data = f.read()
        try:
            readme_metadata = _get_skill_data_readme(readme_data)
        except Exception as e:
            LOG.error(f"Failed to parse README for {skill_data['name']}: {e}")
            readme_metadata = {}
    return {**readme_metadata, **skill_data}


def _get_skill_data_setuptools(setup_py: str) -> dict:
    """
    Get skill metadata from a setup.py file by executing it with a mocked setuptools.setup
    Args:
        setup_py: setup.py file to evaluate
    Returns:
        dict: Skill metadata
    """

    if not isfile(setup_py):
        raise FileNotFoundError(f"File not found: {setup_py}")

    # Create a mock for setuptools.setup
    setup_mock = Mock()

    # Mock setuptools.find_packages as well
    find_packages_mock = Mock(return_value=[])

    # Change to the directory containing setup.py to handle relative paths
    original_cwd = getcwd()
    setup_dir = dirname(abspath(setup_py))

    try:
        chdir(setup_dir)

        # Mock setuptools imports and execute setup.py
        with patch.dict(
            "sys.modules",
            {
                "setuptools": Mock(
                    setup=setup_mock, find_packages=find_packages_mock
                )
            },
        ):
            # Load and execute the setup.py file
            spec = spec_from_file_location("setup", setup_py)
            setup_module = module_from_spec(spec)
            spec.loader.exec_module(setup_module)

        # Get the captured kwargs from the mock
        if not setup_mock.called:
            raise ValueError(f"No setup() call found in {setup_py}")

        captured_kwargs = (
            setup_mock.call_args.kwargs
            if setup_mock.call_args.kwargs
            else setup_mock.call_args.args[0]
            if setup_mock.call_args.args
            else {}
        )

    finally:
        chdir(original_cwd)

    # Build skill_data matching the expected format
    skill_data = {
        "package_name": captured_kwargs.get("name"),
        "pip_spec": captured_kwargs.get("name"),
        "license": captured_kwargs.get("license"),
        "author": captured_kwargs.get("author"),
        "tags": captured_kwargs.get("keywords", []),
        "version": captured_kwargs.get("version"),
        "url": captured_kwargs.get("url"),
    }

    # Extract skill_id from entry_points if available
    skill_data["skill_id"] = captured_kwargs["entry_points"][
        "ovos.plugin.skill"
    ]

    if "github.com" in skill_data["url"]:
        author, skill = skill_data["url"].split("github.com/")[1].split("/")
        skill_data["skillname"] = skill
        skill_data["authorname"] = author

    # Set additional fields to match existing Neon skill metadata format
    skill_data["name"] = skill_data["package_name"]
    skill_data["title"] = skill_data["package_name"]
    skill_data["credits"] = (
        [skill_data["author"]] if skill_data["author"] != "Unknown" else []
    )

    # Handle requirements
    install_requires = captured_kwargs.get("install_requires", [])
    skill_data["requirements"] = {
        "python": install_requires
        if isinstance(install_requires, list)
        else []
    }

    if "long_description" in captured_kwargs:
        readme_data = _get_skill_data_readme(
            captured_kwargs["long_description"]
        )
    else:
        readme_data = {}
    return {**readme_data, **skill_data}


def _get_skill_data_readme(readme_md: str) -> dict:
    """
    Get skill metadata from a README file
    Args:
        readme_md: README.md file contents to evaluate
    Returns:
        dict: Skill metadata
    """
    from neon_utils.parse_utils import clean_quotes

    lines = readme_md.split("\n")
    if not lines or len(lines) <= 1:
        raise ValueError("Empty README data")

    # Initialize parser params
    list_sections = (
        "examples",
        "incompatible skills",
        "platforms",
        "categories",
        "tags",
        "credits",
    )
    valid_sections = list_sections + (
        "summary",
        "short_description",
        "description",
        "warning",
    )
    section = "header"
    category = None
    parsed_data = {}

    def _check_section_start(ln: str):
        # Handle section start
        if ln.startswith(
            "# ![](https://0000.us/klatchat/app/files/"
            "neon_images/icons/neon_paw.png)"
        ):
            # Old style title line
            parsed_data["title"] = ln.split(")", 1)[1].strip()
            parsed_data["icon"] = ln.split("(", 1)[1].split(")", 1)[0].strip()
            return
        elif section == "header" and ln.startswith("# <img src="):
            # Title line
            parsed_data["title"] = ln.split(">", 1)[1].strip()
            parsed_data["icon"] = (
                ln.split("src=", 1)[1]
                .split()[0]
                .strip('"')
                .strip("'")
                .lstrip("./")
            )
            return "summary"
        elif ln.startswith("# ") or ln.startswith("## "):
            # Top-level section
            if ln.startswith("## About"):
                # Handle Mycroft 'About' section
                return "description"
            elif ln.startswith("## Category"):
                # Handle 'Category' as 'Categories'
                return "categories"
            else:
                return line.lstrip("#").strip().lower()
        return

    def _format_readme_line(ln: str):
        nonlocal category
        if section == "incompatible skills":
            if not any((ln.startswith("-"), ln.startswith("*"))):
                return None
            parsed = clean_quotes(ln.lstrip("-").lstrip("*").lower().strip())
            if parsed.startswith("["):
                return parsed.split("(", 1)[1].split(")", 1)[0]
            return parsed
        if section == "examples":
            if not any((ln.startswith("-"), ln.startswith("*"))):
                return None
            parsed = clean_quotes(ln.lstrip("-").lstrip("*").strip())
            if parsed.split(maxsplit=1)[0].lower() == "neon":
                return parsed.split(maxsplit=1)[1]
            else:
                return parsed
        if section == "categories":
            parsed = ln.rstrip("\n").strip("*")
            if ln.startswith("**"):
                category = parsed
            return parsed
        if section == "credits":
            if ln.strip().startswith("["):
                return ln.split("[", 1)[1].split("]", 1)[0]
            return ln.rstrip("\n").lstrip("@")
        if section == "tags":
            return ln.lstrip("#").rstrip("\n")
        if section in list_sections:
            return clean_quotes(ln.lstrip("-").lstrip("*").lower().strip())
        return ln.rstrip("\n").rstrip()

    for line in lines:
        new_section = _check_section_start(line)
        if new_section:
            section = new_section
        elif line.strip():
            parsed_line = _format_readme_line(line)
            if not parsed_line:
                # Nothing to parse in this line
                continue
            if section in list_sections:
                if section not in parsed_data:
                    parsed_data[section] = list()
                parsed_data[section].append(parsed_line)
            else:
                if section not in valid_sections:
                    continue
                elif section not in parsed_data:
                    parsed_data[section] = parsed_line
                else:
                    parsed_data[section] = " ".join(
                        (parsed_data[section], parsed_line)
                    )
    parsed_data["category"] = (
        category or parsed_data.get("categories", [""])[0]
    )
    if parsed_data.get("incompatible skills"):
        parsed_data["incompatible_skills"] = parsed_data.pop(
            "incompatible skills"
        )
    if parsed_data.get("credits") and len(parsed_data["credits"]) == 1:
        parsed_data["credits"] = parsed_data["credits"][0].split(" ")

    return parsed_data
