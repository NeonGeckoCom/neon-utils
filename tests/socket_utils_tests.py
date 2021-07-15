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
from neon_utils.socket_utils import *

TEST_DICT = {b"section 1": {"key1": "val1",
                            "key2": "val2"},
             "section 2": {"key_1": b"val1",
                           "key_2": f"val2"}}

TEST_DICT_B64 = b'IntiJ3NlY3Rpb24gMSc6IHsna2V5MSc6ICd2YWwxJywgJ2tleTInOiAndmFsMid9LCAnc2VjdGlvbiAyJzogeydrZXlfMSc6IGIndmFsMScsICdrZXlfMic6ICd2YWwyJ319Ig=='


class SocketUtilsTest(unittest.TestCase):

    def test_01_dict_to_b64(self):
        b64_str = dict_to_b64(TEST_DICT)
        self.assertIsInstance(b64_str, bytes)
        self.assertTrue(len(b64_str) > 0)
        self.assertEqual(b64_str, TEST_DICT_B64)

    def test_02_b64_to_dict(self):
        result_dict = b64_to_dict(TEST_DICT_B64)
        self.assertIsInstance(result_dict, dict)
        self.assertTrue(len(list(result_dict)) > 0)
        self.assertEqual(result_dict, TEST_DICT)
