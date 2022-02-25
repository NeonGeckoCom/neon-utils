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

import re
import json
import os
import sys
import shutil

from copy import deepcopy
from os.path import *
from collections.abc import MutableMapping
from contextlib import suppress
from glob import glob
from ovos_utils.json_helper import load_commented_json
from ovos_utils.configuration import read_mycroft_config, LocalConf
from ruamel.yaml import YAML
from typing import Optional

from neon_utils.location_utils import get_full_location
from neon_utils.logger import LOG
from neon_utils.authentication_utils import find_neon_git_token, populate_github_token_config, build_new_auth_config
from neon_utils.lock_utils import create_lock
from neon_utils.file_utils import path_is_read_writable, create_file
from neon_utils.packaging_utils import get_package_version_spec


class NGIConfig:
    configuration_list = dict()
    # configuration_locks = dict()

    def __init__(self, name, path=None, force_reload: bool = False):
        self.name = name
        self.path = path or get_config_dir()
        self.parser = YAML()
        lock_filename = join(self.path, f".{self.name}.lock")
        self.lock = create_lock(lock_filename)
        self._pending_write = False
        self._content = dict()
        self._loaded = os.path.getmtime(self.file_path)
        if not force_reload and self.__repr__() in NGIConfig.configuration_list:
            cache = NGIConfig.configuration_list[self.__repr__()]
            cache.check_reload()
            self._content = cache.content
        else:
            self._content = self._load_yaml_file()
            NGIConfig.configuration_list[self.__repr__()] = self
        self._disk_content_hash = hash(repr(self._content))

    @property
    def file_path(self):
        """
        Returns the path to the yml file associated with this configuration
        Returns: path to this configuration yml
        """
        file_path = join(self.path, self.name + ".yml")
        if not isfile(file_path):
            if path_is_read_writable(self.path):
                create_file(file_path)
                LOG.debug(f"New YAML created: {file_path}")
            else:
                raise PermissionError(f"Cannot write to path: {self.path}")
        return file_path

    @property
    def requires_reload(self) -> bool:
        """
        Checks if yml file on disk has been modified since this config instance was last updated
        :returns: True if yml modified time is different than at last update
        """
        return self._loaded != os.path.getmtime(self.file_path)

    def check_reload(self):
        """
        Conditionally calls `self.check_for_updates` if `self.requires_reload` returns True.
        """
        if self.requires_reload:
            self.check_for_updates()

    def write_changes(self) -> bool:
        """
        Writes any changes to disk. If disk contents have changed, this config object will not modify config files
        :return: True if changes were written, False if disk config has been updated.
        """
        # TODO: Add some param to force overwrite? DM
        if self._pending_write or self._disk_content_hash != hash(repr(self._content)):
            return self._write_yaml_file()

    def populate(self, content, check_existing=False):
        if not check_existing:
            self.__add__(content)
            return
        old_content = deepcopy(self._content)
        self._content = dict_merge(content, self._content)  # to_change, one_with_all_keys
        if old_content == self._content:
            LOG.warning(f"Update called with no change: {self.file_path}")
            return
        if not self.write_changes():
            LOG.error("Disk contents are newer than this config object, changes were not written.")

    def remove_key(self, *key):
        for item in key:
            self.__sub__(item)

    def make_equal_by_keys(self, other: MutableMapping, recursive: bool = True, depth: int = 1):
        """
        Adds and removes keys from this config such that it has the same keys as 'other'. Configuration values are
        preserved with any added keys using default values from 'other'.
        Args:
            other: dict of keys and default values this configuration should have
            recursive: flag to indicate configuration may be merged recursively
            depth: int depth to recurse (0 includes top-level keys only)
        """
        with self.lock:
            old_content = deepcopy(self._content)
            if not recursive:
                depth = 0
            self._content = dict_make_equal_keys(self._content, other, depth)
            if old_content == self._content:
                return

        if not self.write_changes():
            # This is probably because multiple instances are syncing with default config simultaneously
            LOG.warning("Disk contents are newer than this config object, changes were not written.")
            self.check_reload()
            with self.lock:
                old_content = deepcopy(self._content)
                self._content = dict_make_equal_keys(self._content, other, depth)
            if old_content != self._content:
                LOG.error("Still found changes, writing them")
                success = self.write_changes()
                if not success:
                    LOG.error("Failed to write changes! Disk and config object are out of sync")

    def update_keys(self, other):
        """
        Adds keys to this config such that it has all keys in 'other'. Configuration values are
        preserved with any added keys using default values from 'other'.
        Args:
            other: dict of keys and default values this should be added to this configuration
        """
        with self.lock:
            old_content = deepcopy(self._content)
            self._content = dict_update_keys(self._content, other)  # to_change, one_with_all_keys
        if old_content == self._content:
            LOG.warning(f"Update called with no change: {self.file_path}")
            return

        if not self.write_changes():
            # This is probably because multiple instances are syncing with default config simultaneously
            LOG.warning("Disk contents are newer than this config object, changes were not written.")
            self.check_reload()
            with self.lock:
                old_content = deepcopy(self._content)
                self._content = dict_update_keys(old_content, other)
            if old_content != self._content:
                LOG.error("Still found changes, writing them")
                success = self.write_changes()
                if not success:
                    LOG.error("Failed to write changes! Disk and config object are out of sync")

    def check_for_updates(self) -> dict:
        """
        Reloads updated configuration from disk. Used to reload changes when other instances modify a configuration
        Returns:Updated configuration.content
        """
        new_content = self._load_yaml_file()
        if new_content:
            LOG.debug(f"{self.name} Checked for Updates")
            self._content = new_content
        elif self._content:
            LOG.error("new_content is empty! keeping current config")
        return self._content

    def update_yaml_file(self, header=None, sub_header=None, value="", multiple=False, final=False):
        """
        Called by class's children to update, create, or initiate a new parameter in the
        specified YAML file. Creates and updates headers, adds or overwrites preference elements,
        associates value to the created or existing field. Recursive if creating a new
        header-preference-value combo.
        :param multiple: true if more than one continuous write is coming
        :param header: string with the new or existing main header
        :param sub_header: new or existing subheader (sublist)
        :param value: any value that should be associated with the headers.
        :param final: true if this is the last change when skip_reload was true
        :return: pre-existing parameter if nothing to update or error if invalid yaml_type.
        """
        # with self.lock.acquire(30):
        self.check_reload()
        before_change = self._content

        LOG.debug(value)
        if header and sub_header:
            try:
                before_change[header][sub_header] = value
            except KeyError:
                before_change[header] = {sub_header: value}
                return
        elif header and not sub_header:
            try:
                before_change[header] = value
            except Exception as x:
                LOG.error(x)
        else:
            LOG.debug("No change needed")
            if not final:
                return

        if not multiple:
            if not self.write_changes():
                LOG.error("Disk contents are newer than this config object, changes were not written.")
        else:
            LOG.debug("More than one change")
            self._pending_write = True

    def export_to_json(self) -> str:
        """
        Export this configuration to a json file
        Returns: path to exported file
        """
        json_filename = os.path.join(self.path, f"{self.name}.json")
        write_to_json(self._content, json_filename)
        return json_filename

    def from_dict(self, pref_dict: dict):
        """
        Constructor to build this configuration object with the passed dict of data
        Args:
            pref_dict: dict to populate configuration with

        Returns: this object

        """
        self._content = pref_dict

        if not self.write_changes():
            LOG.error("Disk contents are newer than this config object, changes were not written.")
        return self

    def from_json(self, json_path: str):
        """
        Constructor to build this configuration object with the passed json file
        Args:
            json_path: Path to json file to populate configuration with

        Returns: this object

        """
        self._content = load_commented_json(json_path)

        if not self.write_changes():
            LOG.error("Disk contents are newer than this config object, changes were not written.")
        return self

    def _load_yaml_file(self) -> dict:
        """
        Loads and parses the YAML file at a given filepath into the Python
        dictionary object.
        :return: dictionary, containing all keys and values from the most current
                 selected YAML.
        """
        try:
            with self.lock:
                with open(self.file_path, 'r') as f:
                    config = self.parser.load(f)
                if not config:
                    LOG.debug(f"Empty config file found at: {self.file_path}")
                    config = dict()
                self._loaded = os.path.getmtime(self.file_path)
            return config
        except FileNotFoundError:
            LOG.error(f"Configuration file not found! ({self.file_path})")
        except PermissionError:
            LOG.error(f"Permission Denied! ({self.file_path})")
        except Exception as c:
            LOG.error(f"{self.file_path} Configuration file error: {c}")
        return dict()

    def _write_yaml_file(self) -> bool:
        """
        Overwrites and/or updates the YML at the specified file_path.
        :return: True if changes were written to disk, else False
        """
        to_write = deepcopy(self._content)
        if not to_write:
            LOG.error(f"Config content empty! Skipping write to disk and reloading")
            return False
        if not path_is_read_writable(self.file_path):
            LOG.warning(f"Insufficient write permissions: {self.file_path}")
            return False
        with self.lock:
            if self._loaded != os.path.getmtime(self.file_path):
                LOG.warning("File on disk modified! Skipping write to disk")
                return False
            tmp_filename = join(self.path, f".{self.name}.tmp")
            # LOG.debug(f"tmp_filename={tmp_filename}")
            shutil.copy2(self.file_path, tmp_filename)
            try:
                with open(self.file_path, 'w+') as f:
                    self.parser.dump(to_write, f)
                    LOG.debug(f"YAML updated {self.name}")
                self._loaded = os.path.getmtime(self.file_path)
                self._pending_write = False
                self._disk_content_hash = hash(repr(self._content))
            except Exception as e:
                LOG.error(e)
                LOG.info(f"Restoring config from tmp file backup")
                shutil.copy2(tmp_filename, self.file_path)
            return True

    @property
    def content(self) -> dict:
        """
        Loads any changes from disk and returns an updated configuration dict
        Returns:
        dict content of this configuration object
        """
        self.check_reload()
        return self._content

    def get(self, *args) -> any:
        """
        Wraps content.get() to provide standard access to an updated configuration like a Python dictionary.
        Args:
            *args: args passed to self.content.get() (key and default value)

        Returns:
        self.content.get(*args)
        """
        return self.content.get(*args)

    def __getitem__(self, item):
        return self.content.get(item)

    def __contains__(self, item):
        return item in self._content

    def __setitem__(self, key, value):
        # LOG.info(f"Config changes pending write to disk!")
        self._pending_write = True
        self._content[key] = value

    def __repr__(self):
        return f"NGIConfig('{self.name}')@{self.file_path}"

    def __str__(self):
        return f"{self.file_path}: {json.dumps(self._content, indent=4)}"

    def __add__(self, other):
        # with self.lock.acquire(30):
        if other:
            if not isinstance(other, NGIConfig) and not isinstance(other, MutableMapping):
                raise AttributeError("__add__ expects dict or config object as argument")
            to_update = other
            if isinstance(other, NGIConfig):
                to_update = other._content
            if self._content:
                self._content.update(to_update)
            else:
                self._content = to_update
        else:
            raise TypeError("__add__ expects an argument other than None")
        if not self.write_changes():
            LOG.error("Disk contents are newer than this config object, changes were not written.")

    def __sub__(self, *other):
        # with self.lock.acquire(30):
        if other:
            for element in other:
                if isinstance(element, NGIConfig):
                    to_remove = list(element._content.keys())
                elif isinstance(element, MutableMapping):
                    to_remove = list(element.keys())
                elif isinstance(element, list):
                    to_remove = element
                elif isinstance(element, str):
                    to_remove = [element]
                else:
                    raise AttributeError("__add__ expects dict, list, str, or config object as the argument")

                if self._content:
                    self._content = delete_recursive_dictionary_keys(self._content, to_remove)
                else:
                    raise TypeError("{} config is empty".format(self.name))
        else:
            raise TypeError("__sub__ expects an argument other than None")
        if not self.write_changes():
            LOG.error("Disk contents are newer than this config object, changes were not written.")


