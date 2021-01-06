# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2020 Neongecko.com Inc. | All Rights Reserved
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
# US Patents 2008-2020: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

from mycroft_bus_client import Message


def neon_must_respond(message: Message):
    return True


def neon_in_request(message: Message):
    return True


def request_from_mobile(message: Message):
    return True


def preference_brands(message: Message):
    return {'ignored_brands': {},
            'favorite_brands': {},
            'specially_requested': {}}


def preference_user(message: Message):
    return {}


def preference_location(message: Message):
    return {}


def preference_unit(message: Message):
    return {}


def preference_speech(message: Message):
    return {}


def build_user_dict(message: Message = None):
    merged_dict = {**preference_speech(message), **preference_user(message),
                   **preference_brands(message), **preference_location(message),
                   **preference_unit(message)}
    for key, value in merged_dict.items():
        if value == "":
            merged_dict[key] = -1
    return merged_dict


def speak_dialog(key, data=None, expect_response=False, message=None, private=False, speaker=None, wait=False):
    """ Speak a random sentence from a dialog file.

    Arguments:
        :param key: dialog file key (e.g. "hello" to speak from the file "locale/en-us/hello.dialog")
        :param data: information used to populate key
        :param expect_response: set to True if Mycroft should listen for a response immediately after speaking.
        :param wait: set to True to block while the text is being spoken.
        :param speaker: optional dict of speaker info to use
        :param private: private flag (server use only)
        :param message: associated message from request
    """
    super().speak_dialog(key, data, expect_response, wait)


def speak(utterance, expect_response=False, message=None, private=False, speaker=None, wait=False, meta=None):
    """
    Speak a sentence.
    Arguments:
        utterance (str):        sentence mycroft should speak
        expect_response (bool): set to True if Mycroft should listen for a response immediately after
                                speaking the utterance.
        message (Message):      message associated with the input that this speak is associated with
        private (bool):         flag to indicate this message contains data that is private to the requesting user
        speaker (dict):         dict containing language or voice data to override user preference values
        wait (bool):            set to True to block while the text is being spoken.
        meta:                   Information of what built the sentence.
    """
    super().speak(utterance, expect_response, wait, meta)
