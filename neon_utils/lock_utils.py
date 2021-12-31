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

import logging
from tempfile import mkstemp

from threading import Lock
from typing import Union, Optional
from combo_lock import ComboLock, NamedLock
from filelock import FileLock, Timeout

from neon_utils.logger import LOG

logging.getLogger("filelock").setLevel(logging.WARNING)


class LockException(Exception):
    """
    Exception class for lock-related errors
    """


class MasterLock:
    def __init__(self, tlock: Lock, flock: FileLock):
        self.tlock = tlock
        self.flock = flock

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        if not self.tlock.acquire(blocking, timeout):
            return False
        try:
            if not blocking:
                self.flock.acquire(0.01)
            self.flock.acquire(timeout)
        except Timeout:
            self.tlock.release()
            return False
        return True

    def release(self):
        self.tlock.release()
        self.flock.release()

    def __enter__(self):
        if self.acquire():
            return self
        else:
            raise LockException("Unable to acquire locks")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def create_master_lock(lock_path: str):
    """
    Creates a MasterLock object with a FileLock at the specified path. Note that lock objects with the same path will
    block each other
    :param lock_path: Valid file path to store the lock file at
    """
    thread_lock = Lock()
    file_lock = FileLock(lock_path)
    return MasterLock(thread_lock, file_lock)


def create_lock(lock_path: Optional[str], lock_type: Union[type(MasterLock), type(ComboLock)] = NamedLock):
    """
    Create a lock object with the specified lock_path
    :param lock_path: valid file path; some locks will use this as a lock file, others as a UID
    :param lock_type: Class of lock to create
    :return: instance of the requested lock
    """
    if not lock_path:  # TODO: Check read/write permissions
        _, lock_path = mkstemp()
        LOG.warning(f"No valid lock_path provided, using temp file: {lock_path}")
    if lock_type == MasterLock:
        return create_master_lock(lock_path)
    elif lock_type == NamedLock:
        return NamedLock(lock_path)
    elif lock_type == ComboLock:
        return ComboLock(lock_path)
