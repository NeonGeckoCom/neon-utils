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

import sys
import os
import unittest
from time import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.message_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

VALID_STRING = 'This is only a test!'
VALID_BYTES = b'This is only a test!'
ENCODED_UTF8 = "VGhpcyBpcyBvbmx5IGEgdGVzdCE="
ENCODED_UTF16 = "䝖灨祣灂祣療浢㕸䝉杅䝤穖䍤㵅"


def get_message_standard(message):
    print(message)
    return dig_for_message()


def get_message_alt_name(msg):
    print(msg)
    return dig_for_message()


def get_message_no_name(_):
    return dig_for_message()


class MessageUtilTests(unittest.TestCase):
    def test_request_from_mobile(self):
        from_mobile = request_from_mobile(Message("", {}, {"mobile": True}))
        self.assertTrue(from_mobile)

        not_from_mobile = request_from_mobile(Message("", {}, {}))
        self.assertFalse(not_from_mobile)

    def test_get_message_username(self):
        with_user = get_message_user(Message("", {}, {"username": "testrunner"}))
        self.assertEqual(with_user, "testrunner")

        without_user = get_message_user(Message(""))
        self.assertIsNone(without_user)

    def test_get_message_username_invalid_arg(self):
        with self.assertRaises(ValueError):
            get_message_user(None)

        with self.assertRaises(AttributeError):
            get_message_user("Nobody")

    def test_encode_bytes_valid(self):
        encoded_8 = encode_bytes_to_b64_string(VALID_BYTES, 'utf-8')
        self.assertIsInstance(encoded_8, str)
        self.assertEqual(encoded_8, ENCODED_UTF8)

    def test_encode_bytes_invalid_data_type(self):
        with self.assertRaises(ValueError):
            encode_bytes_to_b64_string(ENCODED_UTF8)

    def test_encode_bytes_invalid_charset(self):
        with self.assertRaises(EncodingError):
            encode_bytes_to_b64_string(VALID_BYTES, "INVALID_ENCODING")

    def test_decode_bytes_valid(self):
        decoded_8 = decode_b64_string_to_bytes(ENCODED_UTF8, 'utf-8')
        self.assertIsInstance(decoded_8, bytes)
        self.assertEqual(decoded_8, VALID_BYTES)

    def test_decode_bytes_invalid_data_type(self):
        with self.assertRaises(ValueError):
            decode_b64_string_to_bytes(VALID_BYTES)

    def test_decode_bytes_incorrect_encoding(self):
        with self.assertRaises(EncodingError):
            decode_b64_string_to_bytes(ENCODED_UTF16, "utf-8")

    def test_decode_bytes_invalid_encoding(self):
        with self.assertRaises(EncodingError):
            decode_b64_string_to_bytes(ENCODED_UTF8, "INVALID_ENCODING")

    def test_dig_for_message_simple(self):
        test_msg = Message("test message", {"test": "data"}, {"time": time()})
        self.assertEqual(test_msg, get_message_standard(test_msg))
        test_msg = Message("test message", {"test": "data"}, {"time": time()})
        self.assertEqual(test_msg, get_message_alt_name(test_msg))
        test_msg = Message("test message", {"test": "data"}, {"time": time()})
        self.assertEqual(test_msg, get_message_no_name(test_msg))

    def test_dig_for_message_nested(self):
        message = Message("test message", {"test": "data"}, {"time": time()})

        def simple_wrapper():
            return get_message_no_name(message)

        self.assertEqual(simple_wrapper(), message)

        message = Message("test message", {"test": "data"}, {"time": time()})

        def get_message():
            return dig_for_message()

        def wrapper_method(msg):
            self.assertEqual(msg, get_message())

        wrapper_method(message)

    def test_dig_for_message_invalid_type(self):
        tester = Message("test message", {"test": "data"}, {"time": time()})

        def wrapper_method(_):
            return dig_for_message()
        self.assertIsNone(wrapper_method(dict()))

    def test_dig_for_message_no_method_call(self):
        message = Message("test message", {"test": "data"}, {"time": time()})
        self.assertIsNone(dig_for_message())


if __name__ == '__main__':
    unittest.main()
