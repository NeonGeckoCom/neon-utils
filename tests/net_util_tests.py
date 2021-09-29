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
import socket

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class NetUtilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from socket import socket
        cls.base_socket = socket

    @classmethod
    def tearDownClass(cls) -> None:
        socket.socket = cls.base_socket

    def setUp(self):
        socket.socket = self.base_socket

    def test_get_ip_address_valid(self):
        from neon_utils.net_utils import get_ip_address

        ip_addr = get_ip_address()
        self.assertIsInstance(ip_addr, str)

    def test_get_ip_address_offline(self):
        def mock_socket(*args, **kwargs):
            raise OSError("Socket is disabled!")
        socket.socket = mock_socket
        from neon_utils.net_utils import get_ip_address

        with self.assertRaises(OSError):
            get_ip_address()

    def test_get_adapter_info(self):
        from neon_utils.net_utils import get_adapter_info
        try:
            info = get_adapter_info()
            self.assertIsInstance(info, dict)
            self.assertIsInstance(info.get("mac"), str)
            self.assertEqual(len(info["mac"]), 17)
            self.assertIsInstance(info.get("ipv4"), str)
            self.assertEqual(len(info["ipv4"].split('.')), 4)
            self.assertIsInstance(info.get("ipv6"), str)
            print(info["ipv6"])
            self.assertGreater(info["ipv6"].count(':'), 3)
        except IndexError:
            print("No Connection")

    def test_get_adapter_fail(self):
        from neon_utils.net_utils import get_adapter_info

        with self.assertRaises(IndexError):
            get_adapter_info("FAIL")

    def test_check_url_connection_valid_online(self):
        from neon_utils.net_utils import check_url_response

        self.assertTrue(check_url_response())
        self.assertTrue(check_url_response("google.com"))
        self.assertTrue(check_url_response("https://github.com"))

    def test_check_url_connection_invalid_schema(self):
        from neon_utils.net_utils import check_url_response

        with self.assertRaises(ValueError):
            check_url_response("smb://google.com")
        with self.assertRaises(ValueError):
            check_url_response("ssh://github.com")

    def test_check_url_connection_invalid_args(self):
        from neon_utils.net_utils import check_url_response

        with self.assertRaises(ValueError):
            check_url_response("")
        with self.assertRaises(ValueError):
            check_url_response(123)
        with self.assertRaises(ValueError):
            check_url_response(None)

    def test_check_url_connection_valid_offline(self):
        def mock_socket(*args, **kwargs):
            raise ConnectionError("Socket is disabled!")
        socket.socket = mock_socket
        from neon_utils.net_utils import check_url_response

        self.assertFalse(check_url_response())

    def test_check_url_connection_invalid_url(self):
        from neon_utils.net_utils import check_url_response

        self.assertFalse(check_url_response("https://api.neon.ai"))

    def test_check_online_valid_online(self):
        from neon_utils.net_utils import check_online
        self.assertTrue(check_online())
        self.assertTrue(check_online(("google.com", "github.com")))
        self.assertTrue(check_online(("api.neon.ai", "google.com")))
        self.assertTrue(check_online(("", "google.com")))

    def test_check_online_invalid_offline(self):
        from neon_utils.net_utils import check_online
        self.assertFalse(check_online(("api.neon.ai",)))
        self.assertFalse(check_online(("",)))

    def test_check_online_valid_offline(self):
        def mock_socket(*args, **kwargs):
            raise ConnectionError("Socket is disabled!")
        socket.socket = mock_socket
        from neon_utils.net_utils import check_online
        self.assertFalse(check_online())
        self.assertFalse(check_online(("google.com", "github.com")))

    def test_check_online_invalid_params(self):
        from neon_utils.net_utils import check_online
        with self.assertRaises(ValueError):
            check_online(None)
        with self.assertRaises(ValueError):
            check_online("google.com")
        with self.assertRaises(ValueError):
            check_online(123)


if __name__ == '__main__':
    unittest.main()
