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
from multiprocessing import Process
from time import time, sleep

import pika
from neon_mq_connector.connector import MQConnector, ConsumerThread

from neon_utils.socket_utils import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.mq_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEST_PATH = os.path.join(ROOT_DIR, "tests", "ccl_files")


class TestMQConnector(MQConnector):
    def __init__(self, config: dict, service_name: str, vhost: str):
        super().__init__(config, service_name)
        self.vhost = vhost

    @staticmethod
    def respond(channel, method, _, body):
        request = b64_to_dict(body)
        if request.get("fail"):
            raise Exception("Failure Case!")
        response = dict_to_b64({"message_id": request["message_id"],
                                "success": True,
                                "request_data": request["data"]})
        channel.queue_declare(queue='neon_utils_test_output')
        channel.basic_publish(exchange='',
                              routing_key='neon_utils_test_output',
                              body=response,
                              properties=pika.BasicProperties(expiration='1000'))

    def exception_handler(self, *args, **kwargs):
        LOG.info("Handling Exception")
        self.register_consumer("neon_utils_test", self.vhost, "neon_utils_test_input",
                               self.respond)
        self.run_consumers()
        LOG.info("Exception Handled")


class MqUtilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vhost = "/neon_testing"
        cls.test_connector = TestMQConnector(config=get_neon_local_config().content.get('MQ'),
                                             service_name="mq_handler",
                                             vhost=vhost)
        cls.test_connector.register_consumer("neon_utils_test", vhost, "neon_utils_test_input",
                                             cls.test_connector.respond, cls.test_connector.exception_handler)
        cls.test_connector.run_consumers()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test_connector.stop_consumers()

    def test_get_mq_response_valid(self):
        request = {"data": time()}
        response = get_mq_response("/neon_testing", request, "neon_utils_test_input", "neon_utils_test_output")
        self.assertIsInstance(response, dict)
        self.assertTrue(response["success"])
        self.assertEqual(response["request_data"], request["data"])

    def test_multiple_mq_requests(self):
        responses = dict()
        processes = []

        def check_response(name: str):
            request = {"data": time()}
            response = get_mq_response("/neon_testing", request, "neon_utils_test_input", "neon_utils_test_output")
            self.assertIsInstance(response, dict)
            if not isinstance(response, dict):
                responses[name] = {'success': False,
                                   'reason': 'Response is not a dict',
                                   'response': response}
                return
            if not response.get("success"):
                responses[name] = {'success': False,
                                   'reason': 'Response success flag not true',
                                   'response': response}
                return
            if response.get("request_data") != request["data"]:
                responses[name] = {'success': False,
                                   'reason': "Response data doesn't match request",
                                   'response': response}
                return
            responses[name] = {'success': True}

        for i in range(8):
            p = Process(target=check_response, args=(str(i),))
            p.start()
            processes.append(p)

        for p in processes:
            p.join(30)

        for resp in responses.values():
            self.assertTrue(resp['success'], resp.get('reason'))

    def test_get_mq_response_invalid_vhost(self):
        with self.assertRaises(ValueError):
            get_mq_response("invalid_endpoint", {}, "test", "test")

    # def test_get_mq_response_error_in_handler(self):
    #     # TODO: Troubleshoot this DM
    #     request = {"fail": True}
    #     response = get_mq_response("/neon_testing", request, "neon_utils_test_input", "neon_utils_test_output")
    #     self.assertIsInstance(response, dict)
    #     self.assertFalse(response)


if __name__ == '__main__':
    unittest.main()
