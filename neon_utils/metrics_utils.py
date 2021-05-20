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

from time import time


class Stopwatch:
    """
    Provides a stopwatch object compatible with mycroft.metrics Stopwatch.
    """
    def __init__(self, metric_name=None, allow_reporting=False):
        """
        Create a stopwatch object with an optional metric_name
        Args:
            metric_name: name of the metric this stopwatch is measuring
            allow_reporting: boolean flag to allow this stopwatch to report measured metrics
        """
        self._metric = metric_name
        self._report = allow_reporting
        self._context = dict()
        self.start_time = None
        self.time = None

    def __enter__(self):
        self.start()

    def __exit__(self, typ, val, traceback):
        self.stop()
        # self.report()

    # def add_context(self, context: dict):
    #     """
    #     Add context to the measured metric.
    #     Args:
    #         context: dict of arbitrary data to add to this metric reporting
    #     """
    #     if self._metric:
    #         self._context = context

    def start(self):
        self.start_time = time()

    def stop(self):
        self.time = time() - self.start_time
        return self.time

    # def report(self):
    #     if self._metric and self._report:
    #         report_metric(self._metric, self._context)
    #         self._context = dict()


# def report_metric(name: str, data: dict, config: dict = None):
#     """
#     Report a metric via the messagebus.
#     Args:
#         name: Name of the metric to report
#         data: Arbitrary metric data to report
#         config: Optional messagebus config
#     """
#     combined = deepcopy(data)
#     combined['name'] = name
#     mycroft_bus_client.send("neon.metric", combined, config)
