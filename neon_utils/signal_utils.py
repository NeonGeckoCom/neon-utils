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
from time import time, sleep

from mycroft_bus_client import MessageBusClient, Message
import ovos_utils.signal

from neon_utils.logger import LOG

BUS = MessageBusClient()
BUS.run_in_thread()


def fs_wait_for_signal_create(signal_name: str, timeout: int = 30):
    expiration = time() + timeout
    while not check_for_signal(signal_name, -1) and time() < expiration:
        sleep(0.1)
    return check_for_signal(signal_name, -1)


def fs_wait_for_signal_clear(signal_name: str, timeout: int = 30):
    expiration = time() + timeout
    while check_for_signal(signal_name, -1) and time() < expiration:
        sleep(0.1)
    return check_for_signal(signal_name, -1)


# Init default file handler methods
create_signal = ovos_utils.signal.create_signal
check_for_signal = ovos_utils.signal.check_for_signal
wait_for_signal_clear = fs_wait_for_signal_clear
wait_for_signal_create = fs_wait_for_signal_create


def init_signal_handlers():
    """
    Initialize the proper signal methods dependent on the Signal Manager being available.
    Any previously imported methods will not be affected by calls to this method, but imports of `signal_utils` are.
    i.e. `from neon_utils.signal_utils import check_for_signal`, `check_for_signal` is not changed,
         `import neon_utils.signal_utils`, `neon_utils.signal_utils.check_for_signal` is changed.
    """
    global create_signal
    global check_for_signal
    global wait_for_signal_clear
    global wait_for_signal_create
    if check_signal_manager_available():
        LOG.info("Signal Manager Available")
        create_signal = manager_create_signal
        check_for_signal = manager_check_for_signal
        wait_for_signal_clear = manager_wait_for_signal_clear
        wait_for_signal_create = manager_wait_for_signal_create
    else:
        LOG.warning("No signal manager available; falling back to FS signals")
        create_signal = ovos_utils.signal.create_signal
        check_for_signal = ovos_utils.signal.check_for_signal
        wait_for_signal_clear = fs_wait_for_signal_clear
        wait_for_signal_create = fs_wait_for_signal_create

    try:
        import mycroft.util.signal
        mycroft.util.signal.create_signal = create_signal
        mycroft.util.signal.check_for_signal = check_for_signal
        LOG.info(f"Overrode mycroft.util.signal methods")
    except ImportError:
        pass
    except TypeError as e:
        # This comes from tests overriding MessageBusClient()
        LOG.error(e)


def check_signal_manager_available() -> bool:
    """
    Method to check if a signal manager service is available
    """
    if BUS.connected_event.wait(10):  # Wait up to 10 seconds for the bus service
        response = BUS.wait_for_response(Message("neon.signal_manager_active"))
        LOG.debug(f"signal_manager_active={response is not None}")
        return response is not None
    LOG.error(f"Signal manager check gave up waiting for the MessageBus")
    return False


def manager_create_signal(signal_name: str, *_, **__) -> bool:
    """
    Backwards-compatible method for creating a signal
    :param signal_name: named signal to create
    :return: True if signal exists
    """
    stat = BUS.wait_for_response(Message("neon.create_signal",
                                         {"signal_name": signal_name}),
                                 f"neon.create_signal.{signal_name}", 10) or Message('')
    return stat.data.get("is_set")


def manager_check_for_signal(signal_name: str, sec_lifetime: int = 0, *_, **__) -> bool:
    """
    Backwards-compatible method for checking for a signal
    :param signal_name: name of signal to check
    :param sec_lifetime: max age of signal in seconds before clearing it and returning False
    :return: True if signal exists
    """
    stat = BUS.wait_for_response(Message("neon.check_for_signal",
                                         {"signal_name": signal_name,
                                          "sec_lifetime": sec_lifetime}),
                                 f"neon.check_for_signal.{signal_name}", 10) or Message('')
    return stat.data.get("is_set")


def manager_wait_for_signal_create(signal_name: str, timeout: int = 30) -> bool:
    """
    Block until the specified signal is set or timeout is reached
    :param signal_name: name of signal to check
    :param timeout: max seconds to wait for signal to be created, Default is 30 seconds
    :return: True if signal exists
    """
    timeout = 300 if timeout > 300 else timeout  # Cap wait at 5 minutes
    bus_wait_time = timeout + 5  # Allow some padding for bus handler
    stat = BUS.wait_for_response(Message("neon.wait_for_signal_create",
                                         {"signal_name": signal_name,
                                          "timeout": timeout}),
                                 f"neon.wait_for_signal_create.{signal_name}", bus_wait_time)
    return stat.data.get("is_set")


def manager_wait_for_signal_clear(signal_name: str, timeout: int = 30) -> bool:
    """
    Block until the specified signal is cleared or timeout is reached
    :param signal_name: name of signal to check
    :param timeout: max seconds to wait for signal to be created, Default is 30 seconds
    :return: True if signal exists
    """
    timeout = 300 if timeout > 300 else timeout  # Cap wait at 5 minutes
    bus_wait_time = timeout + 5  # Allow some padding for bus handler
    stat = BUS.wait_for_response(Message("neon.wait_for_signal_clear",
                                         {"signal_name": signal_name,
                                          "timeout": timeout}),
                                 f"neon.wait_for_signal_clear.{signal_name}", bus_wait_time)
    return stat.data.get("is_set")


# Check for service handlers on import
init_signal_handlers()
