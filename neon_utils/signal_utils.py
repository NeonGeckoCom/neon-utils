# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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

import inspect

from time import time, sleep
from typing import Optional, Callable

from ovos_bus_client import MessageBusClient, Message
from ovos_utils.log import log_deprecation

from neon_utils.logger import LOG

try:
    from mock.mock import Mock
except ImportError:
    raise ImportError("`mock` is not installed,"
                      " pip install neon-utils[signal]")
_BUS: Optional[MessageBusClient] = None
_MAX_TIMEOUT: Optional[int] = None

_create_signal: Optional[Callable] = None
_check_for_signal: Optional[Callable] = None
_wait_for_signal_clear: Optional[Callable] = None
_wait_for_signal_create: Optional[Callable] = None


def create_signal(*args, **kwargs):
    global _create_signal
    if not _create_signal:
        LOG.warning("create_signal called before signal manager init")
        init_signal_handlers()
    return _create_signal(*args, **kwargs)


def check_for_signal(*args, **kwargs):
    global _check_for_signal
    if not _check_for_signal:
        LOG.warning("check_for_signal called before signal manager init")
        init_signal_handlers()
    return _check_for_signal(*args, **kwargs)


def wait_for_signal_clear(*args, **kwargs):
    global _wait_for_signal_clear
    if not _wait_for_signal_clear:
        LOG.warning("wait_for_signal_clear called before signal manager init")
        init_signal_handlers()
    return _wait_for_signal_clear(*args, **kwargs)


def wait_for_signal_create(*args, **kwargs):
    global _wait_for_signal_create
    if not _wait_for_signal_create:
        LOG.warning("wait_for_signal_create called before signal manager init")
        init_signal_handlers()
    return _wait_for_signal_create(*args, **kwargs)


def init_signal_bus(bus: MessageBusClient):
    """
    Specify a MessageBusClient to use for methods in this module
    :param bus: Connected and Running MessageBusClient
    """
    global _BUS
    if not bus.started_running:
        bus.run_in_thread()
    _BUS = bus


def init_signal_handlers():
    """
    Initialize the proper signal methods dependent on the Signal Manager
    being available. Any previously imported methods will not be affected by
    calls to this method, but imports of `signal_utils` are.
    i.e. `from neon_utils.signal_utils import check_for_signal`,
     `check_for_signal` is not changed.
     `import neon_utils.signal_utils`,
     `neon_utils.signal_utils.check_for_signal` is changed.
    """
    global _create_signal
    global _check_for_signal
    global _wait_for_signal_clear
    global _wait_for_signal_create
    global _MAX_TIMEOUT
    from ovos_config.config import Configuration
    signal_config = Configuration().get("signal") or dict()
    patch_imports = signal_config.get("patch_imports", True)
    _MAX_TIMEOUT = int(signal_config.get("max_wait_seconds") or 300)

    if check_signal_manager_available():
        LOG.info("Signal Manager Available")
        _create_signal = _manager_create_signal
        _check_for_signal = _manager_check_for_signal
        _wait_for_signal_clear = _manager_wait_for_signal_clear
        _wait_for_signal_create = _manager_wait_for_signal_create

        if patch_imports:
            log_deprecation("Import patching will be deprecated. Disable in "
                            "configuration by setting `signal`.`patch_imports` "
                            "to `False`", "2.0.0")
            try:
                import mycroft.util.signal
                mycroft.util.signal.create_signal = _create_signal
                mycroft.util.signal.check_for_signal = _check_for_signal
                LOG.info("Overrode mycroft.util.signal methods")
            except (ImportError, AttributeError) as e:
                LOG.debug(e)
            except TypeError as e:
                # This comes from tests overriding MessageBusClient()
                LOG.error(e)

    else:
        LOG.warning("FS signals are deprecated. Signal methods will have no effect.")
        if patch_imports:
            import os
            import tempfile
            from ovos_utils.file_utils import ensure_directory_exists
            log_deprecation("Import patching will be deprecated. Disable in "
                "configuration by setting `signal`.`patch_imports` "
                "to `False`", "2.0.0")

            def get_ipc_directory(domain=None, config=None):
                """Get the directory used for Inter Process Communication

                Files in this folder can be accessed by different processes on the
                machine.  Useful for communication.  This is often a small RAM disk.

                Args:
                    domain (str): The IPC domain.  Basically a subdirectory to prevent
                        overlapping signal filenames.
                    config (dict): mycroft.conf, to read ipc directory from

                Returns:
                    str: a path to the IPC directory
                """
                if config is None:
                    try:
                        from ovos_config.config import Configuration
                        config = Configuration()
                    except ImportError:
                        LOG.warning("Config not provided and ovos_config not available")
                        config = dict()
                path = config.get("ipc_path")
                if not path:
                    # If not defined, use /tmp/mycroft/ipc
                    path = os.path.join(tempfile.gettempdir(), "mycroft", "ipc")
                return ensure_directory_exists(path, domain)

            def create_file(filename):
                """ Create the file filename and create any directories needed

                    Args:
                        filename: Path to the file to be created
                """
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError:
                    pass
                with open(filename, 'w') as f:
                    f.write('')

            def create_signal(signal_name, config=None):
                """Create a named signal

                Args:
                    signal_name (str): The signal's name.  Must only contain characters
                        valid in filenames.
                    config (dict): mycroft.conf, to read ipc directory from
                """
                try:
                    path = os.path.join(get_ipc_directory(config=config),
                                        "signal", signal_name)
                    create_file(path)
                    return os.path.isfile(path)
                except IOError:
                    return False


            def check_for_signal(signal_name, sec_lifetime=0, config=None):
                """See if a named signal exists

                Args:
                    signal_name (str): The signal's name.  Must only contain characters
                        valid in filenames.
                    sec_lifetime (int, optional): How many seconds the signal should
                        remain valid.  If 0 or not specified, it is a single-use signal.
                        If -1, it never expires.
                    config (dict): mycroft.conf, to read ipc directory from

                Returns:
                    bool: True if the signal is defined, False otherwise
                """
                path = os.path.join(get_ipc_directory(config=config),
                                    "signal", signal_name)
                if os.path.isfile(path):
                    if sec_lifetime == 0:
                        # consume this single-use signal
                        os.remove(path)
                    elif sec_lifetime == -1:
                        return True
                    elif int(os.path.getctime(path) + sec_lifetime) < int(time.time()):
                        # remove once expired
                        os.remove(path)
                        return False
                    return True

                # No such signal exists
                return False 

            _create_signal = create_signal
            _check_for_signal = check_for_signal
            _wait_for_signal_clear = _fs_wait_for_signal_clear
            _wait_for_signal_create = _fs_wait_for_signal_create
        else:
            _create_signal = Mock(return_value=False)
            _check_for_signal = Mock(return_value=False)
            _wait_for_signal_clear = Mock(return_value=False)
            _wait_for_signal_create = Mock(return_value=False)


