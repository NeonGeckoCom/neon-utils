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
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.authentication_utils import *
from neon_utils.configuration_utils import get_neon_local_config, NGIConfig

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
CRED_PATH = os.path.join(ROOT_DIR, "credentials")


class AuthUtilTests(unittest.TestCase):
    def setUp(self) -> None:
        config_path = os.path.join(ROOT_DIR, "configuration")
        self.old_local_conf = os.path.join(config_path, "old_local_conf.yml")
        self.ngi_local_conf = os.path.join(config_path, "ngi_local_conf.yml")
        shutil.copy(self.ngi_local_conf, self.old_local_conf)
        NGIConfig(os.path.splitext(os.path.basename(self.ngi_local_conf))[0], os.path.dirname(self.ngi_local_conf),
                  force_reload=True)

    def tearDown(self) -> None:
        shutil.move(self.old_local_conf, self.ngi_local_conf)

    def test_get_git_token(self):
        try:
            token = find_neon_git_token("/tmp")
            self.assertIsInstance(token, str)
        except Exception as e:
            self.assertIsInstance(e, FileNotFoundError)

        token = find_neon_git_token(CRED_PATH)
        self.assertEqual(token, "github token goes here")

    def test_get_aws_credentials(self):
        try:
            keys = find_neon_aws_keys("/tmp")
            self.assertEqual(list(keys.keys()), ["aws_access_key_id", "aws_secret_access_key"])
        except Exception as e:
            self.assertIsInstance(e, FileNotFoundError)

        keys = find_neon_aws_keys(CRED_PATH)
        self.assertEqual(keys, {"aws_access_key_id": "FAKE_KEY_ID",
                                "aws_secret_access_key": "FAKE_SECRET/"})

    def test_get_google_credentials(self):
        try:
            creds = find_neon_google_keys("/tmp")
            self.assertIsInstance(creds, dict)
        except Exception as e:
            self.assertIsInstance(e, FileNotFoundError)

        creds = find_neon_google_keys(CRED_PATH)
        self.assertEqual(list(creds.keys()), ["type", "project_id", "private_key_id", "private_key", "client_email",
                                              "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url",
                                              "client_x509_cert_url"])
        self.assertEqual(creds["private_key"],
                         "-----BEGIN PRIVATE KEY-----\nREDACTED\nREDACTED\nREDACTED\n-----END PRIVATE KEY-----\n")

    def test_get_wolfram_key(self):
        try:
            key = find_neon_wolfram_key("/tmp")
            self.assertIsInstance(key, str)
        except Exception as e:
            self.assertIsInstance(e, FileNotFoundError)

        key = find_neon_wolfram_key(CRED_PATH)
        self.assertEqual(key, "RED-ACTED")

    def test_get_alpha_vantage_key(self):
        try:
            key = find_neon_alpha_vantage_key("/tmp")
            self.assertIsInstance(key, str)
        except Exception as e:
            self.assertIsInstance(e, FileNotFoundError)

        key = find_neon_alpha_vantage_key(CRED_PATH)
        self.assertEqual(key, "Alpha-Vantage")

    def test_get_owm_key(self):
        try:
            key = find_neon_owm_key("/tmp")
            self.assertIsInstance(key, str)
        except Exception as e:
            self.assertIsInstance(e, FileNotFoundError)

        key = find_neon_owm_key(CRED_PATH)
        self.assertEqual(key, "OpenWeatherMap")

    def test_write_github_token(self):
        config_path = os.path.join(ROOT_DIR, "configuration")
        token = "TOKEN"
        local_config = get_neon_local_config(config_path)
        self.assertIsNone(local_config["skills"]["neon_token"])
        populate_github_token_config(token, config_path)
        self.assertEqual(local_config["skills"]["neon_token"], token)

    def test_write_aws_credentials(self):
        config_path = os.path.join(ROOT_DIR, "configuration")
        local_config = get_neon_local_config(config_path)
        self.assertEqual(local_config["tts"]["amazon"], {"region": "us-west-2",
                                                         "aws_access_key_id": "",
                                                         "aws_secret_access_key": ""})
        populate_amazon_keys_config({"aws_access_key_id": "KEY_ID",
                                     "aws_secret_access_key": "KEY_SECRET"}, config_path)
        self.assertEqual(local_config["tts"]["amazon"], {"region": "us-west-2",
                                                         "aws_access_key_id": "KEY_ID",
                                                         "aws_secret_access_key": "KEY_SECRET"})

    def test_aws_credentials_missing_keys(self):
        with self.assertRaises(AssertionError):
            populate_amazon_keys_config({})

        with self.assertRaises(AssertionError):
            populate_amazon_keys_config({"aws_access_key_id": ""})
        with self.assertRaises(AssertionError):
            populate_amazon_keys_config({"aws_secret_access_key": ""})

    def test_aws_credentials_invalid_keys(self):
        with self.assertRaises(ValueError):
            populate_amazon_keys_config({"aws_access_key_id": "",
                                         "aws_secret_access_key": ""})

    def test_repo_is_neon_valid(self):
        self.assertTrue(repo_is_neon("http://github.com/NeonGeckoCom/alerts.neon"))
        self.assertTrue(repo_is_neon("https://github.com/NeonGeckoCom/caffeinewiz.neon"))
        self.assertTrue(repo_is_neon("ssh://github.com/NeonGeckoCom/launcher.neon"))

        self.assertTrue(repo_is_neon("https://github.com/neondaniel/speedtest.neon"))

        self.assertFalse(repo_is_neon("https://github.com/mycroftai/skill-alarm"))
        self.assertFalse(repo_is_neon("http://gitlab.com/neongecko/some-skill"))

    def test_repo_is_neon_invalid(self):
        with self.assertRaises(ValueError):
            repo_is_neon("https://github.com")
        with self.assertRaises(ValueError):
            repo_is_neon("not a url")
        with self.assertRaises(ValueError):
            repo_is_neon("")

    def test_build_new_auth_config(self):
        config = build_new_auth_config(CRED_PATH)
        self.assertEqual(set(config.keys()), {"github", "amazon", "wolfram", "google", "alpha_vantage", "owm"})
        for key in config.keys():
            self.assertIsInstance(config[key], dict)
            self.assertTrue(config[key])


if __name__ == '__main__':
    unittest.main()
