import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from test_objects import *

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


if __name__ == '__main__':
    unittest.main()