def check_signal_manager_available() -> bool:
    """
    Method to check if a signal manager service is available
    """
    global _BUS
    if not _BUS:
        LOG.warning("Initializing new messagebus connection")
        init_signal_bus(MessageBusClient())
    if _BUS.connected_event.wait(10):  # Wait up to 10 seconds for the bus service
        response = _BUS.wait_for_response(Message("neon.signal_manager_active"))
        LOG.debug(f"signal_manager_active={response is not None}")
        return response is not None
    LOG.error(f"Signal manager check gave up waiting for the MessageBus")
    return False


def _manager_create_signal(signal_name: str, *_, **__) -> bool:
    """
    Backwards-compatible method for creating a signal
    :param signal_name: named signal to create
    :return: True if signal exists
    """
    call = inspect.stack()[2]
    module = inspect.getmodule(call.frame)
    name = module.__name__ if module else call.filename
    stat = _BUS.wait_for_response(Message("neon.create_signal",
                                          {"signal_name": signal_name},
                                          {"origin_module": name,
                                           "origin_line": call.lineno}),
                                  f"neon.create_signal.{signal_name}", 10) or \
        Message('')
    return stat.data.get("is_set")


def _manager_check_for_signal(signal_name: str, sec_lifetime: int = 0, *_, **__) -> bool:
    """
    Backwards-compatible method for checking for a signal
    :param signal_name: name of signal to check
    :param sec_lifetime: max age of signal in seconds before clearing it and
        returning False
    :return: True if signal exists
    """
    call = inspect.stack()[2]
    module = inspect.getmodule(call.frame)
    name = module.__name__ if module else call.filename
    stat = _BUS.wait_for_response(Message("neon.check_for_signal",
                                          {"signal_name": signal_name,
                                           "sec_lifetime": sec_lifetime},
                                          {"origin_module": name,
                                           "origin_line": call.lineno}),
                                  f"neon.check_for_signal.{signal_name}",
                                  10) or Message('')
    return stat.data.get("is_set")


def _manager_wait_for_signal_create(signal_name: str,
                                    timeout: int = 30) -> bool:
    """
    Block until the specified signal is set or timeout is reached
    :param signal_name: name of signal to check
    :param timeout: max seconds to wait for signal to be created,
        Default is 30 seconds
    :return: True if signal exists
    """
    timeout = _MAX_TIMEOUT if timeout > _MAX_TIMEOUT else timeout  # Cap wait
    bus_wait_time = timeout + 5  # Allow some padding for bus handler
    stat = _BUS.wait_for_response(Message("neon.wait_for_signal_create",
                                          {"signal_name": signal_name,
                                           "timeout": timeout}),
                                  f"neon.wait_for_signal_create.{signal_name}",
                                  bus_wait_time)
    return stat.data.get("is_set")


def _manager_wait_for_signal_clear(signal_name: str, timeout: int = 30) -> bool:
    """
    Block until the specified signal is cleared or timeout is reached
    :param signal_name: name of signal to check
    :param timeout: max seconds to wait for signal to be created,
        Default is 30 seconds
    :return: True if signal exists
    """
    timeout = _MAX_TIMEOUT if timeout > _MAX_TIMEOUT else timeout  # Cap wait
    bus_wait_time = timeout + 5  # Allow some padding for bus handler
    stat = _BUS.wait_for_response(Message("neon.wait_for_signal_clear",
                                          {"signal_name": signal_name,
                                           "timeout": timeout}),
                                  f"neon.wait_for_signal_clear.{signal_name}",
                                  bus_wait_time)
    return stat.data.get("is_set")


def _fs_wait_for_signal_create(signal_name: str, timeout: int = 30):
    expiration = time() + timeout
    while not check_for_signal(signal_name, -1) and time() < expiration:
        sleep(0.1)
    return check_for_signal(signal_name, -1)


def _fs_wait_for_signal_clear(signal_name: str, timeout: int = 30):
    expiration = time() + timeout
    while check_for_signal(signal_name, -1) and time() < expiration:
        sleep(0.1)
    return check_for_signal(signal_name, -1)
