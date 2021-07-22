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

from mycroft.skills.mycroft_skill.mycroft_skill import MycroftSkill
from mycroft.skills.fallback_skill import FallbackSkill

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.language_utils import LanguageDetector, LanguageTranslator
from neon_utils.cache_utils import LRUCache
from neon_utils.configuration_utils import NGIConfig

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from skills import *

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
SKILL_PATH = os.path.join(ROOT_DIR, "skills")


class SkillObjectTests(unittest.TestCase):
    def test_common_message_skill(self):
        skill = TestCMS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, CommonMessageSkill)
        self.assertEqual(skill.name, "Test Common Message Skill")

    def test_common_play_skill(self):
        skill = TestCPS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, CommonPlaySkill)
        self.assertEqual(skill.name, "Test Common Play Skill")

    def test_common_query_skill(self):
        skill = TestCQS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, CommonQuerySkill)
        self.assertEqual(skill.name, "Test Common Query Skill")

    def test_fallback_skill(self):
        skill = TestFBS()
        self.assertIsInstance(skill, MycroftSkill)
        self.assertIsInstance(skill, NeonSkill)
        self.assertIsInstance(skill, NeonFallbackSkill)
        self.assertIsInstance(skill, FallbackSkill)
        self.assertEqual(skill.name, "Test Fallback Skill")

    def test_neon_skill(self):
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


if __name__ == '__main__':
    unittest.main()
