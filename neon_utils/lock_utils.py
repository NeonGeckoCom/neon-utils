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

from threading import Lock
from filelock import FileLock, Timeout

# TODO: Consider rebasing MasterLock to extend combo-lock DM


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
