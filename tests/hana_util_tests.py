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

import json
import unittest

from os import remove
from os.path import join, dirname, isfile
from shutil import copy
from time import time, sleep
from unittest.mock import patch

valid_config = {}
valid_headers = {}


class HanaUtilTests(unittest.TestCase):
    test_server = "https://hana.neonaibeta.com"
    test_path = join(dirname(__file__), "hana_test.json")

    def tearDown(self) -> None:
        global valid_config
        global valid_headers
        import neon_utils.hana_utils
        if isfile(self.test_path):
            remove(self.test_path)
        if neon_utils.hana_utils._client_config:
            valid_config = neon_utils.hana_utils._client_config
        if neon_utils.hana_utils._headers:
            valid_headers = neon_utils.hana_utils._headers
        neon_utils.hana_utils._client_config = {}
        neon_utils.hana_utils._headers = {}

    @patch("neon_utils.hana_utils._get_client_config_path")
    def test_request_backend(self, config_path):
        config_path.return_value = self.test_path

        # Use a valid config and skip extra auth
        import neon_utils.hana_utils
        neon_utils.hana_utils._client_config = valid_config
        neon_utils.hana_utils._headers = valid_headers
        from neon_utils.hana_utils import request_backend
        resp = request_backend("/neon/get_response",
                               {"lang_code": "en-us",
                                "utterance": "who are you",
                                "user_profile": {}}, self.test_server)
        self.assertEqual(resp['lang_code'], "en-us")
        self.assertIsInstance(resp['answer'], str)

        # Test expired/invalid token
        old_token_path = join(dirname(__file__), "outdated_hana_token.json")
        copy(old_token_path, self.test_path)
        with open(self.test_path, 'r') as f:
            old_contents = f.read()
        neon_utils.hana_utils._client_config = {}
        neon_utils.hana_utils._headers = {}

        # Request generates an updated token
        resp = request_backend("/neon/get_response",
                               {"lang_code": "en-us",
                                "utterance": "who are you",
                                "user_profile": {}}, self.test_server)
        self.assertEqual(resp['lang_code'], "en-us")
        self.assertIsInstance(resp['answer'], str)

        # New token is created at expected path
        self.assertTrue(isfile(self.test_path))
        with open(self.test_path, 'r') as f:
            new_contents = f.read()
        self.assertNotEqual(new_contents, old_contents)

        # TODO: Test token refresh fails, old token is removed
        # TODO: Test invalid route, invalid request data

    @patch("neon_utils.hana_utils._get_client_config_path")
    @patch("neon_utils.hana_utils._refresh_token")
    def test_request_backend_refresh_token(self, refresh_token, config_path):
        config_path.return_value = self.test_path

        import neon_utils.hana_utils
        from neon_utils.hana_utils import request_backend
        neon_utils.hana_utils.set_default_backend_url(self.test_server)
        neon_utils.hana_utils._init_client(self.test_server)
        real_client_config = neon_utils.hana_utils._client_config
        neon_utils.hana_utils._client_config['expiration'] = time() + 29
        neon_utils.hana_utils._refresh_token = refresh_token
        resp = request_backend("/neon/get_response",
                               {"lang_code": "en-us",
                                "utterance": "how are you",
                                "user_profile": {}}, self.test_server)
        self.assertEqual(resp['lang_code'], "en-us")
        self.assertIsInstance(resp['answer'], str)
        refresh_token.assert_called_once_with(self.test_server)

        neon_utils.hana_utils._client_config = real_client_config

    @patch("neon_utils.hana_utils._get_client_config_path")
    def test_00_get_token(self, config_path):
        config_path.return_value = self.test_path
        from neon_utils.hana_utils import _get_token

        # Test valid request
        _get_token(self.test_server)
        from neon_utils.hana_utils import _client_config
        self.assertTrue(isfile(self.test_path))
        with open(self.test_path) as f:
            credentials_on_disk = json.load(f)
        self.assertEqual(credentials_on_disk, _client_config)
        # TODO: Test invalid request, rate-limited request

    @patch("neon_utils.hana_utils._get_client_config_path")
    @patch("neon_utils.hana_utils._get_token")
    def test_refresh_token(self, get_token, config_path):
        config_path.return_value = self.test_path
        import neon_utils.hana_utils

        def _write_token(*_, **__):
            with open(self.test_path, 'w+') as c:
                json.dump(valid_config, c)
            neon_utils.hana_utils._client_config = valid_config

        from neon_utils.hana_utils import _refresh_token
        get_token.side_effect = _write_token

        self.assertFalse(isfile(self.test_path))

        # Test valid request (auth + refresh)
        _refresh_token(self.test_server)
        get_token.assert_called_once()
        from neon_utils.hana_utils import _client_config
        self.assertTrue(isfile(self.test_path))
        with open(self.test_path) as f:
            credentials_on_disk = json.load(f)
        self.assertEqual(credentials_on_disk, _client_config)

        # Test refresh of existing token (no auth)
        sleep(1)  # sleep to ensure new credentials expire later than existing
        _refresh_token(self.test_server)
        get_token.assert_called_once()
        with open(self.test_path) as f:
            new_credentials = json.load(f)
        self.assertNotEqual(credentials_on_disk, new_credentials)
        self.assertEqual(credentials_on_disk['client_id'],
                         new_credentials['client_id'])
        self.assertEqual(credentials_on_disk['username'],
                         new_credentials['username'])
        self.assertGreater(new_credentials['expiration'],
                           credentials_on_disk['expiration'])
        self.assertNotEqual(credentials_on_disk['access_token'],
                            new_credentials['access_token'])
        self.assertNotEqual(credentials_on_disk['refresh_token'],
                            new_credentials['refresh_token'])

    def test_config_path(self):
        from neon_utils.hana_utils import _get_client_config_path
        path_1 = _get_client_config_path("https://hana.neonaialpha.com")
        default = _get_client_config_path("https://hana.neonaiservices.com")
        self.assertNotEqual(path_1, default)
        self.assertEqual(dirname(path_1), dirname(default))

        # TODO: Test invalid refresh

    @patch("ovos_config.config.Configuration")
    def test_set_default_backend_url(self, config):
        import neon_utils.hana_utils
        from neon_utils.hana_utils import set_default_backend_url
        neon_utils.hana_utils._DEFAULT_BACKEND_URL = None
        config.return_value = dict()

        set_default_backend_url()
        self.assertEqual(neon_utils.hana_utils._DEFAULT_BACKEND_URL,
                         "https://hana.neonaiservices.com")

        set_default_backend_url("https://hana.neonaialpha.com")
        self.assertEqual(neon_utils.hana_utils._DEFAULT_BACKEND_URL,
                         "https://hana.neonaialpha.com")

        set_default_backend_url()
        self.assertEqual(neon_utils.hana_utils._DEFAULT_BACKEND_URL,
                         "https://hana.neonaiservices.com")


if __name__ == '__main__':
    unittest.main()
