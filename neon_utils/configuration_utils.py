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

import logging
import re
import json
import os
import sys
import shutil
import sysconfig

from copy import deepcopy
from os.path import *
from collections.abc import MutableMapping
from contextlib import suppress
from glob import glob
from ovos_utils.json_helper import load_commented_json
from ovos_utils.configuration import read_mycroft_config, LocalConf
from ruamel.yaml import YAML
from typing import Optional
from neon_utils import LOG
from neon_utils.authentication_utils import find_neon_git_token, populate_github_token_config, build_new_auth_config
from neon_utils.lock_utils import create_master_lock


class NGIConfig:
    configuration_list = dict()
    # configuration_locks = dict()

    def __init__(self, name, path=None, force_reload: bool = False):
        self.name = name
        self.path = path or get_config_dir()
        self.parser = YAML()
        lock_filename = join(self.path, f".{self.name}.lock")
        self.lock = create_master_lock(lock_filename)
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
            create_file(file_path)
            LOG.debug(f"New YAML created: {file_path}")
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


def get_config_dir():
    """
    Get a default directory in which to find configuration files
    Returns: Path to configuration or else default
    """
    if os.getenv("NEON_CONFIG_PATH"):
        config_path = expanduser(os.getenv("NEON_CONFIG_PATH"))
        if os.path.isdir(config_path):
            # LOG.info(f"Got config path from environment vars: {config_path}")
            return config_path
        else:
            LOG.error(f"NEON_CONFIG_PATH is not valid and will be ignored: {config_path}")
    site = sysconfig.get_paths()['platlib']
    if exists(join(site, 'NGI')):
        return join(site, "NGI")
    for p in [path for path in sys.path if path != ""]:
        if exists(join(p, "NGI")):
            return join(p, "NGI")
        if re.match(".*/lib/python.*/site-packages", p):
            clean_path = "/".join(p.split("/")[0:-4])
            if clean_path.startswith("/usr") or clean_path.startswith("/lib"):
                # Exclude system paths
                continue
            if exists(join(clean_path, "NGI")):
                LOG.warning(f"Depreciated core structure found at {clean_path}")
                return join(clean_path, "NGI")
            elif exists(join(clean_path, "neon_core")):
                # Cloned Dev Environment
                return clean_path
            elif exists(join(clean_path, "NeonCore", "neon_core")):
                # Installed Dev Environment
                return join(clean_path, "NeonCore")
            elif exists(join(clean_path, "mycroft")):
                LOG.info(f"Mycroft core structure found at {clean_path}")
                return clean_path
            elif exists(join(clean_path, ".venv")):
                # Localized Production Environment (Servers)
                return clean_path
    default_path = expanduser("~/.local/share/neon")
    # LOG.info(f"System packaged core found! Using default configuration at {default_path}")
    return default_path


def create_file(filename):
    """ Create the file filename and create any directories needed

        Args:
            filename: Path to the file to be created
    """
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    except OSError:
        pass
    # with NamedLock(filename): # TODO: Implement combo_lock with file lock support or add lock utils to neon_utils DM
    with open(filename, 'w') as f:
        f.write('')


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
    neon_skills["directory_override"] = neon_skills["directory"]
    neon_skills["disable_osm"] = neon_skills["skill_manager"] != "osm"
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
            LOG.warning(f"No Github token found; skills may fail to install!")
    skills_config = {**mycroft_config.get("skills", {}), **neon_skills}
    return skills_config


def get_neon_client_config() -> dict:
    core_config = get_neon_local_config()
    server_addr = core_config.get("remoteVars", {}).get("remoteHost", "167.172.112.7")
    if server_addr == "64.34.186.92":
        LOG.warning(f"Depreciated call to host: {server_addr}")
        server_addr = "167.172.112.7"
    return {"server_addr": server_addr,
            "devVars": core_config["devVars"],
            "remoteVars": core_config["remoteVars"]}


def get_neon_transcribe_config() -> dict:
    local_config = get_neon_local_config()
    user_config = get_neon_user_config()
    neon_transcribe_config = dict()
    neon_transcribe_config["transcript_dir"] = local_config["dirVars"].get("docsDir", "")
    neon_transcribe_config["audio_permission"] = user_config["privacy"].get("save_audio", False)
    return neon_transcribe_config


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
    return mycroft


def get_neon_user_config(path: Optional[str] = None) -> NGIConfig:
    """
    Returns a dict user configuration and handles any migration of configuration values to local config from user config
    Args:
        path: optional path to yml configuration files
    Returns:
        NGIConfig object with user config
    """
    user_config = NGIConfig("ngi_user_info", path)
    default_user_config = NGIConfig("default_user_conf",
                                    os.path.join(os.path.dirname(__file__), "default_configurations"))
    if len(user_config.content) == 0:
        LOG.info("Created Empty User Config!")
        user_config.populate(default_user_config.content)
    local_config = NGIConfig("ngi_local_conf", path)
    _move_config_sections(user_config, local_config)
    user_config.make_equal_by_keys(default_user_config.content)
    LOG.info(f"Loaded user config from {user_config.file_path}")
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
    local_config = NGIConfig("ngi_local_conf", path)
    default_local_config = NGIConfig("default_core_conf",
                                     os.path.join(os.path.dirname(__file__), "default_configurations"))
    if len(local_config.content) == 0:
        LOG.info(f"Created Empty Local Config at {local_config.path}")
        local_config.populate(default_local_config.content)
        # TODO: Update from Mycroft config DM
    user_config = NGIConfig("ngi_user_info", path)
    _move_config_sections(user_config, local_config)
    local_config.make_equal_by_keys(default_local_config.content)
    LOG.info(f"Loaded local config from {local_config.file_path}")
    return local_config


