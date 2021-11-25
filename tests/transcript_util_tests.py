# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
