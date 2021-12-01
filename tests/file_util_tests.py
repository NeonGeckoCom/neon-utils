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

import unittest
from pydub.exceptions import CouldntDecodeError

from neon_utils.file_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
AUDIO_PATH = os.path.join(ROOT_DIR, "tests", "audio_files")
README_PATH = os.path.join(ROOT_DIR, "tests", "readme_files")


class FileUtilTests(unittest.TestCase):

    __audio_data = None

    def test_encode_file(self):
        byte_string = encode_file_to_base64_string(os.path.join(ROOT_DIR, "LICENSE.md"))
        self.assertIsInstance(byte_string, str)

    def test_write_encoded_file(self):
        byte_string = encode_file_to_base64_string(os.path.join(ROOT_DIR, "LICENSE.md"))
        output_path = os.path.join(ROOT_DIR, "tests", "LICENSE.md")
        output_file = decode_base64_string_to_file(byte_string, output_path)
        self.assertEqual(output_path, output_file)
        with open(os.path.join(ROOT_DIR, "LICENSE.md"), "r") as original:
            original_text = original.read()
        with open(output_file, "r") as duplicated:
            duplicate_text = duplicated.read()
        self.assertEqual(original_text, duplicate_text)
        os.remove(output_file)

    def test_get_most_recent_file_in_dir(self):
        newest = get_most_recent_file_in_dir(ROOT_DIR)
        self.assertIsInstance(newest, str)
        print(newest)
        self.assertTrue(os.path.exists(newest))

        newest_py = get_most_recent_file_in_dir(os.path.join(ROOT_DIR, "*.py"))
        self.assertIsInstance(newest_py, str)
        self.assertTrue(os.path.isfile(newest_py))

        newest_dne = get_most_recent_file_in_dir(os.path.join(ROOT_DIR, "*.fake"))
        self.assertIsNone(newest_dne)

    def test_get_most_recent_file_in_dir_with_ext(self):
        newest = get_most_recent_file_in_dir(ROOT_DIR, "py")
        self.assertTrue(os.path.isfile(newest))

        newest_dne = get_most_recent_file_in_dir(ROOT_DIR, "fake")
        self.assertIsNone(newest_dne)

    def test_get_wav_as_wav(self):
        test_file = os.path.join(AUDIO_PATH, "testing 1 2 3.wav")
        wav_data = get_file_as_wav(test_file, 16000)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 16000)

        wav_data = get_file_as_wav(test_file, 44100)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 44100)

    def test_file_stream_wav(self):
        test_file = os.path.join(AUDIO_PATH, "stop.wav")
        stream = get_audio_file_stream(test_file)
        self.assertEqual(stream.sample_rate, 16000)

        stream = get_audio_file_stream(test_file, 44100)
        self.assertEqual(stream.sample_rate, 44100)

    def test_get_mp3_as_wav(self):
        test_file = os.path.join(AUDIO_PATH, "testing 1 2 3.mp3")
        wav_data = get_file_as_wav(test_file, 16000)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 16000)

        wav_data = get_file_as_wav(test_file, 44100)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 44100)

    def test_file_stream_mp3(self):
        test_file = os.path.join(AUDIO_PATH, "testing 1 2 3.mp3")
        stream = get_audio_file_stream(test_file)
        self.assertEqual(stream.sample_rate, 16000)

        stream = get_audio_file_stream(test_file, 44100)
        self.assertEqual(stream.sample_rate, 44100)

    def test_get_flac_as_wav(self):
        test_file = os.path.join(AUDIO_PATH, "testing 1 2 3.flac")
        wav_data = get_file_as_wav(test_file, 16000)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 16000)

        wav_data = get_file_as_wav(test_file, 44100)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 44100)

    def test_file_stream_flac(self):
        test_file = os.path.join(AUDIO_PATH, "testing 1 2 3.flac")
        stream = get_audio_file_stream(test_file)
        self.assertEqual(stream.sample_rate, 16000)

        stream = get_audio_file_stream(test_file, 44100)
        self.assertEqual(stream.sample_rate, 44100)

    def test_get_ogg_as_wav(self):
        test_file = os.path.join(AUDIO_PATH, "testing 1 2 3.ogg")
        wav_data = get_file_as_wav(test_file, 16000)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 16000)

        wav_data = get_file_as_wav(test_file, 44100)
        self.assertIsInstance(wav_data, wave.Wave_read)
        self.assertEqual(wav_data.getframerate(), 44100)

    def test_file_stream_ogg(self):
        test_file = os.path.join(AUDIO_PATH, "testing 1 2 3.ogg")
        stream = get_audio_file_stream(test_file)
        self.assertEqual(stream.sample_rate, 16000)

        stream = get_audio_file_stream(test_file, 44100)
        self.assertEqual(stream.sample_rate, 44100)

    def test_file_stream_invalid_path(self):
        with self.assertRaises(FileNotFoundError):
            get_audio_file_stream(os.path.join(AUDIO_PATH, "nothing"))

    def test_file_stream_invalid_type(self):
        with self.assertRaises(Exception):
            get_audio_file_stream(os.path.join(ROOT_DIR, "README.md"))

    def test_invalid_path_as_wav(self):
        with self.assertRaises(FileNotFoundError):
            get_file_as_wav(os.path.join(AUDIO_PATH, "nothing"), 44100)

    def test_invalid_file_as_wav(self):
        with self.assertRaises(CouldntDecodeError):
            get_file_as_wav(os.path.join(ROOT_DIR, "README.md"), 44100)

    def test_get_file_as_wav_no_ext(self):
        wav_data = get_file_as_wav(os.path.join(AUDIO_PATH, "testing 1 2 3"), 44100)
        self.assertEqual(wav_data.getframerate(), 44100)
        self.assertEqual(wav_data.getsampwidth(), 2)

    def test_get_file_as_wav_change_width(self):
        wav_data = get_file_as_wav(os.path.join(AUDIO_PATH, "testing 1 2 3 (sr4).wav"), 44100)
        self.assertEqual(wav_data.getframerate(), 44100)
        self.assertEqual(wav_data.getsampwidth(), 2)

    def test_resolve_neon_resource_file_valid(self):
        start_listening = resolve_neon_resource_file("snd/start_listening.wav")
        self.assertTrue(os.path.isfile(start_listening))

    def test_resolve_neon_resource_file_invalid(self):
        self.assertIsNone(resolve_neon_resource_file("invalid/file"))

    def test_01_audio_bytes_from_file(self):
        test_path = "testing 1 2 3 (sw4).wav"
        audio_data = audio_bytes_from_file(os.path.join(AUDIO_PATH, test_path))
        self.assertIsInstance(audio_data, dict)
        self.__class__.__audio_data = audio_data
        self.assertTrue(len(audio_data.get('data', [])) > 0)

    def test_02_audio_bytes_to_file(self):
        output_file = "testing output 1 2 3 (sr4).wav"
        self.assertIsNotNone(self.__class__.__audio_data)
        audio_path = audio_bytes_to_file(os.path.join(AUDIO_PATH, output_file),
                                         audio_data=self.__audio_data['data'],
                                         sample_rate=self.__audio_data['sample_rate'])
        self.assertTrue(os.path.exists(audio_path))
        os.remove(audio_path)
        self.assertFalse(os.path.exists(audio_path))

    def test_parse_neon_skill_readme_file_valid(self):
        str_sections = ("title", "icon", "summary", "description", "contact support", "category")
        list_sections = ("examples", "credits", "categories", "tags")
        neon_data = parse_skill_readme_file(os.path.join(README_PATH, "neon_readme.md"))
        self.assertIsInstance(neon_data, dict)
        self.assertEqual(set(neon_data.keys()), {"title", "icon", "summary", "description", "examples",
                                                 "contact support", "credits", "category", "tags", "categories"})

        for val in neon_data.values():
            if val in str_sections:
                self.assertIsInstance(val, str)
            elif val in list_sections:
                self.assertIsInstance(val, list)

        self.assertEqual(neon_data["title"], "Demo")
        self.assertEqual(neon_data["icon"], "https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png")
        self.assertEqual(neon_data["summary"], "Skill to demo Neon capabilities")
        self.assertEqual(neon_data["description"],
                         "The demo skill will prompt on first run if you'd like to see a demo. User may accept or "
                         "decline and optionally choose to be asked again on next run. The demo may also be run at "
                         "any time via intent.")
        self.assertEqual(neon_data["contact support"],
                         "Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub]"
                         "(https://help.github.com/en/articles/creating-an-issue)")
        self.assertEqual(neon_data["category"], "Information")

        self.assertEqual(neon_data["examples"], ["show me the demo"])
        self.assertEqual(set(neon_data["credits"]), {"NeonGeckoCom", "NeonDaniel"})
        self.assertEqual(neon_data["categories"], ["Information"])
        self.assertEqual(neon_data["tags"], ["NeonGecko", "NeonAI", "Demo"])

        for readme in ("legacy_neon_readme.md", "complex_neon_readme.md"):
            neon_data = parse_skill_readme_file(os.path.join(README_PATH, readme))
            self.assertIsInstance(neon_data, dict)
            for val in neon_data.values():
                if val in str_sections:
                    self.assertIsInstance(val, str)
                elif val in list_sections:
                    self.assertIsInstance(val, list)

    def test_parse_skill_readme_file_invalid(self):
        with self.assertRaises(FileNotFoundError):
            parse_skill_readme_file(os.path.join(README_PATH, "invalid_path"))

        with self.assertRaises(FileNotFoundError):
            parse_skill_readme_file(README_PATH)

        with self.assertRaises(ValueError):
            parse_skill_readme_file("")


if __name__ == '__main__':
    unittest.main()
