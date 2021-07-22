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
import os
import unittest
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


class ConfigurationUtilTests(unittest.TestCase):
    def doCleanups(self) -> None:
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

    def test_get_api_config(self):
        config = get_neon_api_config()
        self.assertIsInstance(config["url"], str)
        self.assertIsInstance(config["version"], str)
        self.assertIsInstance(config["update"], bool)
        self.assertIsInstance(config["metrics"], bool)
        self.assertIsInstance(config["disabled"], bool)

    def test_get_device_type(self):
        self.assertIn(get_neon_device_type(), ("desktop", "pi", "linux"))

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
        # self.assertIsInstance(mycroft_config["keys"], dict)
        # self.assertEqual(mycroft_config["skills"]["directory"], mycroft_config["skills"]["directory_override"])
        # self.assertIsInstance(mycroft_config["language"], dict)
        # self.assertIsInstance(mycroft_config["listener"], dict)
        # self.assertIsInstance(mycroft_config["stt"], dict)
        # self.assertIsInstance(mycroft_config["tts"], dict)

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

        self.assertEqual(local_config["dirVars"]["skillsDir"], os.path.join(test_dir, "skills"))
        self.assertEqual(local_config["dirVars"]["diagsDir"], os.path.join(test_dir, "Diagnostics"))
        self.assertEqual(local_config["dirVars"]["logsDir"], os.path.join(test_dir, "logs"))

        shutil.rmtree(test_dir)
        NGIConfig.configuration_list = dict()

    def test_create_config_from_setup_params_non_dev_mode(self):
        test_dir = f"{ROOT_DIR}/test_setup_config"
        os.environ["devMode"] = "false"
        os.environ["autoStart"] = "true"
        os.environ["autoUpdate"] = "true"
        os.environ["devName"] = "Test-Device"
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
        self.assertEqual(local_config["devVars"]["devType"], "linux")
        self.assertEqual(local_config["stt"]["module"], "stt_module")
        self.assertEqual(local_config["tts"]["module"], "tts_module")

        self.assertEqual(local_config["dirVars"]["skillsDir"], "~/.local/share/neon/skills")
        self.assertEqual(local_config["dirVars"]["diagsDir"], "~/Documents/NeonGecko/Diagnostics")
        self.assertEqual(local_config["dirVars"]["logsDir"], "~/.local/share/neon/logs")

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

    def test_write_mycroft_compatible_config(self):
        test_path = os.path.join(CONFIG_PATH, "test.conf")
        config = get_mycroft_compatible_config()
        write_mycroft_compatible_config(test_path)
        with open(test_path) as f:
            from_disk = json.load(f)
        self.assertEqual(from_disk, config)
        os.remove(test_path)

    def test_config_no_permissions(self):
        with self.assertRaises(PermissionError):
            NGIConfig("test_config", "/root/")


if __name__ == '__main__':
    unittest.main()
