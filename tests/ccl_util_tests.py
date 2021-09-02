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

import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.ccl_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEST_PATH = os.path.join(ROOT_DIR, "tests", "ccl_files")


class CclUtilTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.path.isfile(os.path.join(TEST_PATH, "test.ncs")):
            os.remove(os.path.join(TEST_PATH, "test.ncs"))

    def test_parse_nct_to_ncs_valid(self):
        parse_nct_to_ncs(os.path.join(TEST_PATH, "test.nct"))
        self.assertTrue(os.path.isfile(os.path.join(TEST_PATH, "test.ncs")))

    def test_parse_nct_to_ncs_overwrite_existing(self):
        parse_nct_to_ncs(os.path.join(TEST_PATH, "test.nct"))
        with self.assertRaises(FileExistsError):
            parse_nct_to_ncs(os.path.join(TEST_PATH, "test.nct"))
        parse_nct_to_ncs(os.path.join(TEST_PATH, "test.nct"), overwrite_existing=True)

    def test_parse_nct_to_ncs_invalid_input_path(self):
        with self.assertRaises(FileNotFoundError):
            parse_nct_to_ncs("test.nct")
        with self.assertRaises(ValueError):
            parse_nct_to_ncs(os.path.join(TEST_PATH, "empty.ncs"))

    def test_parse_nct_to_ncs_invalid_output_path(self):
        with self.assertRaises(ValueError):
            parse_nct_to_ncs(os.path.join(TEST_PATH, "test.nct"), os.path.join(TEST_PATH, "test.out"))

    def test_parse_text_to_ncs_valid(self):
        with open(os.path.join(TEST_PATH, "test.nct")) as f:
            text = f.read()
        parse_text_to_ncs(text, os.path.join(TEST_PATH, "test.ncs"))
        self.assertTrue(os.path.isfile(os.path.join(TEST_PATH, "test.ncs")))

    def test_parse_text_to_ncs_overwrite_existing(self):
        with open(os.path.join(TEST_PATH, "test.nct")) as f:
            text = f.read()
        parse_text_to_ncs(text, os.path.join(TEST_PATH, "test.ncs"))
        with self.assertRaises(FileExistsError):
            parse_text_to_ncs(text, os.path.join(TEST_PATH, "test.ncs"))
        parse_text_to_ncs(text, os.path.join(TEST_PATH, "test.ncs"), overwrite_existing=True)

    def test_load_ncs_file_valid(self):
        parse_nct_to_ncs(os.path.join(TEST_PATH, "test.nct"))
        parsed = load_ncs_file(os.path.join(TEST_PATH, "test.ncs"))
        self.assertIsInstance(parsed, dict)

    def test_load_ncs_file_invalid(self):
        with self.assertRaises(FileNotFoundError):
            load_ncs_file(os.path.join(TEST_PATH, "test.ncs"))
        with self.assertRaises(ValueError):
            load_ncs_file(os.path.join(TEST_PATH, "test.nct"))
        with self.assertRaises(ValueError):
            load_ncs_file(os.path.join(TEST_PATH, "empty.ncs"))


if __name__ == '__main__':
    unittest.main()
