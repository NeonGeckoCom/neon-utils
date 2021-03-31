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

import json
import os
import sys
import shutil
import sysconfig
from copy import deepcopy
from os.path import *
from collections import MutableMapping
from contextlib import suppress
from filelock import FileLock
from glob import glob
from ovos_utils.json_helper import load_commented_json
from ruamel.yaml import YAML
from neon_utils import LOG


def get_config_dir():
    """
    Get a default directory in which to find configuration files
    Returns: Path to configuration or else default
    """
    site = sysconfig.get_paths()['platlib']
    if exists(join(site, 'NGI')):
        return join(site, "NGI")
    for p in [path for path in sys.path if path != ""]:
        if exists(join(p, "NGI")):
            return join(p, "NGI")
    if exists(expanduser("~/.neon")):
        return expanduser("~/.neon")
    return expanduser("~/")


def create_file(filename):
    """ Create the file filename and create any directories needed

        Args:
            filename: Path to the file to be created
    """
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    except OSError:
        pass
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


def dict_make_equal_keys(dct_to_change: MutableMapping, keys_dct: MutableMapping) -> MutableMapping:
    """
    Adds and removes keys from dct_to_change such that it has the same keys as keys_dct. Values from dct_to_change are
    preserved with any added keys using default values from keys_dct.
    Args:
        dct_to_change: Dict of user preferences to modify and return
        keys_dct: Dict containing all keys and default values
    Returns: dct_to_change with any keys not in keys_dct removed and any new keys added with default values

    """
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(keys_dct, MutableMapping):
        raise AttributeError("merge_recursive_dicts expects two dict objects as args")
    for key in list(dct_to_change.keys()):
        if isinstance(keys_dct.get(key), dict) and isinstance(dct_to_change[key], MutableMapping):
            dct_to_change[key] = dict_make_equal_keys(dct_to_change[key], keys_dct[key])
        elif key not in keys_dct.keys():
            dct_to_change.pop(key)
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
    with open(output_path, "w") as out:
        json.dump(preference_dict, out, indent=4)


def get_lang_config() -> dict:
    """
    Get a language config for language utilities
    Returns:
        dict of config params used by Language Detector and Translator modules
    """
    language_config = NGIConfig("ngi_user_info").content.get("speech", {})
    language_config["internal"] = language_config.get("internal", "en-us")
    language_config["user"] = language_config.get("stt_language", "en-us")
    language_config["boost"] = False
    # TODO: Add these keys to config DM
    # "translation_module"
    # "detection_modile"
    return language_config


def get_neon_cli_config() -> dict:
    """
    Get a configuration dict for the neon_cli
    Returns:
        dict of config params used by the neon_cli
    """
    user_config = NGIConfig("ngi_user_info").content
    local_config = NGIConfig("ngi_local_conf").content
    wake_words_enabled = user_config.get("listener", {}).get("wake_word_enabled", True)
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


def get_neon_speech_config() -> dict:
    """
    Get a configuration dict for listener
    Returns:
        dict of config params used for listener in neon_speech
    """
    local_config = NGIConfig("ngi_local_conf").content
    user_config = NGIConfig("ngi_user_info").content
    listener_config = user_config.get("listener", {})
    lang = "en-us"  # core_lang
    stt_config = user_config.get("stt", {})

    if "sample_rate" not in listener_config:
        listener_config["sample_rate"] = listener_config.get("rate")
    if "wake_word" in listener_config:
        module = listener_config.pop('module')
        module = "jarbas_pocketsphinx_ww_plug" if module == "pocketsphinx" else module
        hotword_config = {listener_config.pop("wake_word"): {"module": module,
                                                             "phonemes": listener_config.pop('phonemes'),
                                                             "threshold": listener_config.pop('threshold'),
                                                             "lang": listener_config.get('language'),
                                                             "sample_rate": listener_config.get('sample_rate'),
                                                             "listen": True,
                                                             "sound": "snd/start_listening.wav",
                                                             "local_model_file": listener_config.get("precise", {}).get(
                                                                 "local_model_file")}}
    else:
        hotword_config = user_config.get("hotwords", {})

    return {"listener": listener_config,
            "hotwords": hotword_config,
            "audio_parsers": {},
            "lang": lang,
            "stt": stt_config,
            "metric_upload": local_config.get("prefFlags", {}).get("metrics", False),
            "remote_server": local_config.get("remoteVars", {}).get("remoteHost", "64.34.186.120"),
            "keys": {}
            }


