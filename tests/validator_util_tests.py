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

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.validator_utils import *


class ValidatorUtilTests(unittest.TestCase):
    def test_numeric_confirmation_validator_valid(self):
        validator = numeric_confirmation_validator("123")
        self.assertTrue(validator("123"))
        self.assertTrue(validator("1 2 3."))
        self.assertTrue(validator("one two three"))
        self.assertTrue(validator("one hundred twenty three"))
        self.assertTrue(validator("blah blah one two three nah"))

        self.assertFalse(validator("one thousand two hundred and three"))
        self.assertFalse(validator("123 4"))

    def test_numeric_confirmation_validator_type_error(self):
        with self.assertRaises(TypeError):
            numeric_confirmation_validator(123)

        with self.assertRaises(ValueError):
            numeric_confirmation_validator("one two three")

        with self.assertRaises(ValueError):
            numeric_confirmation_validator("")

    def test_string_confirmation_validator_valid(self):
        validator = string_confirmation_validator("test phrase")
        self.assertTrue(validator("test phrase"))
        self.assertTrue(validator("yes test phrase yes"))

        self.assertFalse(validator("test no phrase"))
        self.assertFalse(validator("phrase test"))

    def test_string_confirmation_validator_type_error(self):
        with self.assertRaises(TypeError):
            string_confirmation_validator(123)

        with self.assertRaises(ValueError):
            string_confirmation_validator("")

    def test_voc_confirmation_validator_valid(self):
        sys.path.append(os.path.dirname(__file__))
        from valid_skill import ValidNeonSkill
        validator = voc_confirmation_validator("test", ValidNeonSkill())
        self.assertTrue(validator("test"))
        self.assertTrue(validator("something"))

        self.assertFalse(validator("else"))
        self.assertFalse(validator("false"))

    def test_voc_confirmation_validator_type_error(self):
        sys.path.append(os.path.dirname(__file__))
        from valid_skill import ValidNeonSkill
        skill = ValidNeonSkill()
        with self.assertRaises(TypeError):
            voc_confirmation_validator(123, skill)

        with self.assertRaises(FileNotFoundError):
            voc_confirmation_validator("invalid", skill)


if __name__ == '__main__':
    unittest.main()
