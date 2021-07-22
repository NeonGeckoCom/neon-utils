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

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from tests.skills.test_objects import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils import *


class TestSkillPatching(unittest.TestCase):
    def test_skill_needs_patching(self):
        self.assertTrue(skill_needs_patching(MycroftSkill()))
        self.assertFalse(skill_needs_patching(NeonSkill()))

    def test_patch_skill(self):
        skill = MycroftSkill()
        stub_missing_parameters(skill)
        self.assertTrue(hasattr(skill, "server"))
        self.assertFalse(skill.neon_core)
        self.assertIsInstance(skill.gui_enabled, bool)


if __name__ == '__main__':
    unittest.main()
