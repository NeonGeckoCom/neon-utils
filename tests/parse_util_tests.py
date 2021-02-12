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
from neon_utils.parse_utils import *


class ParseUtilTests(unittest.TestCase):
    def test_quote_cleaning_simple(self):
        raw_str = '"this is a double-quoted-string"'
        output = clean_quotes(raw_str)
        self.assertEqual(output, "this is a double-quoted-string")

        raw_str = 'this has a trailing double quote"'
        output = clean_quotes(raw_str)
        self.assertEqual(raw_str, output)

        raw_str = '"this has a leading double quote'
        output = clean_quotes(raw_str)
        self.assertEqual(raw_str, output)

    def test_special_quote(self):
        raw_str = '「this has Japanese quotes」'
        output = clean_quotes(raw_str)
        self.assertEqual(output, "this has Japanese quotes")

        raw_str = "«this has French quotes»"
        output = clean_quotes(raw_str)
        self.assertEqual(output, "this has French quotes")

    def test_clean_filename(self):
        raw_filename = "'My*Weird~Filename I want to use?__'"
        cleaned = clean_filename(raw_filename)
        self.assertEqual(cleaned, "'My_Weird_Filename I want to use___'")
        lowered = clean_filename(raw_filename, True)
        self.assertEqual(lowered, cleaned.lower())

    def test_clean_transcription(self):
        raw_input = "50% is acceptable-ish. Right?"
        cleaned_input = clean_transcription(raw_input)
        self.assertEqual(cleaned_input, "50 percent is acceptable ish  right")


if __name__ == '__main__':
    unittest.main()
