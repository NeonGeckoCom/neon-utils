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

import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.message_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class MessageUtilTests(unittest.TestCase):
    def test_request_from_mobile(self):
        from_mobile = request_from_mobile(Message("", {}, {"mobile": True}))
        self.assertTrue(from_mobile)

        not_from_mobile = request_from_mobile(Message("", {}, {}))
        self.assertFalse(not_from_mobile)

    def test_get_message_username(self):
        with_user = get_message_user(Message("", {}, {"username": "testrunner"}))
        self.assertEqual(with_user, "testrunner")

        without_user = get_message_user(Message(""))
        self.assertIsNone(without_user)


if __name__ == '__main__':
    unittest.main()
