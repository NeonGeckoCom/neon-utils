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

import tracemalloc

from threading import Event, Thread
from typing import Optional
from ovos_utils.log import LOG


_malloc_event = Event()
_malloc_thread = None


def start_systemd_service(service: callable, **kwargs):
    """
    Start a Neon Core module with systemd wrappers to report process lifecycle
    """
    try:
        import sdnotify
    except ImportError:
        LOG.exception(f'sdnotify not installed! '
                      f'Starting service without systemd hooks')
        service(**kwargs)
        return
    notifier = sdnotify.SystemdNotifier()

    def on_ready():
        notifier.notify('READY=1')
        notifier.notify('STATUS=Ready')

    def on_stopping():
        try:
            stop_malloc()
        except Exception as e:
            LOG.error(e)
        notifier.notify('STOPPING=1')
        notifier.notify('STATUS=Stopping')

    def on_error(err: str):
        if err.isnumeric():
            notifier.notify(f'ERRNO={err}')
        else:
            notifier.notify(f'ERRNO=1')

    def on_alive():
        notifier.notify('STATUS=Starting')

    def on_started():
        notifier.notify('STATUS=Started')

    service(ready_hook=on_ready, error_hook=on_error,
            stopping_hook=on_stopping, alive_hook=on_alive,
            started_hook=on_started, **kwargs)


def start_malloc(config: dict = None, stack_depth: int = 1,
                 force: bool = False) -> bool:
    """
    Start malloc trace if configured
    :param config: dict Configuration
    :param stack_depth: depth to track memory usage
    :param force: if True, start tracemalloc regardless of configuration
    :returns: True if malloc started
    """
    if not config:
        from ovos_config.config import Configuration
        config = Configuration()
    if force or config.get('debugging') and \
            config['debugging'].get('tracemalloc'):
        LOG.info(f"starting tracemalloc")
        tracemalloc.start(stack_depth)
        if config['debugging'].get('log_malloc'):
            interval_minutes = config['debugging'].get('log_interval_minutes',
                                                       60)
            global _malloc_thread
            _malloc_thread = Thread(target=_log_malloc,
                                    args=((interval_minutes * 60),),
                                    daemon=True)
            _malloc_thread.start()
        return True
    return False


def stop_malloc():
    """
    Stop tracemalloc logging if active
    """
    if _malloc_thread:
        LOG.debug(f"Stopping malloc logging")
        _malloc_event.set()
        _malloc_thread.join()


def snapshot_malloc() -> Optional[tracemalloc.Snapshot]:
    """
    Capture and return a tracemalloc Snapshot if tracemalloc is started
    """
    try:
        LOG.debug("Capturing malloc snapshot")
        return tracemalloc.take_snapshot()
    except RuntimeError:
        LOG.debug("No tracemalloc trace")
    except Exception as e:
        LOG.exception(e)
    return None


def print_malloc(snapshot: tracemalloc.Snapshot, limit: int = 8,
                 filter_traces: bool = False):
    """
    Log a malloc snapshot
    :param snapshot: Snapshot to evaluate
    :param limit: number of traces to log
    :param filter_traces: if True, remove importlib and unknown stack traces
    """
    LOG.debug(f"Processing snapshot")
    if filter_traces:
        snapshot = snapshot.filter_traces((
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
            tracemalloc.Filter(False, "<unknown>"),
        ))
    top_stats = snapshot.statistics('traceback')

    LOG.info(f"Top {limit} memory users")
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        LOG.info(f"#{index}: {frame.filename}:{frame.lineno}: "
                 f"{stat.size / 1048576} MiB")
        for frame in stat.traceback[1:]:
            LOG.debug(f'{frame.filename}:{frame.lineno}')

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        LOG.info(f"{len(other)} other:{size / 1048576} MiB")
    total = sum(stat.size for stat in top_stats)
    LOG.info(f"Total allocated size: {total / 1048576} MiB")


def _log_malloc(interval_seconds: int):
    _malloc_event.clear()
    while not _malloc_event.wait(interval_seconds):
        print_malloc(snapshot_malloc(), filter_traces=True)
    LOG.info(f"Stopping malloc logging")
