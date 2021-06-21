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
    def test_clean_quotes_simple(self):
        raw_str = '"this is a double-quoted-string"'
        output = clean_quotes(raw_str)
        self.assertEqual(output, "this is a double-quoted-string")

        raw_str = 'this has a trailing double quote"'
        output = clean_quotes(raw_str)
        self.assertEqual(raw_str, output)

        raw_str = '"this has a leading double quote'
        output = clean_quotes(raw_str)
        self.assertEqual(raw_str, output)

    def test_clean_quotes_foreign(self):
        raw_str = '「this has Japanese quotes」'
        output = clean_quotes(raw_str)
        self.assertEqual(output, "this has Japanese quotes")

        raw_str = "«this has French quotes»"
        output = clean_quotes(raw_str)
        self.assertEqual(output, "this has French quotes")

    def test_clean_quotes_error_null(self):
        with self.assertRaises(ValueError):
            clean_quotes(None)

    def test_clean_quotes_error_type(self):
        with self.assertRaises(TypeError):
            clean_quotes(["list"])
        with self.assertRaises(TypeError):
            clean_quotes(123)

    def test_normalize_spoken_string_valid(self):
        valid_string = "hello."
        self.assertEqual(normalize_string_to_speak(valid_string), valid_string)
        valid_string = "hello?"
        self.assertEqual(normalize_string_to_speak(valid_string), valid_string)
        valid_string = "hello!"
        self.assertEqual(normalize_string_to_speak(valid_string), valid_string)
        valid_string = "hello..."
        self.assertEqual(normalize_string_to_speak(valid_string), valid_string)

    def test_normalize_spoken_string_add_punctuation(self):
        invalid_string = "hello"
        self. assertEqual(normalize_string_to_speak(invalid_string), f"{invalid_string}.")

    def test_normalize_spoken_string_error_null(self):
        with self.assertRaises(ValueError):
            normalize_string_to_speak(None)

    def test_normalize_spoken_string_error_type(self):
        with self.assertRaises(TypeError):
            normalize_string_to_speak(["list"])
        with self.assertRaises(TypeError):
            normalize_string_to_speak(123)

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

    def test_get_phonemes(self):
        wake_word = "Hey Neon"
        phonemes = get_phonemes(wake_word)
        self.assertEqual(phonemes, "HH EY . N IY AA N .")

        phonemes = get_phonemes("okay")
        self.assertEqual(phonemes, "OW K EY .")

    def test_format_speak_tags_with_speech(self):
        valid_output = "<speak>Speak This.</speak>"
        no_tags = format_speak_tags("Speak This.")
        self.assertEqual(no_tags, valid_output)

        leading_only = format_speak_tags("<speak>Speak This.")
        self.assertEqual(leading_only, valid_output)

        leading_with_exclusion = format_speak_tags("Nope.<speak>Speak This.")
        self.assertEqual(leading_with_exclusion, valid_output)

        trailing_only = format_speak_tags("Speak This.</speak>")
        self.assertEqual(trailing_only, valid_output)

        trailing_with_exclusion = format_speak_tags("Speak This.</speak> But not this.")
        self.assertEqual(trailing_with_exclusion, valid_output)

        tagged = format_speak_tags("<speak>Speak This.</speak>")
        self.assertEqual(tagged, valid_output)

        tagged_with_exclusion = format_speak_tags("Don't<speak>Speak This.</speak>But Not this.")
        self.assertEqual(tagged_with_exclusion, valid_output)

    def test_format_speak_tags_empty(self):
        leading_closure = format_speak_tags("</speak>hello.")
        self.assertFalse(leading_closure)

        trailing_open = format_speak_tags("hello.<speak>")
        self.assertFalse(trailing_open)

    def test_format_speak_tags_with_speech_no_tags(self):
        valid_output = "Speak This."
        no_tags = format_speak_tags("Speak This.", False)
        self.assertEqual(no_tags, valid_output)

        leading_only = format_speak_tags("<speak>Speak This.", False)
        self.assertEqual(leading_only, valid_output)

        leading_with_exclusion = format_speak_tags("Nope.<speak>Speak This.", False)
        self.assertEqual(leading_with_exclusion, valid_output)

        trailing_only = format_speak_tags("Speak This.</speak>", False)
        self.assertEqual(trailing_only, valid_output)

        trailing_with_exclusion = format_speak_tags("Speak This.</speak> But not this.", False)
        self.assertEqual(trailing_with_exclusion, valid_output)

        tagged = format_speak_tags("<speak>Speak This.</speak>", False)
        self.assertEqual(tagged, valid_output)

        tagged_with_exclusion = format_speak_tags("Don't<speak>Speak This.</speak>But Not this.", False)
        self.assertEqual(tagged_with_exclusion, valid_output)


if __name__ == '__main__':
    unittest.main()