def _get_legacy_config_dir(sys_path: Optional[list] = None) -> Optional[str]:
    """
    Get legacy configuration locations based on install directories
    :param sys_path: Optional list to override `sys.path`
    :return: path to save config to if one is found, else None
    """
    sys_path = sys_path or sys.path
    for p in [path for path in sys_path if sys_path]:
        if re.match(".*/lib/python.*/site-packages", p):
            # Get directory containing virtual environment
            clean_path = "/".join(p.split("/")[0:-4])
        else:
            clean_path = p
        invalid_path_prefixes = re.compile("^/usr|^/lib|.*/lib/python.*")
        valid_path_mapping = (
            (join(clean_path, "NGI"), join(clean_path, "NGI")),
            (join(clean_path, "neon_core"), clean_path),
            (join(clean_path, "mycroft"), clean_path),
            (join(clean_path, ".venv"), clean_path)
        )
        if re.match(invalid_path_prefixes, clean_path):
            # Exclude system paths
            continue
        for (path_to_check, path_to_write) in valid_path_mapping:
            if exists(path_to_check) and path_is_read_writable(path_to_write):
                return path_to_write
    return None


def init_config_dir() -> bool:
    """
    Performs one-time initialization of the configuration directory.
    NOTE: This method is intended to be called once at module init, before any
    configuration is loaded. Repeated calls or calls after configuration is
    loaded may lead to inconsistent behavior.
    :returns: True if configuration was relocated
    """
    env_spec = expanduser(os.getenv("NEON_CONFIG_PATH", ""))
    valid_dir = get_config_dir()
    if env_spec and valid_dir != env_spec:
        with create_lock("init_config"):
            for file in glob(f"{env_spec}/ngi_*.yml"):
                filename = basename(file)
                if not isfile(join(valid_dir, filename)):
                    LOG.info(f"Copying {filename} to {valid_dir}")
                    shutil.copyfile(file, join(valid_dir, filename))
                else:
                    LOG.warning(f"Skipping overwrite of existing file: "
                                f"{basename(file)}")
            os.environ["NEON_CONFIG_PATH"] = valid_dir
            LOG.warning(f"Config files moved and"
                        f" NEON_CONFIG_PATH set to {valid_dir}")
        return True
    if not env_spec:
        LOG.info(f"Set NEON_CONFIG_PATH={valid_dir}")
        os.environ["NEON_CONFIG_PATH"] = valid_dir
    else:
        LOG.debug(f"NEON_CONFIG_PATH={env_spec}")
    return False


