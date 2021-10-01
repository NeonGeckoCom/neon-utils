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

from threading import Thread
from tempfile import mkstemp
from time import sleep

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.lock_utils import *


class LockUtilTests(unittest.TestCase):
    def test_multi_lock_acquire(self):
        results = dict()
        _, lock_file = mkstemp()

        def _test_acquire(idx):
            lock = create_master_lock(lock_file)
            success = lock.acquire(False)
            results[idx] = success
            sleep(5)  # Keep the lock held until all threads have run

        for i in range(0, 10):
            Thread(target=_test_acquire, args=(i,), daemon=True).start()

        while not len(results.keys()) == 10:
            sleep(0.5)
        self.assertEqual(len([lock for lock in results.values() if lock]), 1)

    def test_shared_lock_acquire(self):
        results = dict()
        _, lock_file = mkstemp()
        lock = create_master_lock(lock_file)

        def _test_acquire(idx):
            success = lock.acquire(False)
            results[idx] = success
            sleep(5)  # Keep the lock held until all threads have run

        for i in range(0, 10):
            Thread(target=_test_acquire, args=(i,), daemon=True).start()

        while not len(results.keys()) == 10:
            sleep(0.5)
        self.assertEqual(len([lock for lock in results.values() if lock]), 1)

    def test_shared_threaded_lock(self):
        _, lock_file = mkstemp()
        lock = create_master_lock(lock_file)
        call_order = []

        def thread_a():
            nonlocal call_order
            with lock:
                sleep(0.2)
                call_order.append('a')

        def thread_b():
            nonlocal call_order
            sleep(0.1)
            with lock:
                call_order.append('b')

        a = Thread(target=thread_a)
        b = Thread(target=thread_b)

        b.start()
        a.start()
        b.join()
        a.join()
        self.assertEqual(call_order, ['a', 'b'])

    def test_multi_threaded_lock(self):
        _, lock_file = mkstemp()
        call_order = []

        def thread_a():
            nonlocal call_order
            lock = create_master_lock(lock_file)
            with lock:
                sleep(0.2)
                call_order.append('a')

        def thread_b():
            nonlocal call_order
            lock = create_master_lock(lock_file)
            sleep(0.1)
            with lock:
                call_order.append('b')

        a = Thread(target=thread_a)
        b = Thread(target=thread_b)

        b.start()
        a.start()
        b.join()
        a.join()
        self.assertEqual(call_order, ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
