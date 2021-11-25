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
from neon_utils.packaging_utils import *


class PackagingUtilTests(unittest.TestCase):
    def test_get_neon_core_version(self):
        version = get_neon_core_version()
        self.assertIsInstance(version, str)
        self.assertGreaterEqual(len(version.split('.')), 2)

    def test_get_core_root(self):
        try:
            core_dir = get_core_root()
            self.assertIsInstance(core_dir, str)
            self.assertTrue(os.path.isdir(os.path.join(core_dir, "mycroft")))
        except FileNotFoundError:
            with self.assertRaises(FileNotFoundError):
                get_core_root()

    def test_get_neon_core_root(self):
        try:
            core_dir = get_neon_core_root()
            self.assertIsInstance(core_dir, str)
            self.assertTrue(os.path.isdir(os.path.join(core_dir, "neon_core")))
        except FileNotFoundError:
            with self.assertRaises(FileNotFoundError):
                get_neon_core_root()

    def test_get_mycroft_core_root(self):
        try:
            core_dir = get_mycroft_core_root()
            self.assertIsInstance(core_dir, str)
            self.assertTrue(os.path.isdir(os.path.join(core_dir, "mycroft")))
        except FileNotFoundError:
            with self.assertRaises(FileNotFoundError):
                get_mycroft_core_root()

    def test_get_packaged_core_version(self):
        try:
            ver = get_packaged_core_version()
            self.assertIsInstance(ver, str)
            self.assertGreaterEqual(len(ver.split('.')), 2)
        except ImportError:
            with self.assertRaises(ImportError):
                get_packaged_core_version()

    def test_get_version_from_file(self):
        try:
            ver = get_version_from_file()
            self.assertIsInstance(ver, str)
            self.assertGreaterEqual(len(ver.split('.')), 2)
        except FileNotFoundError:
            with self.assertRaises(FileNotFoundError):
                get_version_from_file()

    # TODO: Actually validate exception cases? DM


if __name__ == '__main__':
    unittest.main()