def get_config_dir():
    """
    Get a default directory in which to find configuration files,
    creating it if it doesn't exist.
    Returns: Path to configuration or else default
    """
    # Check envvar spec path
    if os.getenv("NEON_CONFIG_PATH"):
        config_path = expanduser(os.getenv("NEON_CONFIG_PATH"))
        if os.path.isdir(config_path) and path_is_read_writable(config_path):
            # LOG.info(f"Got config path from environment vars: {config_path}")
            return config_path
        elif path_is_read_writable(dirname(config_path)) and not os.path.exists(config_path):
            LOG.info(f"Creating requested config path: {config_path}")
            os.makedirs(config_path)
            return config_path
        else:
            LOG.warning(f"NEON_CONFIG_PATH is not valid and will be ignored: "
                        f"{config_path}")

    # TODO: Update modules to set NEON_CONFIG_PATH and log a deprecation warning here DM
    # Check for legacy path spec
    legacy_path = _get_legacy_config_dir()
    if legacy_path:
        if not isdir(legacy_path):
            os.makedirs(legacy_path)
        # LOG.warning(f"Legacy Config Path Found: {legacy_path}")
        return legacy_path

    default_path = expanduser("~/.local/share/neon")
    if not isdir(default_path):
        os.makedirs(default_path)
    # LOG.info(f"System packaged core found! Using default configuration at {default_path}")
    return default_path


def delete_recursive_dictionary_keys(dct_to_change: MutableMapping, list_of_keys_to_remove: list) -> MutableMapping:
    """
    Removes the specified keys from the specified dict.
    Args:
        dct_to_change: Dictionary to modify
        list_of_keys_to_remove: List of keys to remove

    Returns: dct_to_change with any specified keys removed

    """
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(list_of_keys_to_remove, list):
        raise AttributeError("delete_recursive_dictionary_keys expects a dict and a list as args")

    for key in list_of_keys_to_remove:
        with suppress(KeyError):
            del dct_to_change[key]
    for value in list(dct_to_change.values()):
        if isinstance(value, MutableMapping):
            delete_recursive_dictionary_keys(value, list_of_keys_to_remove)
    return dct_to_change


def dict_merge(dct_to_change: MutableMapping, merge_dct: MutableMapping) -> MutableMapping:
    """
    Recursively merges two configuration dictionaries and returns the combined object. All keys are returned with values
    from merge_dct overwriting those from dct_to_change.
    Args:
        dct_to_change: dict to append keys and values to
        merge_dct: dict with keys and new values to add to dct_to_change
    Returns: dict of merged preferences
    """
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(merge_dct, MutableMapping):
        raise AttributeError("merge_recursive_dicts expects two dict objects as args")
    for key, value in merge_dct.items():
        if isinstance(dct_to_change.get(key), dict) and isinstance(value, MutableMapping):
            dct_to_change[key] = dict_merge(dct_to_change[key], value)
        else:
            dct_to_change[key] = value
    return dct_to_change