class NGIConfig:
    configuration_list = []

    def __init__(self, name, path=None):
        self.name = name
        self.path = path or get_config_dir()
        self.parser = YAML()
        self.lock = FileLock(f"{self.file_path}.lock", timeout=10)
        self.content = self._load_yaml_file()
        if not self.content:
            self.content = {}

        NGIConfig.configuration_list.append(self.name)

    def populate(self, content, check_existing=False):
        if not check_existing:
            self.__add__(content)
            return
        self.content = dict_merge(content, self.content)  # to_change, one_with_all_keys
        self._reload_yaml_file()

    def remove_key(self, *key):
        for item in key:
            self.__sub__(item)

    def make_equal_by_keys(self, other: MutableMapping):
        """
        Adds and removes keys from this config such that it has the same keys as 'other'. Configuration values are
        preserved with any added keys using default values from 'other'.
        Args:
            other: dict of keys and default values this configuration should have
        """
        old_content = deepcopy(self.content)
        self.content = dict_make_equal_keys(self.content, other)
        if self.content != old_content:
            self._reload_yaml_file()

    def update_keys(self, other):
        """
        Adds keys to this config such that it has all keys in 'other'. Configuration values are
        preserved with any added keys using default values from 'other'.
        Args:
            other: dict of keys and default values this should be added to this configuration
        """
        self.content = dict_update_keys(self.content, other)  # to_change, one_with_all_keys
        self._reload_yaml_file()

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

    def check_for_updates(self) -> dict:
        """
        Reloads updated configuration from disk. Used to reload changes when other instances modify a configuration
        Returns:Updated configuration.content
        """
        new_content = self._load_yaml_file()
        if new_content:
            LOG.debug(f"{self.name} Checked for Updates")
            self.content = new_content
        else:
            LOG.warning("new_content is empty!!")
            new_content = self._load_yaml_file()
            if new_content:
                LOG.debug("second attempt success")
                self.content = new_content
            else:
                LOG.error("second attempt failed")
        return self.content

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
        before_change = self.content
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
            self._reload_yaml_file()
        else:
            LOG.debug("More than one change")

    def export_to_json(self) -> str:
        """
        Export this configuration to a json file
        Returns: path to exported file
        """
        json_filename = os.path.join(self.path, f"{self.name}.json")
        write_to_json(self.content, json_filename)
        return json_filename

    def from_dict(self, pref_dict: dict):
        """
        Constructor to build this configuration object with the passed dict of data
        Args:
            pref_dict: dict to populate configuration with

        Returns: this object

        """
        self.content = pref_dict
        self._reload_yaml_file()
        return self

    def from_json(self, json_path: str):
        """
        Constructor to build this configuration object with the passed json file
        Args:
            json_path: Path to json file to populate configuration with

        Returns: this object

        """
        self.content = load_commented_json(json_path)
        self._reload_yaml_file()
        return self

    def _load_yaml_file(self) -> dict:
        """
        Loads and parses the YAML file at a given filepath into the Python
        dictionary object.
        :return: dictionary, containing all keys and values from the most current
                 selected YAML.
        """
        try:
            with open(self.file_path, 'r') as f:
                return self.parser.load(f)
        except FileNotFoundError as x:
            LOG.error(f"Configuration file not found error: {x}")
        except Exception as c:
            LOG.error(f"Configuration file error: {c}")
        return dict()

    def _reload_yaml_file(self):
        """
        Overwrites and/or updates the YML at the specified file_path.
        :return: updated dictionary of YAML keys and values.
        """
        try:
            with self.lock.acquire(30):
                tmp_filename = join(self.path, self.name + ".tmp")
                LOG.debug(f"tmp_filename={tmp_filename}")
                shutil.copy2(self.file_path, tmp_filename)
                with open(self.file_path, 'w+') as f:
                    self.parser.dump(self.content, f)
                    LOG.debug(f"YAML updated {self.name}")
        except FileNotFoundError as x:
            LOG.error(f"Configuration file not found error: {x}")

    def __repr__(self):
        return "NGIConfig('{}') \n {}".format(self.name, self.file_path)

    def __str__(self):
        return "{}: {}".format(self.file_path, json.dumps(self.content, indent=4))

    def __add__(self, other):
        # with self.lock.acquire(30):
        if other:
            if not isinstance(other, NGIConfig) and not isinstance(other, MutableMapping):
                raise AttributeError("__add__ expects dict or config object as argument")
            to_update = other
            if isinstance(other, NGIConfig):
                to_update = other.content
            if self.content:
                self.content.update(to_update)
            else:
                self.content = to_update
        else:
            raise TypeError("__add__ expects an argument other than None")
        self._reload_yaml_file()

    def __sub__(self, *other):
        # with self.lock.acquire(30):
        if other:
            for element in other:
                if isinstance(element, NGIConfig):
                    to_remove = list(element.content.keys())
                elif isinstance(element, MutableMapping):
                    to_remove = list(element.keys())
                elif isinstance(element, list):
                    to_remove = element
                elif isinstance(element, str):
                    to_remove = [element]
                else:
                    raise AttributeError("__add__ expects dict, list, str, or config object as the argument")

                if self.content:
                    self.content = delete_recursive_dictionary_keys(self.content, to_remove)
                else:
                    raise TypeError("{} config is empty".format(self.name))
        else:
            raise TypeError("__sub__ expects an argument other than None")
        self._reload_yaml_file()
