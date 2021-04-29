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
from datetime import date

import time
import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.transcript_utils import *

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "transcripts")


class TranscriptUtilTests(unittest.TestCase):
    def test_get_likes(self):
        selected_ts = os.path.join(TRANSCRIPTS_DIR, "csv_files", "selected_ts.csv")
        self.assertTrue(os.path.isfile(selected_ts), f"{selected_ts} FNF!")
        demo_likes = get_likes_from_csv(selected_ts, "DemoTest", date_limit=None)
        all_likes = get_likes_from_csv(selected_ts, None, date_limit=None)
        self.assertIsInstance(demo_likes, dict)
        self.assertIsInstance(all_likes, dict)
        self.assertIn("neon", demo_likes, demo_likes)
        self.assertIn("neon", all_likes, all_likes)
        self.assertGreater(len(all_likes["neon"]), len(demo_likes["neon"]))

    def test_invalid_get_likes(self):
        invalid_likes = get_likes_from_csv(os.path.join(TRANSCRIPTS_DIR, "csv_files", "selected_ts.csv"), "InvalidUser")
        self.assertIsInstance(invalid_likes, dict)
        self.assertDictEqual(invalid_likes, dict())

    def test_get_transcript_file(self):
        valid_user = get_transcript_file(TRANSCRIPTS_DIR, "running_out_transcripts", "DemoTest", "2021-02-08")
        valid_all = get_transcript_file(TRANSCRIPTS_DIR, "running_out_transcripts", None, "2021-02-08")
        self.assertIsInstance(valid_user, str)
        self.assertIsInstance(valid_all, str)
        self.assertTrue(os.path.isfile(valid_user))
        self.assertTrue(os.path.isfile(valid_all))

    def test_invalid_get_transcript_file(self):
        invalid_user = get_transcript_file(TRANSCRIPTS_DIR, "running_out_transcripts", "DemoTest", "2021-02-07")
        invalid_all = get_transcript_file(TRANSCRIPTS_DIR, "running_out_transcripts", None, "2021-02-07")
        self.assertIsNone(invalid_user)
        self.assertIsNone(invalid_all)

    def test_update_new_csv(self):
        csv_path = os.path.join(TRANSCRIPTS_DIR, "csv_files", "full_ts.csv")
        new_line_data = ["2021-01-01", "00:00:00.000000", "TestRunner", "TestDev", "Test Input Utterance",
                         "TestRunner-2021-01-01", None]
        update_csv(new_line_data, csv_path)
        self.assertTrue(os.path.isfile(csv_path))
        with open(csv_path, "r") as f:
            lines = f.readlines()
        self.assertIn("2021-01-01,00:00:00.000000,TestRunner,TestDev,Test Input Utterance,TestRunner-2021-01-01,\n",
                      lines)
        self.assertEqual("Date,Time,Profile,Device,Input,Location,Wav_Length\n", lines[0])
        os.remove(csv_path)

    def test_write_transcript_file(self):
        line = write_transcript_file("test utterance", TRANSCRIPTS_DIR, "test_transcripts", "TestRunner", time.time())
        self.assertIsInstance(line, str)
        self.assertTrue(os.path.isfile(os.path.join(TRANSCRIPTS_DIR, "test_transcripts",
                                                    str(date.fromtimestamp(time.time())) + ".txt")))

    def test_write_transcript_file_relative_path(self):
        line = write_transcript_file("test utterance", "~/.local/share/neon", "test_transcripts", "TestRunner",
                                     time.time())
        self.assertIsInstance(line, str)
        self.assertTrue(os.path.isfile(os.path.expanduser(
            os.path.join("~/.local/share/neon", "test_transcripts", str(date.fromtimestamp(time.time())) + ".txt"))))


if __name__ == '__main__':
    unittest.main()