def dict_make_equal_keys(dct_to_change: MutableMapping, keys_dct: MutableMapping,
                         max_depth: int = 1, cur_depth: int = 0) -> MutableMapping:
    """
    Adds and removes keys from dct_to_change such that it has the same keys as keys_dct. Values from dct_to_change are
    preserved with any added keys using default values from keys_dct.
    Args:
        dct_to_change: Dict of user preferences to modify and return
        keys_dct: Dict containing all keys and default values
        max_depth: Int depth to recurse (0-indexed)
        cur_depth: Current depth relative to top-level config (0-indexed)
    Returns: dct_to_change with any keys not in keys_dct removed and any new keys added with default values

    """
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(keys_dct, MutableMapping):
        raise AttributeError("merge_recursive_dicts expects two dict objects as args")
    if not keys_dct:
        raise ValueError("Empty keys_dct provided, not modifying anything.")
    for key in list(dct_to_change.keys()):
        if isinstance(keys_dct.get(key), dict) and isinstance(dct_to_change[key], MutableMapping):
            if max_depth > cur_depth:
                if key in ("tts", "stt", "hotwords", "language"):
                    dct_to_change[key] = dict_update_keys(dct_to_change[key], keys_dct[key])
                else:
                    dct_to_change[key] = dict_make_equal_keys(dct_to_change[key], keys_dct[key],
                                                              max_depth, cur_depth + 1)
        elif key not in keys_dct.keys():
            dct_to_change.pop(key)
            LOG.warning(f"Removing '{key}' from dict!")
            # del dct_to_change[key]
    for key, value in keys_dct.items():
        if key not in dct_to_change.keys():
            dct_to_change[key] = value
    return dct_to_change


def dict_update_keys(dct_to_change: MutableMapping, keys_dct: MutableMapping) -> MutableMapping:
    """
    Adds keys to dct_to_change such that all keys in keys_dict exist in dict_to_change. Added keys use default values
    from keys_dict
    Args:
        dct_to_change: Dict of user preferences to modify and return
        keys_dct: Dict containing potentially new keys and default values

    Returns: dct_to_change with any new keys in keys_dict added with default values

    """
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(keys_dct, MutableMapping):
        raise AttributeError("merge_recursive_dicts expects two dict objects as args")
    for key, value in list(keys_dct.items()):
        if isinstance(keys_dct.get(key), dict) and isinstance(value, MutableMapping):
            dct_to_change[key] = dict_update_keys(dct_to_change.get(key, {}), keys_dct[key])
        else:
            if key not in dct_to_change.keys():
                dct_to_change[key] = value
    return dct_to_change


def write_to_json(preference_dict: MutableMapping, output_path: str):
    """
    Writes the specified dictionary to a json file
    Args:
        preference_dict: Dict to write to JSON
        output_path: Output file to write
    """
    if not os.path.exists(output_path):
        create_file(output_path)
    # with NamedLock(output_path): TODO: Implement combo_lock with file lock support or add lock utils to neon_utils DM
    with open(output_path, "w") as out:
        json.dump(preference_dict, out, indent=4)


def get_neon_lang_config() -> dict:
    """
    Get a language config for language utilities
    Returns:
        dict of config params used by Language Detector and Translator modules
    """
    lang_config = deepcopy(get_neon_local_config().content.get("language", {}))
    # TODO: Make sure lang_config is valid here!
    user_lang_config = deepcopy(get_neon_user_config().content.get("speech", {}))
    lang_config["internal"] = lang_config.get("core_lang", "en-us")
    lang_config["user"] = user_lang_config.get("stt_language", "en-us")
    lang_config["boost"] = lang_config.get("boost", False)
    merged_language = {**_safe_mycroft_config().get("language", {}), **lang_config}
    if merged_language.keys() != lang_config.keys():
        LOG.warning(f"Keys missing from Neon config! {merged_language.keys()}")

    return merged_language


def get_neon_cli_config() -> dict:
    """
    Get a configuration dict for the neon_cli
    Returns:
        dict of config params used by the neon_cli
    """
    local_config = NGIConfig("ngi_local_conf").content
    wake_words_enabled = local_config.get("interface", {}).get("wake_word_enabled", True)
    try:
        neon_core_version = os.path.basename(glob(local_config['dirVars']['ngiDir'] +
                                                  '/*.release')[0]).split('.release')[0]
    except Exception as e:
        LOG.error(e)
        neon_core_version = "Unknown"
    log_dir = local_config.get("dirVars", {}).get("logsDir", "/var/log/mycroft")
    return {"neon_core_version": neon_core_version,
            "wake_words_enabled": wake_words_enabled,
            "log_dir": log_dir}


def get_neon_tts_config() -> dict:
    """
    Get a configuration dict for TTS
    Returns:
    dict of TTS-related configuration
    """
    return get_neon_local_config()["tts"]


