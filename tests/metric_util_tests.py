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
from time import sleep

import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.metrics_utils import *


class MetricUtilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["NEON_CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "configuration")

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("NEON_CONFIG_PATH")

    def test_stopwatch_simple(self):
        sleep_time = 1.00
        stopwatch = Stopwatch()
        with stopwatch:
            sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

    def test_stopwatch_reuse(self):
        sleep_time = 0.5
        stopwatch = Stopwatch()
        with stopwatch:
            sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

        with stopwatch:
            sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

        with stopwatch:
            sleep(sleep_time)
        self.assertEqual(round(stopwatch.time, 2), sleep_time)

    def test_stopwatch_init_params(self):
        stopwatch = Stopwatch("Test", True)
        self.assertEqual(stopwatch._metric, "Test")
        self.assertTrue(stopwatch._report)

        stopwatch = Stopwatch()
        self.assertIsNone(stopwatch._metric)
        self.assertFalse(stopwatch._report)

    def test_report_metric(self):
        self.assertTrue(report_metric("test", data="this is only a test"))

    def test_announce_connection(self):
        self.assertTrue(report_connection())


if __name__ == '__main__':
    unittest.main()
