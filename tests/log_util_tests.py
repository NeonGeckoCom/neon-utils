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

import io
import os
import sys
import shutil
import unittest
from time import time, sleep

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.log_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LOG_PATH = os.path.join(ROOT_DIR, "tests", "log_files")


class LogUtilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.makedirs(LOG_PATH, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(LOG_PATH)

    def test_get_log_file(self):
        log = get_logger("test", LOG_PATH)
        test_msg = "This should be in test.log"
        log.debug(test_msg)
        with open(os.path.join(LOG_PATH, "test.log")) as log:
            contents = log.read()
        self.assertTrue(contents.endswith(f"{test_msg}\n"))

    def test_get_log_file_with_stdout(self):
        normal_stdout = sys.stdout
        captured_out = io.StringIO()
        sys.stdout = captured_out
        log = get_logger("test_stdout", LOG_PATH, True)
        test_msg = "This should be in test.log and stdout"
        log.debug(test_msg)
        with open(os.path.join(LOG_PATH, "test_stdout.log")) as log:
            contents = log.read()
        logged = captured_out.getvalue().strip("\n")
        sys.stdout = normal_stdout
        self.assertTrue(contents.endswith(f"{test_msg}\n"))
        self.assertEqual(logged, contents.split("\n")[-2])

    def test_get_log_no_file(self):
        logs = os.listdir(LOG_PATH)
        normal_stdout = sys.stdout
        captured_out = io.StringIO()
        sys.stdout = captured_out
        log = get_logger("terminal_only", "stdout")
        test_msg = "This should be in stdout ONLY"
        log.debug(test_msg)
        logged = captured_out.getvalue().strip("\n")
        sys.stdout = normal_stdout
        self.assertTrue(logged.endswith(test_msg))
        self.assertEqual(logs, os.listdir(LOG_PATH))

    def test_archive_logs_default(self):
        os.makedirs(LOG_PATH, exist_ok=True)
        test_log = os.path.join(LOG_PATH, "to_backup.log")
        with open(test_log, "w+") as f:
            f.write("TEST LOG")
        archive_logs(LOG_PATH)
        for path in os.listdir(LOG_PATH):
            if os.path.isdir(os.path.join(LOG_PATH, path)):
                self.assertTrue(os.path.isfile(os.path.join(LOG_PATH, path, "to_backup.log")))
                return
        self.assertTrue(False)

    def test_archive_logs_specific(self):
        os.makedirs(LOG_PATH, exist_ok=True)
        test_log = os.path.join(LOG_PATH, "to_backup.log")
        with open(test_log, "w+") as f:
            f.write("TEST LOG")
        archive_logs(LOG_PATH, "backup")
        path = os.path.join(LOG_PATH, "backup")
        self.assertTrue(os.path.isfile(os.path.join(LOG_PATH, path, "to_backup.log")))

    def test_remove_old_logs(self):
        os.makedirs(LOG_PATH, exist_ok=True)
        test_log = os.path.join(LOG_PATH, "to_be_removed.log")
        with open(test_log, "w+") as f:
            f.write("TEST LOG")
        archive_logs(LOG_PATH)
        old_log_time = time()
        sleep(1)

        test_log = os.path.join(LOG_PATH, "to_be_retained.log")
        with open(test_log, "w+") as f:
            f.write("TEST LOG")
        archive_logs(LOG_PATH)

        remove_old_logs(LOG_PATH, timedelta(seconds=time() - old_log_time))
        self.assertEqual(len([p for p in os.listdir(LOG_PATH) if os.path.isdir(os.path.join(LOG_PATH, p))]), 1)
        for path in os.listdir(LOG_PATH):
            if os.path.isdir(os.path.join(LOG_PATH, path)):
                self.assertTrue(os.path.isfile(os.path.join(LOG_PATH, path, "to_be_retained.log")))
                return

    def test_get_log_file_for_module(self):
        self.assertEqual("voice.log", os.path.basename(get_log_file_for_module("neon_speech_client")))
        self.assertEqual("voice.log", os.path.basename(get_log_file_for_module("neon_speech")))
        self.assertEqual("bus.log", os.path.basename(get_log_file_for_module(["python3", "-m",
                                                                              "mycroft.messagebus.service"])))
        self.assertEqual("bus.log", os.path.basename(get_log_file_for_module("neon_messagebus_service")))
        self.assertEqual("skills.log", os.path.basename(get_log_file_for_module("mycroft.skills")))
        self.assertEqual("skills.log", os.path.basename(get_log_file_for_module("neon_skills_service")))
        self.assertEqual("gui.log", os.path.basename(get_log_file_for_module("mycroft-gui-app")))
        self.assertEqual("display.log", os.path.basename(get_log_file_for_module("neon_gui_service")))
        self.assertEqual("display.log", os.path.basename(get_log_file_for_module("neon_core.gui")))

        self.assertEqual("extras.log", os.path.basename(get_log_file_for_module("NGI.gui")))
        self.assertEqual("extras.log", os.path.basename(get_log_file_for_module("nothing")))


if __name__ == '__main__':
    unittest.main()