def get_neon_speech_config() -> dict:
    """
    Get a configuration dict for listener. Merge any values from Mycroft config if missing from Neon.
    Returns:
        dict of config params used for listener in neon_speech
    """
    mycroft = _safe_mycroft_config()
    local_config = get_neon_local_config()

    neon_listener_config = deepcopy(local_config.get("listener", {}))
    neon_listener_config["wake_word_enabled"] = local_config["interface"].get("wake_word_enabled", True)
    neon_listener_config["save_utterances"] = local_config["prefFlags"].get("saveAudio", False)
    neon_listener_config["confirm_listening"] = local_config["interface"].get("confirm_listening", True)
    neon_listener_config["record_utterances"] = neon_listener_config["save_utterances"]
    neon_listener_config["record_wake_words"] = neon_listener_config["save_utterances"]
    merged_listener = {**mycroft.get("listener", {}), **neon_listener_config}
    if merged_listener.keys() != neon_listener_config.keys():
        LOG.warning(f"Keys missing from Neon config! {merged_listener.keys()}")

    lang = mycroft.get("language", {}).get("internal", "en-us")  # core_lang

    neon_stt_config = local_config.get("stt", {})
    merged_stt_config = {**mycroft.get("stt", {}), **neon_stt_config}
    # stt keys will vary by installed/configured plugins
    # if merged_stt_config.keys() != neon_stt_config.keys():
    #     LOG.warning(f"Keys missing from Neon config! {merged_stt_config.keys()}")

    hotword_config = local_config.get("hotwords") or mycroft.get("hotwords")
    if hotword_config != local_config.get("hotwords"):
        LOG.warning(f"Neon hotword config missing! {hotword_config}")

    neon_audio_parser_config = local_config.get("audio_parsers", {})
    merged_audio_parser_config = {**mycroft.get("audio_parsers", {}), **neon_audio_parser_config}
    if merged_audio_parser_config.keys() != neon_audio_parser_config.keys():
        LOG.warning(f"Keys missing from Neon config! {merged_audio_parser_config.keys()}")

    return {"listener": merged_listener,
            "hotwords": hotword_config,
            "audio_parsers": merged_audio_parser_config,
            "lang": lang,
            "stt": merged_stt_config,
            "metric_upload": local_config["prefFlags"].get("metrics", False),
            "remote_server": local_config.get("remoteVars", {}).get("remoteHost", "64.34.186.120"),
            "data_dir": os.path.expanduser(local_config.get("dirVars", {}).get("rootDir") or "~/.local/share/neon"),
            "keys": {}  # TODO: Read from somewhere DM
            }


def get_neon_bus_config() -> dict:
    """
    Get a configuration dict for the messagebus. Merge any values from Mycroft config if missing from Neon.
    Returns:
        dict of config params used for a messagebus client
    """
    mycroft = _safe_mycroft_config().get("websocket", {})
    neon = get_neon_local_config().get("websocket", {})
    merged = {**mycroft, **neon}
    if merged.keys() != neon.keys():
        LOG.warning(f"Keys missing from Neon config! {merged.keys()}")
    return merged


def get_neon_audio_config() -> dict:
    """
    Get a configuration dict for the audio module. Merge any values from Mycroft config if missing from Neon.
    Returns:
        dict of config params used for the Audio module
    """
    mycroft = _safe_mycroft_config()
    local_config = get_neon_local_config()
    neon_audio = local_config.get("audioService", {})
    merged_audio = {**mycroft.get("Audio", {}), **neon_audio}
    # tts keys will vary by installed/configured plugins
    # if merged_audio.keys() != neon_audio.keys():
    #     LOG.warning(f"Keys missing from Neon config! {merged_audio.keys()}")

    return {"Audio": merged_audio,
            "tts": get_neon_tts_config(),
            "language": get_neon_lang_config()}


def get_neon_api_config() -> dict:
    """
    Get a configuration dict for the api module. Merge any values from Mycroft config if missing from Neon.
    Returns:
        dict of config params used for the Mycroft API module
    """
    core_config = get_neon_local_config()
    api_config = deepcopy(core_config.get("api"))
    api_config["metrics"] = core_config["prefFlags"].get("metrics", False)
    mycroft = _safe_mycroft_config().get("server", {})
    merged = {**mycroft, **api_config}
    if merged.keys() != api_config.keys():
        LOG.warning(f"Keys missing from Neon config! {merged.keys()}")
    return merged


def get_neon_skills_config() -> dict:
    """
    Get a configuration dict for the skills module. Merge any values from Mycroft config if missing from Neon.
    Returns:
        dict of config params used for the Mycroft Skills module
    """
    core_config = get_neon_local_config()
    mycroft_config = _safe_mycroft_config()
    neon_skills = deepcopy(core_config.get("skills", {}))
    neon_skills["directory"] = os.path.expanduser(core_config["dirVars"].get("skillsDir"))

    try:
        ovos_core_version = get_package_version_spec("ovos-core")
        if ovos_core_version.startswith("0.0.1"):
            # ovos-core 0.0.1 uses directory_override param
            LOG.debug("Adding `directory_override` setting for ovos-core")
            neon_skills["directory_override"] = neon_skills["directory"]
    except ModuleNotFoundError:
        LOG.warning("ovos-core not installed")
        neon_skills["directory_override"] = neon_skills["directory"]

    neon_skills["disable_osm"] = neon_skills["skill_manager"] != "osm"
    neon_skills["priority_skills"] = neon_skills["priority"]
    neon_skills["blacklisted_skills"] = neon_skills["blacklist"]

    if not isinstance(neon_skills["auto_update_interval"], float):
        try:
            neon_skills["auto_update_interval"] = float(neon_skills["auto_update_interval"])
        except Exception as e:
            LOG.error(e)
            neon_skills["auto_update_interval"] = 24.0
    if not isinstance(neon_skills["appstore_sync_interval"], float):
        try:
            neon_skills["appstore_sync_interval"] = float(neon_skills["appstore_sync_interval"])
        except Exception as e:
            LOG.error(e)
            neon_skills["appstore_sync_interval"] = 6.0
    neon_skills["update_interval"] = neon_skills["auto_update_interval"]  # Backwards Compat.
    if not neon_skills["neon_token"]:
        try:
            neon_skills["neon_token"] = find_neon_git_token()  # TODO: GetPrivateKeys
            populate_github_token_config(neon_skills["neon_token"])
        except FileNotFoundError:
            LOG.debug(f"No Github token found; skills may fail to install")
    skills_config = {**mycroft_config.get("skills", {}), **neon_skills}
    return skills_config


