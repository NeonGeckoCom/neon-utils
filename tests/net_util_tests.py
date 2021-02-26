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
from neon_utils.net_utils import *


class NetUtilTests(unittest.TestCase):
    def test_get_ip_address(self):
        ip_addr = get_ip_address()
        self.assertIsInstance(ip_addr, str)

    def test_get_adapter_info(self):
        try:
            info = get_adapter_info()
            self.assertIsInstance(info, dict)
            self.assertIsInstance(info.get("mac"), str)
            self.assertEqual(len(info["mac"]), 17)
            self.assertIsInstance(info.get("ipv4"), str)
            self.assertEqual(len(info["ipv4"].split('.')), 4)
            self.assertIsInstance(info.get("ipv6"), str)
            print(info["ipv6"])
            self.assertGreater(info["ipv6"].count(':'), 3)
        except IndexError:
            print("No Connection")

    def test_get_adapter_fail(self):
        with self.assertRaises(IndexError):
            get_adapter_info("FAIL")


if __name__ == '__main__':
    unittest.main()