def get_neon_auth_config(path: Optional[str] = None) -> NGIConfig:
    """
    Returns a dict authentication configuration and handles populating values from key files
    Args:
        path: optional path to yml configuration files
    Returns:
        NGIConfig object with authentication config
    """
    auth_config = NGIConfig("ngi_auth_vars", path)
    if not auth_config.content:
        LOG.info("Populating empty auth configuration")
        auth_config._content = build_new_auth_config(path)
        auth_config.write_changes()

    if not auth_config.content:
        LOG.info("Empty auth_config generated, adding 'created' key to prevent regeneration attempts")
        auth_config._content = {"_loaded": True}
        auth_config.write_changes()

    LOG.info(f"Loaded auth config from {auth_config.file_path}")
    return auth_config


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


def get_mycroft_compatible_config(mycroft_only=False):
    # TODO: This is kinda slow, should probably be depreciated DM
    default_config = _safe_mycroft_config()
    if mycroft_only or not is_neon_core():
        return default_config
    speech = get_neon_speech_config()
    user = get_neon_user_config()
    local = get_neon_local_config()

    default_config["lang"] = "en-us"
    default_config["language"] = get_neon_lang_config()
    default_config["keys"] = get_neon_auth_config().content
    # default_config["text_parsers"]  TODO
    default_config["audio_parsers"] = speech["audio_parsers"]
    default_config["system_unit"] = user["units"]["measure"]
    default_config["time_format"] = "half" if user["units"]["time"] == 12 else "full"
    default_config["date_format"] = user["units"]["date"]
    default_config["opt_in"] = local["prefFlags"]["metrics"]
    default_config["confirm_listening"] = local["interface"]["confirm_listening"]
    default_config["sounds"] = {**default_config.get("sounds", {}), **local.get("sounds", {})}
    default_config["data_dir"] = local["dirVars"]["rootDir"]
    default_config["skills"] = get_neon_skills_config()
    default_config["server"] = get_neon_api_config()
    default_config["websocket"] = get_neon_bus_config()
    default_config["gui_websocket"] = {**default_config.get("gui_websocket", {}), **local["gui"]}
    default_config["gui_websocket"]["base_port"] = \
        default_config["gui_websocket"].get("base_port") or default_config["gui_websocket"].get("port")
    default_config["listener"] = speech["listener"]
    # default_config["precise"]
    default_config["hotwords"] = speech["hotwords"]
    # default_config["ignore_logs"]
    default_config["session"] = local["session"]
    default_config["stt"] = speech["stt"]
    default_config["tts"] = local["tts"]
    default_config["Audio"] = get_neon_audio_config()
    default_config["disable_xdg"] = False
    # TODO: Location config
    # default_config["Display"]

    return default_config


def write_mycroft_compatible_config(file_to_write: str = "~/.mycroft/mycroft.conf") -> str:
    """
    Generates a mycroft-compatible configuration and writes it to the specified file
    :param file_to_write: config file to write out
    :return: path to written config file
    """
    configuration = get_mycroft_compatible_config()
    file_path = os.path.expanduser(file_to_write)
    # with NamedLock(file_path): TODO: Implement combo_lock with file lock support or add lock utils to neon_utils DM
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
    local_conf["prefFlags"]["devMode"] = os.environ.get("devMode", str(pref_flags["devMode"])).lower() == "true"
    local_conf["prefFlags"]["autoStart"] = os.environ.get("autoStart", str(pref_flags["autoStart"])).lower() == "true"
    local_conf["prefFlags"]["autoUpdate"] = os.environ.get("autoUpdate",
                                                           str(pref_flags["autoUpdate"])).lower() == "true"
    local_conf["skills"]["neon_token"] = os.environ.get("GITHUB_TOKEN")
    local_conf["tts"]["module"] = os.environ.get("ttsModule", local_conf["tts"]["module"])
    local_conf["stt"]["module"] = os.environ.get("sttModule", local_conf["stt"]["module"])
    local_conf["language"]["translation_module"] = os.environ.get("translateModule", local_conf["language"]["translation_module"])
    local_conf["language"]["detection_module"] = os.environ.get("detectionModule", local_conf["language"]["detection_module"])

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
            "https://raw.githubusercontent.com/NeonGeckoCom/neon-skills-submodules/dev/.utilities/DEFAULT-SKILLS-DEV"
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
