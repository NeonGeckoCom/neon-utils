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
