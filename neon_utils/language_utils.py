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
import boto3
from neon_utils.logger import LOG
from neon_utils.configuration_utils import get_neon_lang_config, NGIConfig, get_neon_tts_config


def get_language_dir(base_path, lang="en-us"):
    """ checks for all language variations and returns best path """
    lang_path = os.path.join(base_path, lang)
    # base_path/en-us
    if os.path.isdir(lang_path):
        return lang_path
    if "-" in lang:
        main = lang.split("-")[0]
        # base_path/en
        general_lang_path = os.path.join(base_path, main)
        if os.path.isdir(general_lang_path):
            return general_lang_path
    else:
        main = lang
    # base_path/en-uk, base_path/en-au...
    if os.path.isdir(base_path):
        candidates = [os.path.join(base_path, f)
                      for f in os.listdir(base_path) if f.startswith(main)]
        paths = [p for p in candidates if os.path.isdir(p)]
        # TODO how to choose best local dialect?
        if len(paths):
            return paths[0]
    return os.path.join(base_path, lang)


class LanguageDetector:
    def __init__(self):
        self.config = get_neon_lang_config()
        self.default_language = self.config["user"].split("-")[0]
        # hint_language: str  E.g., 'ITALIAN' or 'it' boosts Italian
        self.hint_language = self.config["user"].split("-")[0]
        self.boost = self.config.get("boost")

    def detect(self, text):
        # assume default language
        return self.default_language

    def detect_probs(self, text):
        return {self.detect(text): 1}


class LanguageTranslator:
    def __init__(self):
        self.config = get_neon_lang_config()
        self.boost = self.config["boost"]
        self.default_language = self.config["user"].split("-")[0]
        self.internal_language = self.config["internal"]

    def translate(self, text, target=None, source=None):
        return text


class GoogleDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        from ovos_utils.lang.detect import detect_lang
        import logging
        logging.getLogger("hyper.http20.connection").setLevel("ERROR")
        self._detect = detect_lang

    def detect(self, text):
        return self._detect(text) or self.default_language

    def detect_probs(self, text):
        lang = self._detect(text, True)
        return {lang["lang_code"]: lang["conf"]}


class FastLangDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        try:
            from fastlang import fastlang
        except ImportError:
            LOG.error("Run pip install fastlang")
            raise
        self._detect = fastlang

    def detect(self, text):
        return self._detect(text)["lang"]

    def detect_probs(self, text):
        return self._detect(text)["probabilities"]


class LangDetectDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        try:
            from langdetect import detect, detect_langs
        except ImportError:
            LOG.error("Run pip install langdetect")
            raise
        self._detect = detect
        self._detect_prob = detect_langs

    def detect(self, text):
        return self._detect(text)

    def detect_probs(self, text):
        langs = {}
        for lang in self._detect_prob(text):
            langs[lang.lang] = lang.prob
        return langs


class GoogleTranslator(LanguageTranslator):
    def __init__(self):
        super().__init__()
        from ovos_utils.lang.translate import translate_text
        self._translate = translate_text

    def translate(self, text, target=None, source=None):
        if self.boost and not source:
            source = self.default_language
        target = target or self.internal_language
        return self._translate(text, target, source)


class AmazonTranslator(LanguageTranslator):
    def __init__(self):
        super().__init__()
        # TODO: Replace private key function DM
        # self.keys = get_private_keys()["amazon"]
        self.keys = get_neon_tts_config()["amazon"]
        self.client = boto3.Session(aws_access_key_id=self.keys["aws_access_key_id"],
                                    aws_secret_access_key=self.keys["aws_secret_access_key"],
                                    region_name=self.keys["region"]).client('translate')

    def translate(self, text, target=None, source="auto"):
        target = target or self.internal_language

        response = self.client.translate_text(
            Text=text,
            SourceLanguageCode=source,
            TargetLanguageCode=target.split("-")[0]
        )
        return response["TranslatedText"]


class AmazonDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        # TODO: Replace private key funciton DM
        # self.keys = get_private_keys()["amazon"]
        self.keys = get_neon_tts_config()["amazon"]

        self.client = boto3.Session(aws_access_key_id=self.keys["aws_access_key_id"],
                                    aws_secret_access_key=self.keys["aws_secret_access_key"],
                                    region_name=self.keys["region"]).client('comprehend')

    def detect(self, text):
        response = self.client.detect_dominant_language(
            Text=text
        )
        return response['Languages'][0]['LanguageCode']

    def detect_probs(self, text):
        response = self.client.detect_dominant_language(
            Text=text
        )
        langs = {}
        for lang in response["Languages"]:
            langs[lang["LanguageCode"]] = lang["Score"]
        return langs


class MyMemoryTranslator(LanguageTranslator):
    def __init__(self):
        super().__init__()

    def translate(self, text, target=None, source="auto"):
        from translate import Translator
        target = target or self.internal_language
        # TODO: This doesn't appear to work DM
        translated = Translator(to_lang=target).translate(text)
        LOG.info(translated)
        return translated


class TranslatorFactory:
    CLASSES = {
        "google": GoogleTranslator,
        "amazon": AmazonTranslator,
        # "mymemory": MyMemoryTranslator
    }

    @staticmethod
    def create(module=None):
        module = module or "amazon"
        config = get_neon_lang_config()
        module = module or config.get("translation_module", "google")
        # TODO: Check file locations DM
        if module == "amazon" \
                and get_neon_tts_config()["amazon"].get("aws_access_key_id", "") == "":
            from neon_utils.authentication_utils import find_neon_aws_keys, populate_amazon_keys_config
            try:
                config_keys = find_neon_aws_keys()
                populate_amazon_keys_config(config_keys)
            except FileNotFoundError:
                LOG.debug("Amazon credentials not available")
                module = "google"
            except Exception as e:
                LOG.error(e)
                module = "google"
        try:
            clazz = TranslatorFactory.CLASSES.get(module)
            return clazz()
        except Exception as e:
            # The translate backend failed to start. Report it and fall back to
            # default.
            LOG.exception('The selected translator backend could not be loaded, '
                          'falling back to default...')
            LOG.error(e)
            if module != 'google':
                return GoogleTranslator()
            else:
                raise


class DetectorFactory:
    CLASSES = {
        "amazon": AmazonDetector,
        "google": GoogleDetector,
        "fastlang": FastLangDetector,
        "detect": LangDetectDetector
    }

    @staticmethod
    def create(module=None):
        module = module or "fastlang"
        config = get_neon_lang_config()
        module = module or config.get("detection_module", "fastlang")
        try:
            clazz = DetectorFactory.CLASSES.get(module)
            return clazz()
        except Exception as e:
            # The translate backend failed to start. Report it and fall back to
            # default.
            LOG.exception('The selected language detector backend could not be loaded, '
                          'falling back to default...')
            LOG.error(e)
            if module != 'fastlang':
                return FastLangDetector()
            else:
                raise
