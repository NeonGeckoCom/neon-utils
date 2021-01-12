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

from mycroft_bus_client import Message

from neon_utils.logger import LOG


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
    return {'first_name': '',
            'middle_name': '',
            'last_name': '',
            'preferred_name': '',
            'full_name': '',
            'dob': 'YYYY/MM/DD',
            'age': '',
            'email': '',
            'username': '',
            'password': '',
            'picture': '',
            'about': '',
            'phone': '',
            'email_verified': False,
            'phone_verified': False
            }


def preference_location(message: Message):
    return {'lat': 47.4799078,
            'lng': -122.2034496,
            'city': 'Renton',
            'state': 'Washington',
            'country': 'USA',
            'tz': 'America/Los_Angeles',
            'utc': -8.0
            }


def preference_unit(message: Message):
    return {'time': 12,
            'date': 'MDY',
            'measure': 'imperial'
            }


def preference_speech(message: Message):
    return {'stt_language': 'en',
            'stt_region': 'US',
            'alt_languages': ['en'],
            'tts_language': "en-us",
            'tts_gender': 'female',
            'neon_voice': 'Joanna',
            'secondary_tts_language': '',
            'secondary_tts_gender': '',
            'secondary_neon_voice': '',
            'speed_multiplier': 1.0,
            'synonyms': {}
            }


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
    from neon_utils import SKILL, TYPE
    super(TYPE, SKILL).speak_dialog(key, data, expect_response, wait)


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
    from neon_utils import SKILL, TYPE
    super(TYPE, SKILL).speak(utterance, expect_response, wait, meta)


def create_signal(signal_name):
    """Create a named signal. i.e. "CORE_signalName" or "nick_SKILL_signalName
    Args:
        signal_name (str): The signal's name.  Must only contain characters
            valid in filenames.
    """
    try:
        path = os.path.join('/tmp/mycroft/ipc', "signal", signal_name)
        _create_file(path)
        return os.path.isfile(path)
    except IOError:
        return False


def clear_signals(prefix):
    """
    Clears all signals that begin with the passed prefix. Used with skill prefix for a skill to clear any signals it
    may have set
    :param prefix: (str) prefix to match
    """
    os.makedirs("tmp/mycroft/ipc/signal", exist_ok=True)
    for signal in os.listdir("tmp/mycroft/ipc/signal"):
        if str(signal).startswith(prefix) or f"_{prefix}_" in str(signal):
            os.remove(os.path.join("tmp/mycroft/ipc/signal", signal))


def check_for_signal(signal_name, sec_lifetime=0):
    """See if a named signal exists

    Args:
        signal_name (str): The signal's name.  Must only contain characters
            valid in filenames.
        sec_lifetime (int, optional): How many seconds the signal should
            remain valid.  If 0 or not specified, it is a single-use signal.
            If -1, it never expires.

    Returns:
        bool: True if the signal is defined, False otherwise
    """
    import time
    path = os.path.join('/tmp/neon/ipc', "signal", signal_name)
    if os.path.isfile(path):
        # noinspection PyTypeChecker
        if sec_lifetime == 0:
            # consume this single-use signal
            try:
                os.remove(path)
            except Exception as x:
                print(' >>> ERROR removing signal ' + signal_name + ', error == ' + str(x))

        elif sec_lifetime == -1:
            return True
        elif int(os.path.getctime(path) + sec_lifetime) < int(time.time()):
            # remove once expired
            os.remove(path)
            return False
        return True

    # No such signal exists
    return False


def _create_file(filename):
    """ Create the file filename and create any directories needed

        Args:
            filename: Path to the file to be created
    """
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass
    with open(filename, 'w') as f:
        f.write('')


def request_check_timeout(time_wait, intent_to_check):
    pass


def get_utterance_user(message):
    return "local"


def get_cached_data(filename, file_loc=None):
    """
    Retrieves cache data from a file created/updated with update_cached_data
    :param filename: (str) filename of cache object to update
    :param file_loc: (str) path to directory containing filename (defaults to cache dir)
    :return: (dict) cache data
    """
    import pickle
    import pathlib

    from neon_utils import SKILL

    if not file_loc:
        file_loc = SKILL.cache_loc
    cached_location = os.path.join(file_loc, filename)
    if pathlib.Path(cached_location).exists():
        with open(cached_location, 'rb') as file:
            return pickle.load(file)
    else:
        return {}


def update_cached_data(filename, new_element):
    """
    Updates cache file of skill responses to translated responses when non-english responses are requested.
    :param filename: (str) filename of cache object to update (relative to cacheDir)
    :param new_element: (any) object to cache at passed location
    """
    import pickle

    from neon_utils import SKILL

    with open(os.path.join(SKILL.cache_loc, filename), 'wb+') as file_to_update:
        pickle.dump(new_element, file_to_update, protocol=pickle.HIGHEST_PROTOCOL)


def build_message(kind, utt, message, signal_to_check=None, speaker=None):
    """
    Build a message for user input or neon response
    :param kind: "neon speak" or "execute"
    :param utt: string to emit
    :param message: incoming message object
    :param signal_to_check: signal to check in speech
    :param speaker: speaker data dictionary
    :return: Message object
    """
    from copy import deepcopy

    from neon_utils import SKILL
    # utt = utt.strip('"')  This is done before calling build_message now

    # Use utt as default signal to check
    if not signal_to_check:
        signal_to_check = utt
    LOG.debug(speaker)

    default_speech = SKILL.preference_speech(message)
    # Override user preference for all script responses
    if not speaker:
        speaker = {"name": "Neon",
                   "language": default_speech["tts_language"],
                   "gender": default_speech["tts_gender"],
                   "voice": default_speech["neon_voice"],
                   "override_user": True}
    else:
        speaker["override_user"] = True

    LOG.debug(f"data={message.data}")
    LOG.debug(f"context={message.context}")

    emit_response = False
    if kind == "skill_data":
        emit_response = True
        kind = "execute"

    try:
        if kind == "execute":
            # This is picked up in the intent handler
            return message.reply("skills:execute.utterance", {
                "utterances": [utt.lower()],
                "lang": message.data.get("lang", "en-US"),
                "session": None,
                "ident": None,
                "speaker": speaker
            }, {
                # "mobile": message.context.get("mobile", False),
                # "client": message.context.get("client", None),
                # "flac_filename": message.context.get("flac_filename", ''),
                # "nick_profiles": message.context.get("nick_profiles", {}),
                "neon_should_respond": True,
                "cc_data": {"signal_to_check": signal_to_check,
                            "request": utt,
                            "emit_response": emit_response,
                            # "Neon": True,
                            "execute_from_script": True,
                            "audio_file": message.context["cc_data"].get("audio_file", None),
                            "raw_utterance": utt
                            }
            })
        elif kind == "neon speak":
            context = deepcopy(message.context)
            context["cc_data"]["signal_to_check"] = signal_to_check
            context["cc_data"]["request"] = utt

            return message.reply("speak", {"lang": message.data.get("lang", "en-US"),
                                           "speaker": speaker
                                           }, context)
    except Exception as x:
        LOG.error(x)
