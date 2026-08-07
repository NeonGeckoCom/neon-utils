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
import os
import unittest

from copy import deepcopy
from os.path import join
from threading import Event
from unittest.mock import patch
from ovos_bus_client import Message

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class UserUtilTests(unittest.TestCase):
    def test_get_user_prefs(self):
        from neon_utils.user_utils import get_user_prefs

        test_user_1_profile = {"user": {"username": "test_user_1",
                                        "email": "test@neon.ai"}}
        test_user_2_profile = {"user": {"username": "test_user_2",
                                        "address": "new_key"}}
        test_message_1 = Message("test_message", {}, {
            "username": "test_user_1",
            "user_profiles": [test_user_1_profile,
                              test_user_2_profile]})
        test_message_2 = Message("test_message", {}, {
            "username": "test_user_2",
            "user_profiles": [test_user_1_profile,
                              test_user_2_profile]})

        user_1 = get_user_prefs(test_message_1)
        self.assertEqual(user_1["user"]["username"], "test_user_1")
        self.assertEqual(user_1["user"]["email"], "test@neon.ai")
        self.assertEqual(test_message_1.context['user_profiles'][0], user_1)

        user_2 = get_user_prefs(test_message_2)
        self.assertEqual(user_2["user"]["username"], "test_user_2")
        self.assertIn("address", user_2["user"])
        self.assertEqual(test_message_2.context['user_profiles'][1], user_2)

        missing_profile = get_user_prefs(Message("", {},
                                                 {"username": "test",
                                                  "user_profiles": [{}]}))
        self.assertEqual(missing_profile["user"]["username"], "test")
        missing_profile_2 = get_user_prefs(Message("", {},
                                                   {"username": "test2",
                                                    "user_profiles": [{}]}))
        self.assertEqual(missing_profile_2["user"]["username"], "test2")

        def wrapper(message, valid_dict):
            self.assertEqual(get_user_prefs(), valid_dict)

        wrapper(test_message_1, user_1)
        wrapper(test_message_2, user_2)

    @patch("ovos_config.config.Configuration")
    def test_get_default_user_config_from_mycroft_conf(self, config):
        from ovos_config.models import LocalConf
        # Patch configuration for test
        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        config.return_value = LocalConf(join(test_config_dir, "mycroft",
                                             "mycroft.conf"))
        import importlib
        from neon_utils import user_utils
        importlib.reload(user_utils)
        from neon_utils.user_utils import get_default_user_config
        user_config = get_default_user_config()
        self.assertFalse(os.path.isfile(os.path.join(test_config_dir,
                                                     "ngi_user_info.yml")))
        self.assertIsInstance(user_config, dict)
        self.assertEqual(user_config["location"],
                         {"lat": '38.971669',
                          "lng": '-95.23525',
                          "tz": 'America/Chicago',
                          "utc": '-6.0',
                          "city": 'Kirkland',
                          "state": 'Washington',
                          "country": "United States"})

    def test_update_user_profile(self):
        from neon_utils.user_utils import update_user_profile
        from ovos_utils.messagebus import FakeBus

        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        os.environ["NEON_CONFIG_PATH"] = test_config_dir
        os.environ["XDG_CONFIG_HOME"] = test_config_dir
        from neon_utils.user_utils import get_default_user_config
        user_config = get_default_user_config()
        user_config["user"]["username"] = "test_user"
        username = user_config["user"]["username"]
        self.assertIsInstance(user_config, dict)
        new_email = "developers@neon.ai"

        test_message = Message("test", {}, {"user_profiles": [user_config],
                                            "username": username})
        update_message = None
        updated = Event()
        bus = FakeBus()

        def _handle_update(message):
            nonlocal update_message
            update_message = message
            updated.set()
        bus.on("neon.profile_update", _handle_update)

        updated.clear()
        update_user_profile({"user": {"email": new_email}}, test_message, bus)
        self.assertEqual(
            test_message.context["user_profiles"][0]["user"]["email"],
            new_email)
        updated.wait(5)
        self.assertIsInstance(update_message, Message)
        self.assertEqual(test_message.context["user_profiles"][0],
                         update_message.data["profile"])
        self.assertEqual(update_message.data["profile"]["user"]["username"],
                         "test_user")

        valid_profile = deepcopy(update_message.data["profile"])
        updated.clear()
        update_user_profile({"invalid_key": {},
                             "user": {"invalid_key": "val"}},
                            test_message, bus)
        self.assertEqual(test_message.context["user_profiles"][0],
                         valid_profile)
        updated.wait(5)
        self.assertEqual(update_message.data["profile"], valid_profile)

    def test_update_default_config_on_profile_creation(self):
        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        os.environ["NEON_CONFIG_PATH"] = test_config_dir
        os.environ["XDG_CONFIG_HOME"] = test_config_dir
        import importlib
        from neon_utils.configuration_utils import get_neon_user_config
        from neon_utils import user_utils
        importlib.reload(user_utils)
        from neon_utils.user_utils import get_default_user_config
        user_config = get_default_user_config()
        self.assertFalse(os.path.isfile(os.path.join(test_config_dir,
                                                     "ngi_user_info.yml")))
        self.assertIsInstance(user_config, dict)

        from neon_utils.user_utils import update_user_profile, \
            apply_local_user_profile_updates
        from ovos_utils.messagebus import FakeBus
        bus = FakeBus()

        def on_profile_update(msg):
            # Mock behavior handled in IntentService
            updated_profile = msg.data.get("profile")
            apply_local_user_profile_updates(updated_profile,
                                             get_neon_user_config())

        bus.on("neon.profile_update", on_profile_update)
        local_user = get_neon_user_config()
        local_user['user']['username'] = 'local'
        message = Message("test", {}, {"username": local_user['user']['username'],
                                       "user_profiles": [local_user.content]})
        update_user_profile({"user": {"first_name": "Test",
                                      "last_name": "User"}}, message, bus)

        self.assertEqual(get_default_user_config()['user']['first_name'],
                         'Test')
        self.assertEqual(get_default_user_config()['user']['last_name'], 'User')

        os.remove(local_user.file_path)
        os.environ.pop("NEON_CONFIG_PATH")
        os.environ.pop("XDG_CONFIG_HOME")

    def test_apply_user_profile_updates(self):
        from neon_utils.user_utils import apply_local_user_profile_updates
        from neon_utils.configuration_utils import NGIConfig
        config_object = NGIConfig("test_config", os.path.dirname(__file__))
        config_object["test"] = {"updated": "",
                                 "unchanged": True
                                 }

        apply_local_user_profile_updates({"test": {"updated": "yes",
                                             "added": 1}}, config_object)
        self.assertEqual(dict(config_object.content),
                         {"test": {"updated": "yes",
                                   "unchanged": True,
                                   "added": 1}})
        self.assertFalse(config_object._pending_write)
        os.remove(os.path.join(config_object.path,
                               f".{config_object.name}.tmp"))
        os.remove(config_object.file_path)

    def test_get_default_user_config(self):
        from neon_utils.user_utils import get_default_user_config
        import neon_utils.user_utils
        neon_utils.user_utils._DEFAULT_USER_CONFIG = None
        user_config = get_default_user_config()
        self.assertEqual(set(user_config.keys()),
                         {'user', 'brands', 'location', 'units', 'speech',
                          'response_mode', 'privacy'})
        self.assertEqual(set(user_config['location'].keys()),
                         {'lat', 'lng', 'city', 'state', 'country', 'tz',
                          'utc'})

    @patch("ovos_config.config.Configuration")
    def test_get_user_prefs_heals_null_location(self, config):
        from ovos_config.models import LocalConf
        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        config.return_value = LocalConf(join(test_config_dir, "mycroft",
                                             "mycroft.conf"))
        import importlib
        from neon_utils import user_utils
        importlib.reload(user_utils)
        from neon_utils.user_utils import get_user_prefs

        null_location_profile = {
            "user": {"username": "null_location_user"},
            "location": {"lat": None, "lng": None, "city": None,
                         "state": None, "country": None, "tz": None,
                         "utc": None}}
        prefs = get_user_prefs(Message("test_message", {}, {
            "username": "null_location_user",
            "user_profiles": [null_location_profile]}))
        self.assertEqual(prefs["location"],
                         {"lat": '38.971669',
                          "lng": '-95.23525',
                          "tz": 'America/Chicago',
                          "utc": '-6.0',
                          "city": 'Kirkland',
                          "state": 'Washington',
                          "country": "United States"})

    @patch("ovos_config.config.Configuration")
    def test_get_user_prefs_keeps_configured_location(self, config):
        from ovos_config.models import LocalConf
        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        config.return_value = LocalConf(join(test_config_dir, "mycroft",
                                             "mycroft.conf"))
        import importlib
        from neon_utils import user_utils
        importlib.reload(user_utils)
        from neon_utils.user_utils import get_user_prefs

        user_location_profile = {
            "user": {"username": "located_user"},
            "location": {"lat": '29.4241', "lng": '-98.4936',
                         "city": 'San Antonio', "state": 'Texas',
                         "country": "United States", "tz": 'America/Chicago',
                         "utc": '-6.0'}}
        prefs = get_user_prefs(Message("test_message", {}, {
            "username": "located_user",
            "user_profiles": [user_location_profile]}))
        self.assertEqual(prefs["location"]["city"], 'San Antonio')
        self.assertEqual(prefs["location"]["lat"], '29.4241')
        self.assertEqual(prefs["location"]["state"], 'Texas')

    @patch("ovos_config.config.Configuration")
    def test_get_user_prefs_heals_null_outside_location(self, config):
        from ovos_config.models import LocalConf
        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        config.return_value = LocalConf(join(test_config_dir, "mycroft",
                                             "mycroft.conf"))
        import importlib
        from neon_utils import user_utils
        importlib.reload(user_utils)
        from neon_utils.user_utils import get_user_prefs, \
            get_default_user_config

        # A null anywhere in the profile inherits its configured default
        null_profile = {"user": {"username": "null_prefs_user",
                                 "email": None},
                        "units": {"measure": None, "date": "YMD"},
                        "speech": {"tts_language": None}}
        prefs = get_user_prefs(Message("test_message", {}, {
            "username": "null_prefs_user",
            "user_profiles": [null_profile]}))
        default = get_default_user_config()
        # These defaults are non-null, so the null cannot have survived
        self.assertEqual(prefs["units"]["measure"],
                         default["units"]["measure"])
        self.assertEqual(prefs["speech"]["tts_language"],
                         default["speech"]["tts_language"])
        self.assertIsNotNone(prefs["units"]["measure"])
        self.assertIsNotNone(prefs["speech"]["tts_language"])
        # `user.email` defaults to an empty string, so assert the type changed
        self.assertEqual(prefs["user"]["email"], default["user"]["email"])
        self.assertIsNotNone(prefs["user"]["email"])
        # A non-null value is still preferred over the default
        self.assertEqual(prefs["units"]["date"], "YMD")

    @patch("ovos_config.config.Configuration")
    def test_get_user_prefs_keeps_falsy_values(self, config):
        from ovos_config.models import LocalConf
        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        config.return_value = LocalConf(join(test_config_dir, "mycroft",
                                             "mycroft.conf"))
        import importlib
        from neon_utils import user_utils
        importlib.reload(user_utils)
        from neon_utils.user_utils import get_user_prefs

        # Only null is absent; False, 0, and '' are deliberate user values and
        # must not inherit a truthy default (i.e. a privacy opt-out reverting)
        falsy_profile = {"user": {"username": "falsy_user", "email": ""},
                         "privacy": {"save_audio": False, "save_text": False},
                         "units": {"time": 0}}
        prefs = get_user_prefs(Message("test_message", {}, {
            "username": "falsy_user",
            "user_profiles": [falsy_profile]}))
        self.assertFalse(prefs["privacy"]["save_audio"])
        self.assertFalse(prefs["privacy"]["save_text"])
        self.assertEqual(prefs["user"]["email"], "")
        self.assertEqual(prefs["units"]["time"], 0)

    @patch("ovos_config.config.Configuration")
    def test_get_user_prefs_heals_null_in_message_context(self, config):
        from ovos_config.models import LocalConf
        test_config_dir = os.path.join(os.path.dirname(__file__),
                                       "user_util_test_config")
        config.return_value = LocalConf(join(test_config_dir, "mycroft",
                                             "mycroft.conf"))
        import importlib
        from neon_utils import user_utils
        importlib.reload(user_utils)
        from neon_utils.user_utils import get_user_prefs

        # `get_user_prefs` back-fills the context profile in place, so the
        # healed value must land there too rather than a null being restored
        null_profile = {"user": {"username": "healed_user"},
                        "units": {"measure": None}}
        message = Message("test_message", {}, {
            "username": "healed_user",
            "user_profiles": [null_profile]})
        prefs = get_user_prefs(message)
        self.assertEqual(message.context["user_profiles"][0], prefs)
        self.assertIsNotNone(
            message.context["user_profiles"][0]["units"]["measure"])

    def test_dict_update_keys_preserves_explicit_null(self):
        from neon_utils.configuration_utils import dict_update_keys

        # Skill settings merge through this helper and persist to disk, so a
        # deliberately-nulled setting must not inherit the metadata default
        settings = {"api_key": None, "endpoint": "https://custom"}
        merged = dict_update_keys(settings, {"api_key": "DEFAULT_KEY",
                                             "endpoint": "https://default",
                                             "added_key": "added_value"})
        self.assertIsNone(merged["api_key"])
        self.assertEqual(merged["endpoint"], "https://custom")
        self.assertEqual(merged["added_key"], "added_value")


if __name__ == '__main__':
    unittest.main()
