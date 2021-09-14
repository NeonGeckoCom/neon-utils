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

import datetime
import os
import sys
import unittest

from multiprocessing import Event
from threading import Thread
from time import sleep
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus
from mock import Mock

from mycroft.skills.fallback_skill import FallbackSkill

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.language_utils import LanguageDetector, LanguageTranslator
from neon_utils.cache_utils import LRUCache
from neon_utils.configuration_utils import NGIConfig
from neon_utils import check_for_signal

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from skills import *

MycroftSkill = PatchedMycroftSkill
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
SKILL_PATH = os.path.join(ROOT_DIR, "skills")


def get_test_mycroft_skill(bus_events: dict):
    skill = MycroftSkill()
    bus = FakeBus()
    for event, callback in bus_events.items():
        bus.on(event, callback)
    bus.run_in_thread()
    skill.bind(bus)
    return skill


class SkillObjectTests(unittest.TestCase):
    def test_common_message_skill_init(self):
        skill = TestCMS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, CommonMessageSkill)
        self.assertEqual(skill.name, "Test Common Message Skill")

    def test_common_play_skill_init(self):
        skill = TestCPS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, CommonPlaySkill)
        self.assertEqual(skill.name, "Test Common Play Skill")

    def test_common_query_skill_init(self):
        skill = TestCQS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, CommonQuerySkill)
        self.assertEqual(skill.name, "Test Common Query Skill")

    def test_fallback_skill_init(self):
        skill = TestFBS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, NeonFallbackSkill)
        self.assertIsInstance(skill, FallbackSkill)
        self.assertEqual(skill.name, "Test Fallback Skill")

    def test_neon_skill_init(self):
        skill = TestNeonSkill()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertEqual(skill.name, "Test Neon Skill")

        self.assertIsInstance(skill.user_config, NGIConfig)
        self.assertIsInstance(skill.local_config, NGIConfig)
        self.assertIsInstance(skill.lru_cache, LRUCache)
        self.assertIsInstance(skill.sys_tz, datetime.tzinfo)
        self.assertIsInstance(skill.gui_enabled, bool)
        self.assertIsInstance(skill.scheduled_repeats, list)  # TODO: What is this param for?
        self.assertIsInstance(skill.server, bool)
        self.assertIsInstance(skill.default_intent_timeout, int)
        self.assertTrue(skill.neon_core)  # TODO: This should be depreciated
        self.assertIsInstance(skill.actions_to_confirm, dict)

        self.assertIsInstance(skill.skill_mode, str)
        self.assertIsInstance(skill.extension_time, int)

        self.assertIsInstance(skill.language_config, dict)
        self.assertIsInstance(skill.lang_detector, LanguageDetector)
        self.assertIsInstance(skill.translator, LanguageTranslator)

        self.assertIsInstance(skill.settings, dict)

        self.assertIsInstance(skill.location_timezone, str)

        self.assertIsInstance(skill.preference_brands(), dict)
        self.assertIsInstance(skill.preference_user(), dict)
        self.assertIsInstance(skill.preference_location(), dict)
        self.assertIsInstance(skill.preference_unit(), dict)
        self.assertIsInstance(skill.preference_speech(), dict)
        self.assertIsInstance(skill.preference_skill(), dict)

        self.assertIsInstance(skill.build_user_dict(), dict)

        self.assertEqual(skill.file_system.path, skill.settings_write_path)
        self.assertNotEqual(os.path.basename(skill.file_system.path), skill.name)

    def test_patched_mycroft_skill_init(self):
        skill = TestPatchedSkill()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertEqual(skill.name, "Test Mycroft Skill")

        self.assertEqual(skill.file_system.path, skill.settings_write_path)
        self.assertNotEqual(os.path.basename(skill.file_system.path), skill.name)