def get_neon_client_config() -> dict:
    """
    Get a configuration dict for the client module.
    Returns:
        dict of config params used for the Neon client module
    """
    LOG.warning(f"The Neon client module has been deprecated. This method will be removed")
    # TODO: Remove in v1.0.0
    core_config = get_neon_local_config()
    server_addr = core_config.get("remoteVars", {}).get("remoteHost", "167.172.112.7")
    if server_addr == "64.34.186.92":
        LOG.warning(f"Depreciated call to host: {server_addr}")
        server_addr = "167.172.112.7"
    return {"server_addr": server_addr,
            "devVars": core_config["devVars"],
            "remoteVars": core_config["remoteVars"]}


def get_neon_transcribe_config() -> dict:
    """
    Get a configuration dict for the transcription module.
    Returns:
        dict of config params used for the Neon transcription module
    """
    local_config = get_neon_local_config()
    user_config = get_neon_user_config()
    neon_transcribe_config = dict()
    neon_transcribe_config["transcript_dir"] = local_config["dirVars"].get("docsDir", "")
    neon_transcribe_config["audio_permission"] = user_config["privacy"].get("save_audio", False)
    return neon_transcribe_config


def get_neon_gui_config() -> dict:
    """
    Get a configuration dict for the gui module.
    Returns:
        dict of config params used for the Neon gui module
    """
    local_config = get_neon_local_config()
    gui_config = dict(local_config["gui"])
    gui_config["base_port"] = gui_config["port"]
    return gui_config


def _move_config_sections(user_config, local_config):
    """
    Temporary method to handle one-time migration of user_config params to local_config
    Args:
        user_config (NGIConfig): user configuration object
        local_config (NGIConfig): local configuration object
    """
    depreciated_user_configs = ("interface", "listener", "skills", "session", "tts", "stt", "logs", "device")
    try:
        if any([d in user_config.content for d in depreciated_user_configs]):
            LOG.warning("Depreciated keys found in user config! Adding them to local config")
            if "wake_words_enabled" in user_config.content.get("interface", dict()):
                user_config["interface"]["wake_word_enabled"] = user_config["interface"].pop("wake_words_enabled")
            config_to_move = {"interface": user_config.content.pop("interface", {}),
                              "listener": user_config.content.pop("listener", {}),
                              "skills": user_config.content.pop("skills", {}),
                              "session": user_config.content.pop("session", {}),
                              "tts": user_config.content.pop("tts", {}),
                              "stt": user_config.content.pop("stt", {}),
                              "logs": user_config.content.pop("logs", {}),
                              "device": user_config.content.pop("device", {})}
            local_config.update_keys(config_to_move)

        if not local_config.get("language"):
            local_config["language"] = dict()
        if local_config.get("stt", {}).get("detection_module"):
            local_config["language"]["detection_module"] = local_config["stt"].pop("detection_module")
        if local_config.get("stt", {}).get("translation_module"):
            local_config["language"]["translation_module"] = local_config["stt"].pop("translation_module")
    except (KeyError, RuntimeError):
        # If some other instance moves these values, just pass
        pass


def _safe_mycroft_config() -> dict:
    """
    Safe reference to mycroft config that always returns a dict
    Returns:
        dict mycroft configuration
    """
    try:
        mycroft = read_mycroft_config()
    except FileNotFoundError:
        mycroft = LocalConf(os.path.join(os.path.dirname(__file__), "default_configurations", "mycroft.conf"))
    return dict(mycroft)


def get_neon_user_config(path: Optional[str] = None) -> NGIConfig:
    """
    Returns a dict user configuration and handles any migration of configuration values to local config from user config
    Args:
        path: optional path to yml configuration files
    Returns:
        NGIConfig object with user config
    """
    try:
        user_config = NGIConfig("ngi_user_info", path)
    except PermissionError:
        LOG.error(f"Insufficient Permissions for path: {path}")
        user_config = NGIConfig("ngi_user_info")
    _populate_read_only_config(path, basename(user_config.file_path), user_config)
    default_user_config = NGIConfig("default_user_conf",
                                    os.path.join(os.path.dirname(__file__), "default_configurations"))
    if len(user_config.content) == 0:
        LOG.info("Created Empty User Config!")
        user_config.populate(default_user_config.content)
        # TODO: Update from Mycroft config DM

    if isfile(join(path or get_config_dir(), "ngi_local_conf.yml")):
        local_config = NGIConfig("ngi_local_conf", path)
        _move_config_sections(user_config, local_config)

    user_config.make_equal_by_keys(default_user_config.content)
    # LOG.info(f"Loaded user config from {user_config.file_path}")
    return user_config


def get_neon_local_config(path: Optional[str] = None) -> NGIConfig:
    """
    Returns a dict local configuration and handles any
     migration of configuration values to local config from user config
    Args:
        path: optional path to yml configuration files
    Returns:
        NGIConfig object with local config
    """
    try:
        local_config = NGIConfig("ngi_local_conf", path)
    except PermissionError:
        LOG.error(f"Insufficient Permissions for path: {path}")
        local_config = NGIConfig("ngi_local_conf")
    _populate_read_only_config(path, basename(local_config.file_path), local_config)
    default_local_config = NGIConfig("default_core_conf",
                                     os.path.join(os.path.dirname(__file__), "default_configurations"))
    if len(local_config.content) == 0:
        LOG.info(f"Created Empty Local Config at {local_config.path}")
        local_config.populate(default_local_config.content)
        # TODO: Update from Mycroft config DM

    if isfile(join(path or get_config_dir(), "ngi_user_info.yml")):
        user_config = NGIConfig("ngi_user_info", path)
        _move_config_sections(user_config, local_config)

    local_config.make_equal_by_keys(default_local_config.content)
    # LOG.info(f"Loaded local config from {local_config.file_path}")
    return local_config


