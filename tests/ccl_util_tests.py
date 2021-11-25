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
