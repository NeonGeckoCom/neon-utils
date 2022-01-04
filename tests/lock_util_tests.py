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

    def test_create_lock(self):
        _, lock_file = mkstemp()
        lock = create_lock(lock_file)
        self.assertIsInstance(lock, NamedLock)
        lock = create_lock(lock_file, MasterLock)
        self.assertIsInstance(lock, MasterLock)
        lock = create_lock(lock_file, ComboLock)
        self.assertIsInstance(lock, ComboLock)

        lock = create_lock(None)
        self.assertIsInstance(lock, NamedLock)


if __name__ == '__main__':
    unittest.main()