def get_neon_auth_config(path: Optional[str] = None) -> NGIConfig:
    """
    Returns a dict authentication configuration and handles populating values from key files
    Args:
        path: optional path to yml configuration files
    Returns:
        NGIConfig object with authentication config
    """
    try:
        auth_config = NGIConfig("ngi_auth_vars", path)
    except PermissionError:
        LOG.error(f"Insufficient Permissions for path: {path}")
        auth_config = NGIConfig("ngi_auth_vars")
    _populate_read_only_config(path, basename(auth_config.file_path), auth_config)
    if not auth_config.content:
        LOG.info("Populating empty auth configuration")
        auth_config._content = build_new_auth_config(path)
        auth_config.write_changes()

    if not auth_config.content:
        LOG.info("Empty auth_config generated, adding 'created' key to prevent regeneration attempts")
        auth_config._content = {"_loaded": True}
        auth_config.write_changes()

    # LOG.info(f"Loaded auth config from {auth_config.file_path}")
    return auth_config


def _populate_read_only_config(path: Optional[str], config_filename: str,
                               loaded_config: NGIConfig) -> bool:
    """
    Check if a requested config file wasn't loaded due to insufficient write
    permissions and duplicate its contents into the loaded config object.
    :param path: Optional requested RO config path
    :param config_filename: basename of the requested and loaded config file
    :param loaded_config: Loaded config object to populate with RO config
    :return: True if RO config was copied to new location, else False
    """
    # Handle reading unwritable config contents into new empty config
    requested_file = os.path.abspath(join(path or expanduser(os.getenv("NEON_CONFIG_PATH", "")), config_filename))
    if os.path.isfile(requested_file) and \
            loaded_config.file_path != requested_file and \
            loaded_config.content == dict():
        LOG.warning(f"Loading requested file contents ({requested_file}) into {loaded_config.file_path}")
        with loaded_config.lock:
            shutil.copy(requested_file, loaded_config.file_path)
        loaded_config.check_for_updates()
        return True
    return False


def get_neon_device_type() -> str:
    """
    Returns device type (server, pi, other)
    Returns:
        str device type
    """
    import platform
    import importlib.util
    local_config = get_neon_local_config()
    config_dev = local_config["devVars"].get("devType", "")
    if "pi" in config_dev:
        return "pi"
    if config_dev == "server":
        return "server"
    if config_dev != "generic":
        return config_dev
    if "arm" in platform.machine():
        return "pi"
    if importlib.util.find_spec("neon-core-client"):
        return "desktop"
    if importlib.util.find_spec("neon-core-server"):
        return "server"
    return "desktop"


def is_neon_core() -> bool:
    """
    Checks for neon-specific packages to determine if this is a Neon Core or a Mycroft Core
    Returns:
        True if core is Neon, else False
    """
    import importlib.util
    if importlib.util.find_spec("neon_core"):
        return True
    if importlib.util.find_spec("neon_core_client"):
        LOG.info("Found neon_core_client; assuming neon_core")
        return True
    if importlib.util.find_spec("neon_core_server"):
        LOG.info("Found neon_core_server; assuming neon_core")
        return True
    return False


def get_mycroft_compatible_location(location: dict) -> dict:
    """
    Translates a user config location to a Mycroft-compatible config dict
    :param location: dict location parsed from user config
    :returns: dict formatted to match mycroft.conf spec
    """
    parsed_location = get_full_location((location['lat'], location['lng']))
    location = {
        "city": {
            "code": location["city"],
            "name": location["city"],
            "state": {
                "code": location["state"],  # TODO: Util to parse this
                "name": location["state"],
                "country": {
                    "code": parsed_location["address"]["country_code"],
                    "name": location["country"]
                }
            }
        },
        "coordinate": {
            "latitude": float(location["lat"]),
            "longitude": float(location["lng"])
        },
        "timezone": {
            "code": location["tz"],
            "name": location["tz"],  # TODO: Util to parse this
            "offset": float(location["utc"]) * 3600000,
            "dstOffset": 3600000
        }
    }
    return location


def get_mycroft_compatible_config(mycroft_only=False) -> dict:
    """
    Get a configuration compatible with mycroft.conf/ovos.conf
    NOTE: This method should only be called at startup to write a .conf file
    :param mycroft_only: if True, ignore Neon configuration files
    :returns: dict config compatible with mycroft.conf structure
    """
    default_config = _safe_mycroft_config()
    if mycroft_only or not is_neon_core():
        return default_config
    speech = get_neon_speech_config()
    user = get_neon_user_config()
    local = get_neon_local_config()

    default_config["lang"] = "en-us"
    default_config["system_unit"] = user["units"]["measure"]
    default_config["time_format"] = \
        "half" if user["units"]["time"] == 12 else "full"
    default_config["date_format"] = user["units"]["date"]
    default_config["opt_in"] = local["prefFlags"]["metrics"]
    default_config["confirm_listening"] = \
        local["interface"]["confirm_listening"]
    default_config["sounds"] = {**default_config.get("sounds", {}),
                                **local.get("sounds", {})}

    # default_config["play_wav_cmdline"]
    # default_config["play_mp3_cmdline"]
    # default_config["play_ogg_cmdline"]

    default_config["location"] = \
        get_mycroft_compatible_location(user["location"])

    default_config["data_dir"] = local["dirVars"]["rootDir"]
    default_config["cache_path"] = local["dirVars"]["cacheDir"]
    # default_config["ready_settings"]
    default_config["skills"] = get_neon_skills_config()
    # default_config["converse"]
    # default_config["system"]
    default_config["server"] = get_neon_api_config()
    default_config["websocket"] = get_neon_bus_config()
    default_config["gui_websocket"] = {**default_config.get("gui_websocket",
                                                            {}),
                                       **local["gui"]}
    default_config["gui_websocket"]["base_port"] = \
        default_config["gui_websocket"].get("base_port") or \
        default_config["gui_websocket"].get("port")

    # default_config["network_tests"]
    default_config["listener"] = speech["listener"]
    # default_config["precise"]
    default_config["hotwords"] = speech["hotwords"]
    # default_config["enclosure"]
    default_config["log_level"] = local["logs"]["log_level"]
    # default_config["ignore_logs"]
    default_config["session"] = local["session"]
    default_config["stt"] = speech["stt"]
    default_config["tts"] = local["tts"]
    default_config["padatious"] = {**default_config.get("padatious", {}),
                                   **local["padatious"]}
    default_config["Audio"] = get_neon_audio_config()["Audio"]
    default_config["debug"] = local["prefFlags"]["devMode"]

    default_config["language"] = get_neon_lang_config()
    default_config["keys"] = get_neon_auth_config().content
    default_config["text_parsers"] = {**default_config.get("text_parsers",
                                                           {}),
                                      **local.get("text_parsers", {})}
    default_config["audio_parsers"] = speech["audio_parsers"]
    default_config["disable_xdg"] = False
    default_config["ipc_path"] = local["dirVars"]["ipcDir"]
    default_config["remote-server"] = local["gui"]["file_server"]
    # default_config["Display"]

    return default_config