class PatchedMycroftSkillTests(unittest.TestCase):
    def test_get_response_simple(self):
        def handle_speak(_):
            check_for_signal("isSpeaking")
            spoken.set()

        def skill_response_thread(s: MycroftSkill, idx: str):
            resp = s.get_response(test_dialog)
            test_results[idx] = resp

        test_results = dict()
        spoken = Event()
        test_dialog = "testing get response."
        message = Message("recognizer_loop:utterance", {"utterances": ["testing one", "testing 1", "resting one"]},
                          {"timing": {},
                           "username": "local"})

        skill = get_test_mycroft_skill({"speak": handle_speak})
        t = Thread(target=skill_response_thread, args=(skill, message.context["username"]), daemon=True)
        t.start()
        spoken.wait(30)
        sleep(1)
        skill.converse(message)
        t.join(5)
        self.assertEqual(test_results[message.context["username"]], message.data["utterances"][0])

    def test_get_response_multi_user(self):
        def handle_speak(_):
            check_for_signal("isSpeaking")
            spoken.set()

        def skill_response_thread(s: MycroftSkill, idx: str):
            resp = s.get_response(test_dialog, message=Message("converse_message", {},
                                                               {"username": "valid_converse_user"}))
            test_results[idx] = resp

        test_results = dict()
        spoken = Event()
        test_dialog = "testing get response multi user."
        valid_message = Message("recognizer_loop:utterance",
                                {"utterances": ["testing one", "testing 1", "resting one"]},
                                {"timing": {},
                                 "username": "valid_converse_user"})
        invalid_message = Message("recognizer_loop:utterance",
                                  {"utterances": ["invalid return"]},
                                  {"timing": {},
                                   "username": "invalid_converse_user"})

        skill = get_test_mycroft_skill({"speak": handle_speak})
        t = Thread(target=skill_response_thread, args=(skill, valid_message.context["username"]), daemon=True)
        t.start()
        spoken.wait(30)
        sleep(1)
        skill.converse(invalid_message)
        skill.converse(valid_message)
        skill.converse(invalid_message)
        t.join(5)
        self.assertEqual(test_results[valid_message.context["username"]], valid_message.data["utterances"][0])

    def test_get_response_no_response(self):
        def handle_speak(_):
            check_for_signal("isSpeaking")
            spoken.set()

        def skill_response_thread(s: MycroftSkill, idx: str):
            resp = s.get_response(test_dialog, message=Message("converse_message", {},
                                                               {"username": "valid_converse_user"}))
            test_results[idx] = resp

        test_results = dict()
        spoken = Event()
        test_dialog = "testing get response multi user."
        valid_message = Message("recognizer_loop:utterance",
                                {"utterances": ["testing one", "testing 1", "resting one"]},
                                {"timing": {},
                                 "username": "valid_converse_user"})
        invalid_message = Message("recognizer_loop:utterance",
                                  {"utterances": ["invalid return"]},
                                  {"timing": {},
                                   "username": "invalid_converse_user"})

        skill = get_test_mycroft_skill({"speak": handle_speak})
        t = Thread(target=skill_response_thread, args=(skill, valid_message.context["username"]), daemon=True)
        t.start()
        spoken.wait(30)
        sleep(1)
        skill.converse(invalid_message)
        t.join(30)
        self.assertIsNone(test_results[valid_message.context["username"]])

    def test_get_response_validator_pass(self):
        def handle_speak(_):
            check_for_signal("isSpeaking")
            spoken.set()

        def is_valid(_):
            test_results["validator"] = True
            return True

        def skill_response_thread(s: MycroftSkill, idx: str):
            resp = s.get_response(test_dialog, validator=is_valid, message=Message("converse_message", {},
                                                                                   {"username": "valid_converse_user"}))
            test_results[idx] = resp

        test_results = dict()
        spoken = Event()
        test_dialog = "testing get response multi user."
        valid_message = Message("recognizer_loop:utterance",
                                {"utterances": ["testing one", "testing 1", "resting one"]},
                                {"timing": {},
                                 "username": "valid_converse_user"})

        skill = get_test_mycroft_skill({"speak": handle_speak})
        t = Thread(target=skill_response_thread, args=(skill, valid_message.context["username"]), daemon=True)
        t.start()
        spoken.wait(30)
        sleep(1)
        skill.converse(valid_message)
        t.join(30)
        self.assertTrue(test_results["validator"])
        self.assertEqual(test_results[valid_message.context["username"]], valid_message.data["utterances"][0])

    def test_get_response_validator_fail(self):
        def handle_speak(_):
            check_for_signal("isSpeaking")
            spoken.set()

        def is_valid(_):
            test_results["validator"] = True
            return False

        on_fail = Mock()

        def skill_response_thread(s: MycroftSkill, idx: str):
            resp = s.get_response(test_dialog, validator=is_valid, on_fail=on_fail,
                                  message=Message("converse_message", {},
                                                  {"username": "valid_converse_user"}))
            test_results[idx] = resp

        test_results = dict()
        spoken = Event()
        test_dialog = "testing get response multi user."
        valid_message = Message("recognizer_loop:utterance",
                                {"utterances": ["testing one", "testing 1", "resting one"]},
                                {"timing": {},
                                 "username": "valid_converse_user"})

        skill = get_test_mycroft_skill({"speak": handle_speak})
        t = Thread(target=skill_response_thread, args=(skill, valid_message.context["username"]), daemon=True)
        t.start()
        spoken.wait(30)
        sleep(1)
        skill.converse(valid_message)
        t.join(30)
        self.assertTrue(test_results["validator"])
        on_fail.assert_called_once()
        on_fail.assert_called_with("testing one")

    def test_speak_simple_valid(self):
        handle_speak = Mock()
        utterance = "test to speak"
        skill = get_test_mycroft_skill({"speak": handle_speak})
        skill.speak(utterance)
        handle_speak.assert_called_once()
        msg = handle_speak.call_args.args[0]
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.data["utterance"], utterance)
        self.assertEqual(msg.data["expect_response"], False)
        self.assertIsInstance(msg.data["meta"], dict)
        self.assertIsNone(msg.data["speaker"])

    def test_speak_speaker_valid(self):
        handle_speak = Mock()
        utterance = "test to speak"
        speaker = {"speaker": "Test Speaker",
                   "language": "en-au",
                   "gender": "female"}
        skill = get_test_mycroft_skill({"speak": handle_speak})
        skill.speak(utterance, speaker=speaker)
        handle_speak.assert_called_once()
        msg = handle_speak.call_args.args[0]
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.data["utterance"], utterance)
        self.assertEqual(msg.data["expect_response"], False)
        self.assertIsInstance(msg.data["meta"], dict)
        self.assertEqual(msg.data["speaker"], speaker)

    def test_speak_simple_with_message_valid(self):
        message = Message("date-time.neon:handle_query_time", {'intent_type': 'date-time.neon:handle_query_time',
                                                               'target': None,
                                                               'confidence': 0.6666666666666666,
                                                               'utterance': 'what time is it neon'},
                          {'client_name': 'mycroft_cli',
                           'source': ['skills'],
                           'destination': 'debug_cli',
                           'client': 'local',
                           'neon_should_respond': False,
                           'timing': {'transcribed': 1631062887.5719671,
                                      'text_parsers': 0.34954047203063965,
                                      'speech_start': 1631062888.1001909},
                           'audio_file': '',
                           'skill_id': 'date-time.neon'})
        handle_speak = Mock()
        utterance = "test to speak"
        skill = get_test_mycroft_skill({"speak": handle_speak})
        skill.speak(utterance, message=message)
        handle_speak.assert_called_once()
        msg = handle_speak.call_args.args[0]
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.data["utterance"], utterance)
        self.assertEqual(msg.data["expect_response"], False)
        self.assertIsInstance(msg.data["meta"], dict)
        self.assertIsNone(msg.data["speaker"])
        self.assertEqual(message.context.pop("source"), msg.context.pop("destination"))
        self.assertEqual(message.context.pop("destination"), msg.context.pop("source"))
        self.assertEqual(message.context, msg.context)

    def test_speak_speaker_with_message_override_valid(self):
        message = Message("date-time.neon:handle_query_time", {'intent_type': 'date-time.neon:handle_query_time',
                                                               'target': None,
                                                               'confidence': 0.6666666666666666,
                                                               'utterance': 'what time is it neon',
                                                               'speaker': {"speaker": "invalid speaker",
                                                                           "language": "es-es"}},
                          {'client_name': 'mycroft_cli',
                           'source': ['skills'],
                           'destination': 'debug_cli',
                           'client': 'local',
                           'neon_should_respond': False,
                           'timing': {'transcribed': 1631062887.5719671,
                                      'text_parsers': 0.34954047203063965,
                                      'speech_start': 1631062888.1001909},
                           'audio_file': '',
                           'skill_id': 'date-time.neon'})
        handle_speak = Mock()
        utterance = "test to speak"
        speaker = {"speaker": "Test Speaker",
                   "language": "en-au",
                   "gender": "female"}
        skill = get_test_mycroft_skill({"speak": handle_speak})
        skill.speak(utterance, speaker=speaker, message=message)
        handle_speak.assert_called_once()
        msg = handle_speak.call_args.args[0]
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.data["utterance"], utterance)
        self.assertEqual(msg.data["expect_response"], False)
        self.assertIsInstance(msg.data["meta"], dict)
        self.assertEqual(msg.data["speaker"], speaker)
        self.assertEqual(message.context.pop("source"), msg.context.pop("destination"))
        self.assertEqual(message.context.pop("destination"), msg.context.pop("source"))
        self.assertEqual(message.context, msg.context)

    def test_speak_speaker_with_message_valid(self):
        speaker = {"speaker": "Test Speaker",
                   "language": "en-au",
                   "gender": "female"}
        message = Message("date-time.neon:handle_query_time", {'intent_type': 'date-time.neon:handle_query_time',
                                                               'target': None,
                                                               'confidence': 0.6666666666666666,
                                                               'utterance': 'what time is it neon',
                                                               'speaker': speaker},
                          {'client_name': 'mycroft_cli',
                           'source': ['skills'],
                           'destination': 'debug_cli',
                           'client': 'local',
                           'neon_should_respond': False,
                           'timing': {'transcribed': 1631062887.5719671,
                                      'text_parsers': 0.34954047203063965,
                                      'speech_start': 1631062888.1001909},
                           'audio_file': '',
                           'skill_id': 'date-time.neon'})
        handle_speak = Mock()
        utterance = "test to speak"

        skill = get_test_mycroft_skill({"speak": handle_speak})
        skill.speak(utterance, message=message)
        handle_speak.assert_called_once()
        msg = handle_speak.call_args.args[0]
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.data["utterance"], utterance)
        self.assertEqual(msg.data["expect_response"], False)
        self.assertIsInstance(msg.data["meta"], dict)
        self.assertEqual(msg.data["speaker"], speaker)
        self.assertEqual(message.context.pop("source"), msg.context.pop("destination"))
        self.assertEqual(message.context.pop("destination"), msg.context.pop("source"))
        self.assertEqual(message.context, msg.context)

    def test_speak_emit_response_valid(self):
        message = Message("date-time.neon:handle_query_time", {'intent_type': 'date-time.neon:handle_query_time',
                                                               'target': None,
                                                               'confidence': 0.6666666666666666,
                                                               'utterance': 'what time is it neon'},
                          {'client_name': 'mycroft_cli',
                           'source': ['skills'],
                           'destination': 'debug_cli',
                           'client': 'local',
                           'neon_should_respond': False,
                           'timing': {'transcribed': 1631062887.5719671,
                                      'text_parsers': 0.34954047203063965,
                                      'speech_start': 1631062888.1001909},
                           'audio_file': '',
                           'skill_id': 'date-time.neon',
                           "cc_data": {"emit_response": True}})
        handle_execute_response = Mock()
        utterance = "test to speak"

        skill = get_test_mycroft_skill({"skills:execute.response": handle_execute_response})
        skill.speak(utterance, message=message)
        handle_execute_response.assert_called_once()
        msg = handle_execute_response.call_args.args[0]
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.data["utterance"], utterance)
        self.assertEqual(msg.data["expect_response"], False)
        self.assertIsInstance(msg.data["meta"], dict)
        self.assertEqual(message.context.pop("source"), msg.context.pop("destination"))
        self.assertEqual(message.context.pop("destination"), msg.context.pop("source"))
        self.assertEqual(message.context, msg.context)

    # TODO: Test settings load


# TODO: NeonSkill Tests


if __name__ == '__main__':
    unittest.main()
