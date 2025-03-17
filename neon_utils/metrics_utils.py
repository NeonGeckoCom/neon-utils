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

from socket import gethostname
from time import time, strftime
from ovos_bus_client import Message, MessageBusClient
from ovos_utils.log import LOG, deprecated

from neon_utils.message_utils import dig_for_message


class Stopwatch:
    """
    Provides a stopwatch object compatible with mycroft.metrics Stopwatch.
    """

    def __init__(self, metric_name=None, allow_reporting=False, bus=None):
        """
        Create a stopwatch object with an optional metric_name
        @param metric_name: name of the metric this stopwatch is measuring
        @param allow_reporting: boolean flag to allow this stopwatch to report measured metrics
        @param bus: MessageBusClient object to report metrics with
        """
        self._metric = metric_name
        self._report = allow_reporting
        self._context = dict()
        self._bus = bus
        self.start_time = None
        self.time = None

    def __enter__(self):
        self.start()

    def __exit__(self, typ, val, traceback):
        self.stop()
        try:
            self.report()
        except Exception as e:
            LOG.exception(e)

    def start(self):
        self.start_time = time()

    def stop(self):
        try:
            self.time = time() - self.start_time
        except TypeError:
            LOG.error("stop called before start!")
            self.time = None
        return self.time

    def report(self):
        if self._metric and self._report:
            if not self._bus:
                self._bus = MessageBusClient()
                self._bus.run_in_thread()
            message = dig_for_message() or Message("")
            message.context['timestamp'] = time()
            self._bus.emit(message.forward("neon.metric",
                                           {"name": self._metric,
                                            "duration": self.time}))


@deprecated("Emit `neon.metric` message instead of calling this function.",
            "2.0.0")
def report_metric(name: str, **kwargs):
    """
    Report a metric over the MQ bus.
    :param name: Name of the metric to report
    :param kwargs: Arbitrary data to include with metric report
    """
    try:
        from neon_mq_connector.utils.client_utils import send_mq_request
        send_mq_request("/neon_metrics", {**{"name": name}, **kwargs},
                        "neon_metrics_input", expect_response=False)
        return True
    except Exception as e:
        LOG.error(e)
        return False


def announce_connection():
    try:
        from neon_mq_connector.utils.client_utils import send_mq_request
        from neon_core.version import __version__
        from ovos_config.config import Configuration
        data = {"time": strftime('%Y-%m-%d %H:%M:%S'),
                "name": dict(Configuration()).get("device_name") or "unknown",
                "host": gethostname(),
                "ver": __version__}
        send_mq_request("/neon_metrics", data, "neon_connections_input",
                        expect_response=False)
        return True
    except Exception as e:
        LOG.error(e)
        return False