def write_mycroft_compatible_config(file_to_write: str = None) -> str:
    """
    Generates a mycroft-like configuration and writes it to the specified file
    NOTE: This is potentially destructive and will overwrite existing config
    :param file_to_write: config file to write out
    :return: path to written config file
    """
    file_to_write = file_to_write or "~/.mycroft/mycroft.conf"
    configuration = get_mycroft_compatible_config()
    file_path = os.path.expanduser(file_to_write)

    if isfile(file_path):
        with open(file_path, 'r') as f:
            disk_config = json.load(f)
        if disk_config == configuration:
            LOG.debug(f"Configuration already up to date")
            return file_path
        LOG.warning(f"File exists and will be overwritten: {file_to_write}")
    elif not isdir(dirname(file_path)):
        os.makedirs(dirname(file_path))

    with create_lock(file_path):
        with open(file_path, 'w') as f:
            json.dump(configuration, f, indent=4)
    return file_path


def create_config_from_setup_params(path=None) -> NGIConfig:
    """
    Populate a (probably) new local config with parameters gathered during setup
    Args:
        path: Optional config path
    Returns:
        NGIConfig object generated from environment vars
    """
    local_conf = get_neon_local_config(path)
    pref_flags = local_conf["prefFlags"]
    local_conf["prefFlags"]["devMode"] = \
        os.environ.get("devMode",
                       str(pref_flags["devMode"])).lower() == "true"
    local_conf["prefFlags"]["autoStart"] = \
        os.environ.get("autoStart",
                       str(pref_flags["autoStart"])).lower() == "true"
    local_conf["prefFlags"]["autoUpdate"] = \
        os.environ.get("autoUpdate",
                       str(pref_flags["autoUpdate"])).lower() == "true"
    local_conf["skills"]["auto_update"] = local_conf["prefFlags"]["autoUpdate"]
    local_conf["skills"]["neon_token"] = os.environ.get("GITHUB_TOKEN")
    local_conf["tts"]["module"] = os.environ.get("ttsModule",
                                                 local_conf["tts"]["module"])
    local_conf["stt"]["module"] = os.environ.get("sttModule",
                                                 local_conf["stt"]["module"])
    local_conf["language"]["translation_module"] = \
        os.environ.get("translateModule",
                       local_conf["language"]["translation_module"])
    local_conf["language"]["detection_module"] = \
        os.environ.get("detectionModule",
                       local_conf["language"]["detection_module"])

    if os.environ.get("installServer", "false") == "true":
        local_conf["devVars"]["devType"] = "server"
    elif os.environ.get("devType"):
        local_conf["devVars"]["devType"] = os.environ.get("devType")
    else:
        import platform
        local_conf["devVars"]["devType"] = platform.system().lower()

    local_conf["devVars"]["devName"] = os.environ.get("devName")

    if local_conf["prefFlags"]["devMode"]:
        root_path = os.environ.get("installerDir", local_conf.path)
        local_conf["dirVars"]["skillsDir"] = os.path.join(root_path, "skills")
        local_conf["dirVars"]["diagsDir"] = os.path.join(root_path, "Diagnostics")
        local_conf["dirVars"]["logsDir"] = os.path.join(root_path, "logs")
        local_conf["skills"]["default_skills"] = \
            "https://raw.githubusercontent.com/NeonGeckoCom/neon_skills/master/skill_lists/DEFAULT-SKILLS-DEV"
    else:
        local_conf["dirVars"]["logsDir"] = "~/.local/share/neon/logs"

    if os.environ.get("skillRepo"):
        local_conf["skills"]["default_skills"] = os.environ.get("skillRepo")

    # TODO: Use XDG here DM
    if not local_conf.write_changes():
        LOG.error("Disk contents are newer than this config object, changes were not written.")
    return local_conf


def parse_skill_default_settings(settings_meta: dict) -> dict:
    """
    Parses default skill settings from settingsmeta file contents
    :param settings_meta: parsed contents of settingsmeta.yml or settingsmeta.json
    :return: parsed dict of default settings keys/values
    """
    if not isinstance(settings_meta, dict):
        LOG.error(settings_meta)
        raise TypeError(f"Expected a dict, got: {type(settings_meta)}")
    if not settings_meta:
        LOG.debug(f"Empty Settings")
        return dict()
    else:
        settings = dict()
        try:
            for settings_group in settings_meta.get("skillMetadata", dict()).get("sections", list()):
                for field in settings_group.get("fields", list()):
                    settings = {**settings, **{field.get("name"): field.get("value")}}
            return settings
        except Exception as e:
            LOG.error(e)
            raise e
