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

import pika

from threading import Thread
from time import time

from neon_utils.socket_utils import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.mq_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEST_PATH = os.path.join(ROOT_DIR, "tests", "ccl_files")

INPUT_CHANNEL = str(time())
OUTPUT_CHANNEL = str(time())


class TestMQConnector(MQConnector):
    def __init__(self, config: dict, service_name: str, vhost: str):
        super().__init__(config, service_name)
        self.vhost = vhost

    @staticmethod
    def respond(channel, method, _, body):
        request = b64_to_dict(body)
        response = dict_to_b64({"message_id": request["message_id"],
                                "success": True,
                                "request_data": request["data"]})
        reply_channel = request.get("routing_key") or OUTPUT_CHANNEL
        channel.queue_declare(queue=reply_channel)
        channel.basic_publish(exchange='',
                              routing_key=reply_channel,
                              body=response,
                              properties=pika.BasicProperties(expiration='1000'))
        channel.basic_ack(delivery_tag=method.delivery_tag)


class MqUtilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vhost = "/neon_testing"
        cls.test_connector = TestMQConnector(config=get_neon_local_config().content.get('MQ'),
                                             service_name="mq_handler",
                                             vhost=vhost)
        cls.test_connector.register_consumer("neon_utils_test", vhost, INPUT_CHANNEL,
                                             cls.test_connector.respond, auto_ack=False)
        cls.test_connector.run_consumers()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test_connector.stop_consumers()

    def test_get_mq_response_valid(self):
        request = {"data": time()}
        response = get_mq_response("/neon_testing", request, INPUT_CHANNEL)
        self.assertIsInstance(response, dict)
        self.assertTrue(response["success"])
        self.assertEqual(response["request_data"], request["data"])

    def test_get_mq_response_spec_output_channel_valid(self):
        request = {"data": time()}
        response = get_mq_response("/neon_testing", request, INPUT_CHANNEL, OUTPUT_CHANNEL)
        self.assertIsInstance(response, dict)
        self.assertTrue(response["success"])
        self.assertEqual(response["request_data"], request["data"])

    def test_multiple_mq_requests(self):
        responses = dict()
        processes = []

        def check_response(name: str):
            request = {"data": time()}
            response = get_mq_response("/neon_testing", request, INPUT_CHANNEL)
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
            p = Thread(target=check_response, args=(str(i),))
            p.start()
            processes.append(p)

        for p in processes:
            p.join(60)

        self.assertEqual(len(processes), len(responses))
        for resp in responses.values():
            self.assertTrue(resp['success'], resp.get('reason'))

    def test_get_mq_response_invalid_vhost(self):
        with self.assertRaises(ValueError):
            get_mq_response("invalid_endpoint", {}, "test", "test")

    # def test_get_mq_response_error_in_handler(self):
    #     # TODO: Troubleshoot this DM
    #     request = {"fail": True}
    #     response = get_mq_response("/neon_testing", request, INPUT_CHANNEL, OUTPUT_CHANNEL)
    #     self.assertIsInstance(response, dict)
    #     self.assertFalse(response)


if __name__ == '__main__':
    unittest.main()
