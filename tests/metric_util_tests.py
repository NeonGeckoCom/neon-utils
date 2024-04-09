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

from time import sleep

import sys
import os
import unittest
from unittest.mock import Mock

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

        stopwatch = Stopwatch()
        stopwatch.stop()
        self.assertIsNone(stopwatch.time)

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

    def test_stopwatch_report_metric(self):
        from ovos_utils.messagebus import FakeBus
        bus = FakeBus()
        on_metric = Mock()
        bus.on("neon.metric", on_metric)
        stopwatch = Stopwatch("test", True, bus)
        with stopwatch:
            sleep(0.05)
        on_metric.assert_called_once()
        msg = on_metric.call_args[0][0]
        self.assertEqual(msg.data['name'], "test")
        self.assertIsInstance(msg.data['duration'], float)
        self.assertIsInstance(msg.context['timestamp'], float)

    def test_report_metric(self):
        self.assertTrue(report_metric("test", data="this is only a test"))

    def test_announce_connection(self):
        # TODO: Better test to check call to `send_mq_request`
        self.assertIsInstance(announce_connection(), bool)


if __name__ == '__main__':
    unittest.main()
