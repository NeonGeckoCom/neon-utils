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

import logging
import shutil
import sys
import os
import unittest

from ruamel.yaml import safe_load
from pprint import pformat
from time import sleep

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.configuration_utils import *
from neon_utils.authentication_utils import *

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, "configuration")

TEST_DICT = {"section 1": {"key1": "val1",
                           "key2": "val2"},
             "section 2": {"key_1": "val1",
                           "key_2": "val2"}}


class NGIConfigTests(unittest.TestCase):
    def doCleanups(self) -> None:
        if os.getenv("NEON_CONFIG_PATH"):
            os.environ.pop("NEON_CONFIG_PATH")
        for file in glob(os.path.join(CONFIG_PATH, ".*.lock")):
            os.remove(file)
        for file in glob(os.path.join(CONFIG_PATH, ".*.tmp")):
            os.remove(file)
        for file in glob(os.path.join(ROOT_DIR, "credentials", ".*.lock")):
            os.remove(file)
        for file in glob(os.path.join(ROOT_DIR, "credentials", ".*.tmp")):
            os.remove(file)
        if os.path.exists(os.path.join(CONFIG_PATH, "old_user_info.yml")):
            os.remove(os.path.join(CONFIG_PATH, "old_user_info.yml"))

    def test_load_config(self):
        local_conf = NGIConfig("ngi_local_conf", CONFIG_PATH)
        self.assertIsInstance(local_conf.content, dict)
        self.assertIsInstance(local_conf.content["devVars"], dict)
        self.assertIsInstance(local_conf.content["prefFlags"]["devMode"], bool)

    def test_config_get(self):
        local_conf = NGIConfig("ngi_local_conf", CONFIG_PATH)
        self.assertIsInstance(local_conf, NGIConfig)
        self.assertIsInstance(local_conf.content, dict)
        self.assertIsInstance(local_conf["devVars"], dict)
        self.assertIsInstance(local_conf["prefFlags"]["devMode"], bool)
        self.assertEqual(local_conf["prefFlags"], local_conf.get("prefFlags"))
        self.assertIsNone(local_conf.get("fake_key"))
        self.assertTrue(local_conf.get("fake_key", True))

    def test_config_set(self):
        local_conf = NGIConfig("ngi_local_conf", CONFIG_PATH)
        self.assertIsInstance(local_conf.content, dict)
        self.assertIsInstance(local_conf["prefFlags"]["devMode"], bool)

        local_conf["prefFlags"]["devMode"] = True
        self.assertTrue(local_conf["prefFlags"]["devMode"])

        local_conf["prefFlags"]["devMode"] = False
        self.assertFalse(local_conf["prefFlags"]["devMode"])

    def test_get_config_dir_invalid_override(self):
        os.environ["NEON_CONFIG_PATH"] = "/invalid"
        config_path = get_config_dir()
        self.assertNotEqual(config_path, "/invalid")
        os.environ.pop("NEON_CONFIG_PATH")
        self.assertIsNone(os.getenv("NEON_CONFIG_PATH"))

    def test_make_equal_keys(self):
        old_user_info = os.path.join(CONFIG_PATH, "old_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        shutil.copy(ngi_user_info, old_user_info)
        user_conf = NGIConfig("ngi_user_info", CONFIG_PATH, True)
        self.assertEqual(user_conf.content["user"]["full_name"], 'Test User')
        self.assertNotIn("phone_verified", user_conf.content["user"])
        self.assertIn('bad_key', user_conf.content["user"])

        user_conf.make_equal_by_keys(NGIConfig("clean_user_info", CONFIG_PATH).content)
        self.assertIn("phone_verified", user_conf.content["user"])
        self.assertNotIn('bad_key', user_conf.content["user"])
        self.assertFalse(user_conf.content["user"]["phone_verified"])
        self.assertEqual(user_conf.content["user"]["full_name"], 'Test User')

        new_user_info = NGIConfig("ngi_user_info", CONFIG_PATH)
        self.assertEqual(user_conf.content, new_user_info.content)
        shutil.copy(old_user_info, ngi_user_info)

    def test_make_equal_keys_no_recurse(self):
        skill_settings = NGIConfig("skill_populated", CONFIG_PATH)
        correct_settings = deepcopy(skill_settings.content)
        skill_settings.make_equal_by_keys(NGIConfig("skill_default", CONFIG_PATH).content, False)
        self.assertEqual(correct_settings, skill_settings.content)

    def test_update_keys(self):
        old_user_info = os.path.join(CONFIG_PATH, "old_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        shutil.copy(ngi_user_info, old_user_info)
        user_conf = NGIConfig("ngi_user_info", CONFIG_PATH, True)
        self.assertEqual(user_conf.content["user"]["full_name"], 'Test User')
        self.assertNotIn("phone_verified", user_conf.content["user"])
        self.assertIn('bad_key', user_conf.content["user"])

        user_conf.update_keys(NGIConfig("clean_user_info", CONFIG_PATH).content)
        self.assertIn("phone_verified", user_conf.content["user"])
        self.assertIn('bad_key', user_conf.content["user"])
        self.assertFalse(user_conf.content["user"]["phone_verified"])
        self.assertEqual(user_conf.content["user"]["full_name"], 'Test User')

        new_user_info = NGIConfig("ngi_user_info", CONFIG_PATH)
        self.assertEqual(user_conf.content, new_user_info.content)
        shutil.move(old_user_info, ngi_user_info)

    def test_update_key(self):
        old_user_info = os.path.join(CONFIG_PATH, "old_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        shutil.copy(ngi_user_info, old_user_info)
        user_conf = NGIConfig("ngi_user_info", CONFIG_PATH)

        self.assertEqual(user_conf.content["user"]["full_name"], 'Test User')
        user_conf.update_yaml_file("user", "full_name", "New Name", multiple=False, final=True)
        self.assertEqual(user_conf.content["user"]["full_name"], 'New Name')
        new_user_conf = NGIConfig("ngi_user_info", CONFIG_PATH)
        self.assertEqual(user_conf.content["user"]["full_name"], new_user_conf.content["user"]["full_name"])
        shutil.copy(old_user_info, ngi_user_info)

    def test_export_json(self):
        user_conf = NGIConfig("ngi_user_info", CONFIG_PATH)
        json_file = user_conf.export_to_json()
        with open(json_file, "r") as f:
            from_disk = json.load(f)
        self.assertEqual(from_disk, user_conf.content)
        os.remove(json_file)

    def test_import_dict(self):
        test_conf = NGIConfig("test_conf", CONFIG_PATH).from_dict(TEST_DICT)
        self.assertEqual(test_conf.content, TEST_DICT)
        from_disk = NGIConfig("test_conf", CONFIG_PATH)
        self.assertEqual(from_disk.content, test_conf.content)
        os.remove(test_conf.file_path)

    def test_import_json(self):
        json_path = os.path.join(CONFIG_PATH, "mycroft.conf")
        test_conf = NGIConfig("mycroft", CONFIG_PATH).from_json(json_path)
        parsed_json = load_commented_json(json_path)
        self.assertEqual(parsed_json, test_conf.content)
        from_disk = NGIConfig("mycroft", CONFIG_PATH)
        self.assertEqual(from_disk.content, test_conf.content)
        os.remove(test_conf.file_path)

    def test_config_cache(self):
        from neon_utils.configuration_utils import NGIConfig as NGIConf2
        bak_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.bak")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")

        shutil.copy(ngi_local_conf, bak_local_conf)
        config_1 = NGIConfig("ngi_local_conf", CONFIG_PATH)
        self.assertFalse(config_1.requires_reload)
        config_2 = NGIConf2("ngi_local_conf", CONFIG_PATH, True)
        self.assertFalse(config_2.requires_reload)
        self.assertEqual(config_1._content, config_2._content)
        self.assertNotEqual(config_1, config_2)

        config_1.update_yaml_file("prefFlags", "autoStart", False)
        self.assertFalse(config_1._pending_write)
        self.assertEqual(config_2._content["prefFlags"]["autoStart"], True)
        self.assertFalse(config_2._pending_write)

        self.assertNotEqual(config_1._loaded, config_2._loaded)
        self.assertGreater(config_1._loaded, config_2._loaded)
        self.assertTrue(config_2.requires_reload)
        self.assertEqual(config_1.content, config_2.content)
        self.assertEqual(config_1._loaded, config_2._loaded)

        config_2.update_yaml_file("prefFlags", "devMode", False, multiple=True)
        self.assertFalse(config_2["prefFlags"]["devMode"])
        self.assertTrue(config_2._pending_write)
        config_2.write_changes()
        self.assertFalse(config_2._pending_write)
        self.assertTrue(config_1.requires_reload)
        self.assertEqual(config_1.content["prefFlags"]["devMode"], False)

        config_2.update_yaml_file("prefFlags", "devMode", True, multiple=True)
        self.assertTrue(config_2._pending_write)
        self.assertTrue(config_2["prefFlags"]["devMode"])
        self.assertFalse(config_1["prefFlags"]["devMode"])

        shutil.move(bak_local_conf, ngi_local_conf)

    def test_multi_config(self):
        bak_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.bak")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")

        shutil.copy(ngi_local_conf, bak_local_conf)

        config_objects = []
        for i in range(100):
            config_objects.append(NGIConfig("ngi_local_conf", CONFIG_PATH, True))

        first_config = config_objects[0]
        last_config = config_objects[-1]
        self.assertIsInstance(first_config, NGIConfig)
        self.assertIsInstance(last_config, NGIConfig)

        self.assertEqual(first_config.content, last_config.content)
        first_config.update_yaml_file("prefFlags", "devMode", False)

        self.assertFalse(last_config["prefFlags"]["devMode"])
        self.assertEqual(first_config.content, last_config.content)

        shutil.move(bak_local_conf, ngi_local_conf)

    def test_concurrent_config_read(self):
        from threading import Thread
        valid_config = NGIConfig("dep_user_info", CONFIG_PATH)
        test_results = {}

        def _open_config(idx):
            from neon_utils.configuration_utils import NGIConfig as Config
            config = Config("dep_user_info", CONFIG_PATH, True)
            test_results[idx] = config.content == valid_config.content

        for i in range(10):
            Thread(target=_open_config, args=(i,), daemon=True).start()
        while not len(test_results.keys()) == 10:
            sleep(0.5)
        self.assertTrue(all(test_results.values()))

    def test_new_ngi_config(self):
        config = NGIConfig("temp_conf", CONFIG_PATH)
        self.assertIsInstance(config.content, dict)
        os.remove(os.path.join(CONFIG_PATH, "temp_conf.yml"))


class ConfigurationUtilTests(unittest.TestCase):
    def doCleanups(self) -> None:
        if os.getenv("NEON_CONFIG_PATH"):
            os.environ.pop("NEON_CONFIG_PATH")
        for file in glob(os.path.join(CONFIG_PATH, ".*.lock")):
            os.remove(file)
        for file in glob(os.path.join(CONFIG_PATH, ".*.tmp")):
            os.remove(file)
        for file in glob(os.path.join(ROOT_DIR, "credentials", ".*.lock")):
            os.remove(file)
        for file in glob(os.path.join(ROOT_DIR, "credentials", ".*.tmp")):
            os.remove(file)
        if os.path.exists(os.path.join(CONFIG_PATH, "old_user_info.yml")):
            os.remove(os.path.join(CONFIG_PATH, "old_user_info.yml"))

    def test_get_legacy_config_path(self):
        from neon_utils.configuration_utils import _get_legacy_config_dir
        test_dir = join(CONFIG_PATH, "config_path_test_dirs")

        venv_path = join(test_dir, "arbitrary_venv")
        mycroft_path = join(test_dir, "default_mycroft")
        cloned_neon_path = join(test_dir, "cloned_neon")
        legacy_neon_path = join(test_dir, "legacy_neon_path")

        test_path = ["/lib/python3.8", "/usr/lib/python3.8", "/opt/mycroft"]
        self.assertIsNone(_get_legacy_config_dir(test_path))

        test_path.insert(0, f"{venv_path}/.venv/lib/python3.8/site-packages")
        self.assertEqual(_get_legacy_config_dir(test_path), venv_path)

        test_path.insert(0, mycroft_path)
        self.assertEqual(_get_legacy_config_dir(test_path), mycroft_path)

        test_path.insert(0, cloned_neon_path)
        self.assertEqual(_get_legacy_config_dir(test_path), cloned_neon_path)

        test_path.insert(0, legacy_neon_path)
        self.assertEqual(_get_legacy_config_dir(test_path), f"{legacy_neon_path}/NGI")

        dev_test_path = ['', '/usr/lib/python38.zip', '/usr/lib/python3.8', '/usr/lib/python3.8/lib-dynload',
                         f'{join(test_dir, "dev_environment")}/venv/lib/python3.8/site-packages',
                         f'{join(test_dir, "dev_environment")}/neon_cli',
                         f'{join(test_dir, "dev_environment")}/transcripts_controller',
                         f'{join(test_dir, "dev_environment")}/neon_enclosure',
                         f'{join(test_dir, "dev_environment")}/neon_speech',
                         f'{join(test_dir, "dev_environment")}/neon_audio',
                         f'{join(test_dir, "dev_environment")}/NeonCore',
                         f'{join(test_dir, "dev_environment")}/neon-test-utils',
                         f'{join(test_dir, "dev_environment")}/neon_display',
                         f'{join(test_dir, "dev_environment")}/neon_messagebus',
                         f'{join(test_dir, "dev_environment")}/neon_gui']
        self.assertEqual(_get_legacy_config_dir(dev_test_path), f'{join(test_dir, "dev_environment")}/NeonCore')

    def test_get_config_dir_default(self):
        config_path = get_config_dir()
        self.assertTrue(os.path.isdir(config_path))

    def test_get_config_dir_valid_override(self):
        os.environ["NEON_CONFIG_PATH"] = "~/"
        self.assertIsNotNone(os.getenv("NEON_CONFIG_PATH"))
        config_path = get_config_dir()
        self.assertEqual(config_path, os.path.expanduser("~/"))
        self.assertTrue(os.path.isdir(config_path))
        os.environ.pop("NEON_CONFIG_PATH")
        self.assertIsNone(os.getenv("NEON_CONFIG_PATH"))

    def test_delete_recursive_dictionary_keys_simple(self):
        test_dict = deepcopy(TEST_DICT)
        test_dict = delete_recursive_dictionary_keys(test_dict, ["key_1", "key1"])
        self.assertEqual(test_dict, {"section 1": {"key2": "val2"},
                                     "section 2": {"key_2": "val2"}})

    def test_delete_recursive_dictionary_keys_section(self):
        test_dict = deepcopy(TEST_DICT)
        test_dict = delete_recursive_dictionary_keys(test_dict, ["section 1"])
        self.assertEqual(test_dict, {"section 2": {"key_1": "val1",
                                                   "key_2": "val2"}})

    def test_dict_merge(self):
        to_update = deepcopy(TEST_DICT)
        new_keys = {"section 2": {"key_2": "new2",
                                  "key_3": "val3"}}
        updated = dict_merge(to_update, new_keys)
        self.assertEqual(updated["section 2"], {"key_1": "val1",
                                                "key_2": "new2",
                                                "key_3": "val3"})

    def test_dict_make_equal_keys(self):
        to_update = deepcopy(TEST_DICT)
        new_keys = {"section 2": {"key_2": "new2",
                                  "key_3": "val3"}}
        updated = dict_make_equal_keys(to_update, new_keys)
        self.assertEqual(updated, {"section 2": {"key_2": "val2",
                                                 "key_3": "val3"}
                                   })

    def test_dict_make_equal_keys_no_depth(self):
        to_update = deepcopy(TEST_DICT)
        new_keys = {"section 2": {"key_2": "new2",
                                  "key_3": "val3"}}
        updated = dict_make_equal_keys(to_update, new_keys, 0)
        self.assertEqual(updated, {"section 2": {"key_1": "val1",
                                                 "key_2": "val2"}
                                   })

    def test_dict_make_equal_keys_limited_depth(self):
        to_update = deepcopy(TEST_DICT)
        to_update["section 2"]["key_2"] = {"2_data": "value"}
        new_keys = {"section 2": {"key_2": {},
                                  "key_3": "val3"}}
        updated = dict_make_equal_keys(to_update, new_keys, 1)
        self.assertEqual(updated, {"section 2": {"key_2": {"2_data": "value"},
                                                 "key_3": "val3"}
                                   })

    def test_dict_make_equal_keys_no_keys(self):
        to_update = deepcopy(TEST_DICT)
        new_keys = dict()
        with self.assertRaises(ValueError):
            dict_make_equal_keys(to_update, new_keys)

    def test_dict_update_keys(self):
        to_update = deepcopy(TEST_DICT)
        new_keys = {"section 2": {"key_2": "new2",
                                  "key_3": "val3"}}
        updated = dict_update_keys(to_update, new_keys)
        self.assertEqual(updated["section 2"], {"key_1": "val1",
                                                "key_2": "val2",
                                                "key_3": "val3"})

    def test_write_json(self):
        file_path = os.path.join(CONFIG_PATH, "test.json")
        write_to_json(TEST_DICT, file_path)
        with open(file_path, "r") as f:
            from_disk = json.load(f)
        self.assertEqual(from_disk, TEST_DICT)
        os.remove(file_path)

    def test_safe_mycroft_config(self):
        from neon_utils.configuration_utils import _safe_mycroft_config
        config = _safe_mycroft_config()
        self.assertIsInstance(config, dict)

    def test_get_cli_config(self):
        config = get_neon_cli_config()
        self.assertIn("log_dir", config)
        self.assertIn("neon_core_version", config)
        self.assertIn("wake_words_enabled", config)

    def test_get_bus_config(self):
        config = get_neon_bus_config()
        self.assertIn("host", config)
        self.assertIn("port", config)
        self.assertIn("route", config)
        self.assertIn("ssl", config)

        self.assertIsInstance(config["host"], str)
        self.assertIsInstance(config["port"], int)
        self.assertIsInstance(config["route"], str)
        self.assertTrue(config["route"].startswith('/'))
        self.assertIsInstance(config["ssl"], bool)
        self.assertIsInstance(config["shared_connection"], bool)

    def test_get_api_config(self):
        config = get_neon_api_config()
        self.assertIsInstance(config["url"], str)
        self.assertIsInstance(config["version"], str)
        self.assertIsInstance(config["update"], bool)
        self.assertIsInstance(config["metrics"], bool)
        self.assertIsInstance(config["disabled"], bool)

    def test_get_device_type(self):
        self.assertIn(get_neon_device_type(),
                      ("desktop", "pi", "linux", "server"))

    def test_get_speech_config(self):
        config = get_neon_speech_config()
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config["stt"], dict)
        self.assertIsInstance(config["listener"], dict)
        self.assertIsInstance(config["hotwords"], dict)
        self.assertIsInstance(config["listener"]["wake_word_enabled"], bool)
        self.assertIsInstance(config["listener"]["phoneme_duration"], int)

    def test_get_audio_config(self):
        config = get_neon_audio_config()
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config["Audio"], dict)
        self.assertIsInstance(config["tts"], dict)
        self.assertIsInstance(config["language"], dict)

    def test_get_gui_config(self):
        config = get_neon_gui_config()
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config["lang"], str)
        self.assertIsInstance(config["enclosure"], str)
        self.assertIsInstance(config["host"], str)
        self.assertIsInstance(config["port"], int)
        self.assertIsInstance(config["base_port"], int)
        self.assertIsInstance(config["route"], str)
        self.assertIsInstance(config["ssl"], bool)
        self.assertIsInstance(config["resource_root"], str)
        self.assertIn("file_server", config.keys())

        self.assertEqual(config["port"], config["base_port"])

    def test_get_user_config_add_keys(self):
        old_user_info = os.path.join(CONFIG_PATH, "old_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        bak_local_conf = os.path.join(CONFIG_PATH, "bak_local_conf.yml")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")

        shutil.copy(ngi_local_conf, bak_local_conf)
        shutil.copy(ngi_user_info, old_user_info)
        config = get_neon_user_config(CONFIG_PATH)
        user_config_keys = ["user", "brands", "speech", "units", "location"]
        self.assertTrue(all(k for k in user_config_keys if k in config))
        shutil.move(old_user_info, ngi_user_info)
        shutil.move(bak_local_conf, ngi_local_conf)

    def test_get_user_config_create(self):
        old_user_info = os.path.join(CONFIG_PATH, "old_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        bak_local_conf = os.path.join(CONFIG_PATH, "bak_local_conf.yml")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")

        shutil.copy(ngi_local_conf, bak_local_conf)
        shutil.move(ngi_user_info, old_user_info)
        config = get_neon_user_config(CONFIG_PATH)
        self.assertTrue(os.path.isfile(ngi_user_info))
        user_config_keys = ["user", "brands", "speech", "units", "location"]
        self.assertTrue(all(k for k in user_config_keys if k in config))
        shutil.move(old_user_info, ngi_user_info)
        shutil.move(bak_local_conf, ngi_local_conf)

    def test_get_user_config_migrate_keys(self):
        bak_user_info = os.path.join(CONFIG_PATH, "bak_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        old_user_info = os.path.join(CONFIG_PATH, "dep_user_info.yml")
        bak_local_conf = os.path.join(CONFIG_PATH, "bak_local_conf.yml")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")
        shutil.move(ngi_user_info, bak_user_info)
        shutil.copy(old_user_info, ngi_user_info)
        shutil.copy(ngi_local_conf, bak_local_conf)

        user_conf = get_neon_user_config(CONFIG_PATH)
        user_config_keys = ["user", "brands", "speech", "units", "location"]
        self.assertTrue(all(k for k in user_config_keys if k in user_conf))

        local_config_keys = ["speech", "interface", "listener", "skills", "session", "tts", "stt", "logs", "device"]
        local_conf = NGIConfig("ngi_local_conf", CONFIG_PATH)
        self.assertTrue(all(k for k in local_config_keys if k in local_conf))

        shutil.move(bak_user_info, ngi_user_info)
        shutil.move(bak_local_conf, ngi_local_conf)

    def test_get_local_config_add_keys(self):
        old_local_conf = os.path.join(CONFIG_PATH, "old_local_conf.yml")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")
        shutil.copy(ngi_local_conf, old_local_conf)
        config = get_neon_local_config(CONFIG_PATH)
        local_config_keys = ["prefFlags", "interface", "devVars", "gestures", "audioService", "padatious", "websocket",
                             "gui", "hotwords", "listener", "skills", "session", "tts", "stt", "logs", "device"]
        self.assertTrue(all(k for k in local_config_keys if k in config))
        shutil.move(old_local_conf, ngi_local_conf)

    def test_get_local_config_create(self):
        old_local_conf = os.path.join(CONFIG_PATH, "old_local_conf.yml")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")
        shutil.move(ngi_local_conf, old_local_conf)
        config = get_neon_local_config(CONFIG_PATH)
        self.assertTrue(os.path.isfile(ngi_local_conf))
        local_config_keys = ["prefFlags", "interface", "devVars", "gestures", "audioService", "padatious", "websocket",
                             "gui", "hotwords", "listener", "skills", "session", "tts", "stt", "logs", "device"]
        self.assertTrue(all(k for k in local_config_keys if k in config))
        shutil.move(old_local_conf, ngi_local_conf)

    def test_user_config_keep_keys(self):
        bak_user_info = os.path.join(CONFIG_PATH, "bak_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        shutil.move(ngi_user_info, bak_user_info)

        user_conf = get_neon_user_config(CONFIG_PATH)
        user_conf.update_yaml_file("brands", "favorite_brands", {'neon': 1})
        self.assertEqual(user_conf["brands"]["favorite_brands"]['neon'], 1)

        new_user_conf = get_neon_user_config(CONFIG_PATH)
        self.assertEqual(user_conf.content, new_user_conf.content)
        self.assertEqual(user_conf["brands"]["favorite_brands"]['neon'], 1)

        shutil.move(bak_user_info, ngi_user_info)

    def test_get_lang_config(self):
        config = get_neon_lang_config()
        self.assertIsInstance(config, dict)
        self.assertIn("internal", config)
        self.assertIn("user", config)
        self.assertIn("detection_module", config)
        self.assertIn("translation_module", config)
        self.assertIn("boost", config)
        self.assertIsInstance(config["libretranslate"], dict)

    def test_get_client_config(self):
        config = get_neon_client_config()
        self.assertIn("devName", config["devVars"])
        self.assertIn("devType", config["devVars"])
        self.assertIn("version", config["devVars"])
        self.assertIn("coreGit", config["remoteVars"])
        self.assertIn("skillsGit", config["remoteVars"])
        self.assertIsInstance(config["server_addr"], str)

    def test_get_transcribe_config(self):
        config = get_neon_transcribe_config()
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config["audio_permission"], bool)
        self.assertIsInstance(config["transcript_dir"], str)

    def test_get_tts_config(self):
        config = get_neon_tts_config()
        self.assertIsInstance(config["module"], str)
        self.assertIsInstance(config[config["module"]], dict)

    def test_get_skills_config(self):
        config = get_neon_skills_config()
        self.assertIsInstance(config["debug"], bool)
        self.assertIsInstance(config["blacklist"], list)
        self.assertIsInstance(config["priority"], list)
        self.assertIsInstance(config["update_interval"], float)
        self.assertIsInstance(config["data_dir"], str)
        self.assertIsInstance(config["skill_manager"], str)

        self.assertIsInstance(config["install_default"], bool)
        self.assertIsInstance(config["install_essential"], bool)
        self.assertIn("default_skills", config)
        self.assertIn("essential_skills", config)
        self.assertIn("neon_token", config)

        self.assertEqual(config["update_interval"], config["auto_update_interval"])  # Backwards Compat.
        self.assertIsInstance(config["directory"], str)
        self.assertIsInstance(config["disable_osm"], bool)

        if config.get("msm"):
            self.assertIsInstance(config["msm"], dict)
            self.assertIsInstance(config["msm"]["directory"], str)
            self.assertIsInstance(config["msm"]["versioned"], bool)
            self.assertIsInstance(config["msm"]["repo"], dict)

            self.assertIsInstance(config["msm"]["repo"]["branch"], str)
            self.assertIsInstance(config["msm"]["repo"]["cache"], str)
            self.assertIsInstance(config["msm"]["repo"]["url"], str)

    def test_get_mycroft_compat_config(self):
        mycroft_config = get_mycroft_compatible_config()
        self.assertIsInstance(mycroft_config, dict)
        self.assertIsInstance(mycroft_config["gui_websocket"], dict)
        self.assertIsInstance(mycroft_config["gui_websocket"]["host"], str)
        self.assertIsInstance(mycroft_config["gui_websocket"]["base_port"], int)
        self.assertIsInstance(mycroft_config["ready_settings"], list)
        # self.assertIsInstance(mycroft_config["keys"], dict)
        # self.assertEqual(mycroft_config["skills"]["directory"], mycroft_config["skills"]["directory_override"])
        # self.assertIsInstance(mycroft_config["language"], dict)
        # self.assertIsInstance(mycroft_config["listener"], dict)
        # self.assertIsInstance(mycroft_config["stt"], dict)
        # self.assertIsInstance(mycroft_config["tts"], dict)

    def test_is_neon_core(self):
        self.assertIsInstance(is_neon_core(), bool)

    def test_get_speech_config_local_changes(self):
        local_config = NGIConfig("ngi_local_conf")
        speech_config = get_neon_speech_config()
        self.assertNotEqual(speech_config.get("listener"), local_config["listener"])

    def test_create_config_from_setup_params_dev_mode(self):
        test_dir = f"{ROOT_DIR}/test_setup_config"
        os.environ["devMode"] = "true"
        os.environ["autoStart"] = "true"
        os.environ["autoUpdate"] = "true"
        os.environ["devName"] = "Test-Device"
        os.environ["sttModule"] = "stt_module"
        os.environ["ttsModule"] = "tts_module"
        os.environ["installServer"] = "false"
        os.environ["installerDir"] = test_dir
        os.environ["GITHUB_TOKEN"] = "git_token"
        local_config = create_config_from_setup_params(test_dir)

        self.assertTrue(local_config["prefFlags"]["devMode"])
        self.assertTrue(local_config["prefFlags"]["autoStart"])
        self.assertTrue(local_config["prefFlags"]["autoUpdate"])
        self.assertEqual(local_config["devVars"]["devName"], "Test-Device")
        self.assertEqual(local_config["devVars"]["devType"], "linux")
        self.assertEqual(local_config["stt"]["module"], "stt_module")
        self.assertEqual(local_config["tts"]["module"], "tts_module")
        self.assertEqual(local_config["skills"]["auto_update"],
                         local_config["prefFlags"]["autoUpdate"])

        self.assertEqual(local_config["dirVars"]["skillsDir"],
                         os.path.join(test_dir, "skills"))
        self.assertEqual(local_config["dirVars"]["diagsDir"],
                         os.path.join(test_dir, "Diagnostics"))
        self.assertEqual(local_config["dirVars"]["logsDir"],
                         os.path.join(test_dir, "logs"))

        shutil.rmtree(test_dir)
        NGIConfig.configuration_list = dict()

    def test_create_config_from_setup_params_non_dev_mode_spec_dev_type(self):
        test_dir = f"{ROOT_DIR}/test_setup_config"
        os.environ["devMode"] = "false"
        os.environ["autoStart"] = "true"
        os.environ["autoUpdate"] = "true"
        os.environ["devName"] = "Test-Device"
        os.environ["devType"] = "neonPi"
        os.environ["sttModule"] = "stt_module"
        os.environ["ttsModule"] = "tts_module"
        os.environ["installServer"] = "false"
        os.environ["installerDir"] = test_dir
        os.environ["GITHUB_TOKEN"] = "git_token"
        local_config = create_config_from_setup_params(test_dir)

        self.assertFalse(local_config["prefFlags"]["devMode"])
        self.assertTrue(local_config["prefFlags"]["autoStart"])
        self.assertTrue(local_config["prefFlags"]["autoUpdate"])
        self.assertEqual(local_config["devVars"]["devName"], "Test-Device")
        self.assertEqual(local_config["devVars"]["devType"], "neonPi")
        self.assertEqual(local_config["stt"]["module"], "stt_module")
        self.assertEqual(local_config["tts"]["module"], "tts_module")
        self.assertEqual(local_config["skills"]["auto_update"],
                         local_config["prefFlags"]["autoUpdate"])

        self.assertEqual(local_config["dirVars"]["skillsDir"],
                         "~/.local/share/neon/skills")
        self.assertEqual(local_config["dirVars"]["diagsDir"],
                         "~/Documents/NeonGecko/Diagnostics")
        self.assertEqual(local_config["dirVars"]["logsDir"],
                         "~/.local/share/neon/logs")

        shutil.rmtree(test_dir)
        NGIConfig.configuration_list = dict()

    def test_unequal_cache_configs(self):
        bak_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.bak")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")
        shutil.copy(ngi_local_conf, bak_local_conf)

        def_config = get_neon_local_config(f"{ROOT_DIR}/test")
        oth_config = get_neon_local_config(CONFIG_PATH)
        self.assertNotEqual(def_config, oth_config)
        self.assertNotEqual(def_config.content, oth_config.content)

        shutil.rmtree(f"{ROOT_DIR}/test")
        shutil.move(bak_local_conf, ngi_local_conf)

    def test_added_module_config(self):
        bak_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.bak")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")
        ngi_test_conf = os.path.join(CONFIG_PATH, "local_conf_with_stt_tts.yml")

        shutil.move(ngi_local_conf, bak_local_conf)
        shutil.copy(ngi_test_conf, ngi_local_conf)
        local_config = get_neon_local_config(CONFIG_PATH)
        self.assertEqual(local_config["tts"]["mozilla_remote"], {"url": "http://something.somewhere"})
        self.assertEqual(local_config["stt"]["some_module"], {"key": "value"})
        self.assertIn("dirVars", local_config.content.keys())
        shutil.move(bak_local_conf, ngi_local_conf)

    def test_move_language_config(self):
        bak_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.bak")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")
        ngi_test_conf = os.path.join(CONFIG_PATH, "local_conf_no_language.yml")

        shutil.move(ngi_local_conf, bak_local_conf)
        shutil.copy(ngi_test_conf, ngi_local_conf)
        local_config = get_neon_local_config(CONFIG_PATH)
        self.assertEqual(local_config["language"]["translation_module"], "old_translate_module")
        self.assertEqual(local_config["language"]["detection_module"], "old_detection_module")
        self.assertIsInstance(local_config["language"]["libretranslate"], dict)
        self.assertIn("dirVars", local_config.content.keys())
        shutil.move(bak_local_conf, ngi_local_conf)

    def test_added_hotwords_config(self):
        bak_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.bak")
        ngi_local_conf = os.path.join(CONFIG_PATH, "ngi_local_conf.yml")

        test_hotword_config = {"listen": True,
                               "model": "model_path"}

        shutil.move(ngi_local_conf, bak_local_conf)
        local_config = get_neon_local_config(CONFIG_PATH)
        hotwords_config = deepcopy(local_config["hotwords"])

        local_config['hotwords']["test_hotword"] = test_hotword_config
        for hotword, config in hotwords_config.items():
            self.assertEqual(local_config['hotwords'][hotword], config)

        fresh_config = get_neon_local_config(CONFIG_PATH)
        self.assertEqual(fresh_config.content, local_config.content)
        self.assertEqual(fresh_config['hotwords']['test_hotword'], test_hotword_config)

        shutil.move(bak_local_conf, ngi_local_conf)

    def test_get_neon_auth_config(self):
        auth_path = os.path.join(ROOT_DIR, "credentials")
        ngi_auth_vars = get_neon_auth_config(auth_path)
        self.assertEqual(ngi_auth_vars["amazon"], find_neon_aws_keys(auth_path))
        self.assertEqual(ngi_auth_vars["google"], find_neon_google_keys(auth_path))
        self.assertEqual(ngi_auth_vars["github"], {"token": find_neon_git_token(auth_path)})
        self.assertEqual(ngi_auth_vars["wolfram"], {"app_id": find_neon_wolfram_key(auth_path)})
        self.assertEqual(ngi_auth_vars["alpha_vantage"], {"api_key": find_neon_alpha_vantage_key(auth_path)})
        self.assertEqual(ngi_auth_vars["owm"], {"api_key": find_neon_owm_key(auth_path)})
        os.remove(ngi_auth_vars.file_path)

    def test_get_neon_auth_config_unwritable(self):
        real_auth_config = join(get_config_dir(), "ngi_auth_vars.yml")
        bak_auth_config = join(get_config_dir(), "ngi_auth.bak")
        if isfile(real_auth_config):
            shutil.copy(real_auth_config, bak_auth_config)
        os.environ["NEON_CONFIG_PATH"] = os.path.join(ROOT_DIR, "configuration", "unwritable_path")
        ngi_auth_vars = get_neon_auth_config()
        # with open(join(os.environ["NEON_CONFIG_PATH"], "ngi_auth_vars.yml")) as f:
        #     contents = safe_load(f)
        # self.assertEqual(contents, ngi_auth_vars.content)
        self.assertNotEqual(ngi_auth_vars.path, os.environ["NEON_CONFIG_PATH"])

        if isfile(bak_auth_config):
            shutil.move(bak_auth_config, real_auth_config)

    def test_write_mycroft_compatible_config(self):
        test_path = os.path.join(CONFIG_PATH, "test.conf")
        config = get_mycroft_compatible_config()
        write_mycroft_compatible_config(test_path)
        with open(test_path) as f:
            from_disk = json.load(f)
        self.assertEqual(from_disk, config)
        write_mycroft_compatible_config(test_path)
        with open(test_path) as f:
            from_disk_2 = json.load(f)
        self.assertEqual(from_disk_2, config)
        self.assertIsNone(config["Audio"].get("Audio"))
        os.remove(test_path)

    def test_config_no_permissions(self):
        with self.assertRaises(PermissionError):
            NGIConfig("test_config", "/root/")

    def test_parse_skill_configuration_valid(self):
        with open(join(CONFIG_PATH, "skill_settingsmeta.json")) as f:
            default_settings = json.load(f)
        parsed_settings = parse_skill_default_settings(default_settings)
        self.assertIsInstance(parsed_settings, dict)

    def test_simultaneous_config_updates(self):
        from threading import Thread
        test_results = {}

        config_path = join(CONFIG_PATH, "depreciated_language_config")
        backup_path = join(CONFIG_PATH, "backup_config")
        os.environ["NEON_CONFIG_PATH"] = config_path
        shutil.copytree(config_path, backup_path)

        def _open_config(idx):
            success = True
            try:
                local_config = deepcopy(get_neon_local_config(config_path).content)
                self.assertNotIn("translation_module", local_config["stt"])
                self.assertNotIn("detection_module", local_config["stt"])
            except Exception as e:
                LOG.error(e)
                success = False
            try:
                user_config = get_neon_user_config(config_path)
                self.assertNotIn("listener", user_config.content.keys())
            except Exception as e:
                LOG.error(e)
                success = False
            try:
                lang_config = get_neon_lang_config()
                self.assertIsInstance(lang_config["boost"], bool)
            except Exception as e:
                LOG.error(e)
                success = False
            test_results[idx] = success

        for i in range(64):
            Thread(target=_open_config, args=(i,), daemon=True).start()
        while not len(test_results.keys()) == 64:
            sleep(0.5)
        self.assertTrue(all(test_results.values()))

        shutil.rmtree(config_path)
        shutil.move(backup_path, config_path)

    def test_default_config(self):
        config = get_neon_local_config("/tmp/neon/test/")
        import requests
        resp = requests.get(config["skills"]["default_skills"])
        self.assertTrue(resp.ok)
        shutil.rmtree("/tmp/neon/test")
        # TODO: Test any other default values

    def test_populate_read_only_config_simple(self):
        from neon_utils.configuration_utils import _populate_read_only_config
        test_dir = os.path.join(ROOT_DIR, "configuration", "populate_tests")
        ro_dir = os.path.join(test_dir, "test_ro_dir")
        test_conf = NGIConfig("ngi_local_conf", test_dir, True)
        test_filename = basename(test_conf.file_path)

        self.assertTrue(_populate_read_only_config(ro_dir,
                                                   test_filename, test_conf))
        os.remove(test_conf.file_path)

    def test_populate_read_only_config_no_overwrite(self):
        from neon_utils.configuration_utils import _populate_read_only_config
        test_dir = os.path.join(ROOT_DIR, "configuration", "populate_tests")
        ro_dir = os.path.join(test_dir, "test_ro_dir")
        test_conf = get_neon_local_config(test_dir)
        test_filename = basename(test_conf.file_path)

        self.assertFalse(_populate_read_only_config(test_dir,
                                                    test_filename, test_conf))

        os.chdir(test_dir)
        self.assertFalse(_populate_read_only_config("./",
                                                    test_filename, test_conf))
        self.assertFalse(_populate_read_only_config(None,
                                                    test_filename, test_conf))
        self.assertFalse(_populate_read_only_config(ro_dir,
                                                    test_filename, test_conf))
        os.remove(test_conf.file_path)

    def test_init_config_dir(self):
        from neon_utils.configuration_utils import init_config_dir
        ro_dir = os.path.join(ROOT_DIR, "configuration", "unwritable_path")
        os.environ["NEON_CONFIG_PATH"] = ro_dir
        self.assertTrue(init_config_dir())

        self.assertFalse(init_config_dir())
        os.environ.pop("NEON_CONFIG_PATH")
        self.assertFalse(init_config_dir())

    def test_get_mycroft_compatible_location(self):
        from neon_utils.configuration_utils import \
            get_mycroft_compatible_location

        old_user_info = os.path.join(CONFIG_PATH, "old_user_info.yml")
        ngi_user_info = os.path.join(CONFIG_PATH, "ngi_user_info.yml")
        shutil.copy(ngi_user_info, old_user_info)

        user_config = get_neon_user_config(CONFIG_PATH)

        with self.assertRaises(KeyError):
            get_mycroft_compatible_location(user_config.content)

        location = get_mycroft_compatible_location(user_config["location"])
        self.assertEqual(location["city"]["name"], user_config["location"]["city"])
        self.assertEqual(location["city"]["code"], user_config["location"]["city"])
        self.assertEqual(location["city"]["state"]["name"],
                         user_config["location"]["state"])
        self.assertIsInstance(location["city"]["state"]["code"], str)
        self.assertEqual(location["city"]["state"]["country"]["name"],
                         user_config["location"]["country"])
        self.assertEqual(location["city"]["state"]["country"]["code"], "us")

        self.assertIsInstance(location["coordinate"]["latitude"], float)
        self.assertEqual(str(location["coordinate"]["latitude"]),
                         user_config["location"]["lat"])
        self.assertIsInstance(location["coordinate"]["longitude"], float)
        self.assertEqual(str(location["coordinate"]["longitude"]),
                         user_config["location"]["lng"])

        self.assertEqual(location["timezone"]["code"],
                         user_config["location"]["tz"])
        self.assertIsInstance(location["timezone"]["name"], str)
        self.assertIsInstance(location["timezone"]["offset"], float)
        self.assertEqual(location["timezone"]["dstOffset"], 3600000)

        shutil.move(old_user_info, ngi_user_info)


if __name__ == '__main__':
    unittest.main()
