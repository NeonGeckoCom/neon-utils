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
import time
from typing import Optional

from mycroft_bus_client import Message
from neon_utils.logger import LOG
from neon_utils.configuration_utils import get_neon_local_config

IPC_DIR = get_neon_local_config()["dirVars"]["ipcDir"]


def neon_must_respond(message: Message) -> bool:
    return True


def neon_in_request(message: Message) -> bool:
    return True


def request_from_mobile(message: Message) -> bool:
    if message.context.get("mobile"):
        return True
    return False


def preference_brands(message: Message) -> dict:
    return {'ignored_brands': {},
            'favorite_brands': {},
            'specially_requested': {}}


def preference_user(message: Message) -> dict:
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


def preference_location(message: Message) -> dict:
    return {'lat': 47.4799078,
            'lng': -122.2034496,
            'city': 'Renton',
            'state': 'Washington',
            'country': 'USA',
            'tz': 'America/Los_Angeles',
            'utc': -8.0
            }


def preference_unit(message: Message) -> dict:
    return {'time': 12,
            'date': 'MDY',
            'measure': 'imperial'
            }


def preference_speech(message: Message) -> dict:
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


def update_skill_settings(new_settings: dict, message: Message):
    from neon_utils import SKILL
    for pref, val in new_settings.items():
        SKILL.settings[pref] = val


def preference_skill(message: Message) -> dict:
    from neon_utils import SKILL
    return SKILL.settings


def build_user_dict(message: Message = None) -> dict:
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


def create_signal(signal_name: str) -> bool:
    """Create a named signal. i.e. "CORE_signalName" or "nick_SKILL_signalName
    Args:
        signal_name (str): The signal's name.  Must only contain characters
            valid in filenames.
    """
    LOG.warning("This method and signal use are deprecated and will not work in some configurations")
    try:
        path = os.path.join(IPC_DIR, "signal", signal_name)
        _create_file(path)
        return os.path.isfile(path)
    except IOError:
        return False


def clear_signals(prefix: str):
    """
    Clears all signals that begin with the passed prefix. Used with skill prefix for a skill to clear any signals it
    may have set
    :param prefix: (str) prefix to match
    """
    LOG.warning("This method and signal use are deprecated and will not work in some configurations")
    os.makedirs(f"{IPC_DIR}/signal", exist_ok=True)
    for signal in os.listdir(f"{IPC_DIR}/signal"):
        if str(signal).startswith(prefix) or f"_{prefix}_" in str(signal):
            os.remove(os.path.join(f"{IPC_DIR}/signal", signal))


def check_for_signal(signal_name: str, sec_lifetime: Optional[int] = 0):
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
    # TODO: Log deprecation warning after isSpeaking check is refactored DM
    # LOG.warning("This method and signal use are deprecated and will not work in some configurations")
    import time
    path = os.path.join(IPC_DIR, "signal", signal_name)  # /tmp/neon/ipc/signal/isSpeaking
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


def _create_file(filename: str):
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


def get_utterance_user(message) -> str:
    return "local"


def get_cached_data(filename: str, file_loc: Optional[str] = None) -> dict:
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


def update_cached_data(filename: str, new_element):
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
        if kind in ("execute", "skill"):
            message.context["cc_data"] = message.context.get("cc_data", {})
            # This is picked up in the intent handler
            # return message.reply("skills:execute.utterance", {
            return message.reply("recognizer_loop:utterance", {
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
            LOG.info(f"CONTEXT IS {context}")
            context["cc_data"] = context.get("cc_data", {})
            context["cc_data"]["signal_to_check"] = signal_to_check
            context["cc_data"]["request"] = utt

            return message.reply("speak", {"lang": message.data.get("lang", "en-US"),
                                           "speaker": speaker
                                           }, context)
    except Exception as x:
        LOG.error(x)


def to_system_time(dt):
    """
    Converts a timezone aware datetime object to an object to be used in the messagebus scheduler
    :param dt: datetime object to convert
    :return: timezone aware datetime object that can be scheduled
    """
    from dateutil.tz import tzlocal, gettz

    tz = tzlocal()
    if dt.tzinfo:
        return dt.astimezone(tz)
    else:
        return dt.replace(tzinfo=gettz("UTC")).astimezone(tz)


def speak(utterance, expect_response=False, wait=False, meta=None, message=None, private=False, speaker=None):
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
    from neon_utils import SKILL

    # registers the skill as being active
    meta = meta or {}
    meta['skill'] = SKILL.name
    SKILL.enclosure.register(SKILL.name)
    if utterance:
        LOG.debug(f">>>>> Skill speak! {utterance}")

        # Find the associated message
        if message:
            LOG.info('message passed to speak = ' + str(message.data))
            if not speaker:
                speaker = message.data.get("speaker", None)
        else:
            LOG.debug('message is None.')
            message = dig_for_message()

        if message:
            # filename = message.context.get("flac_filename", "")
            # cc_data = message.context.get("cc_data", {})
            # profiles = message.context.get("nick_profiles", {})
            if not speaker:
                speaker = message.data.get("speaker", speaker)
            # if message.data['flac_filename']:
            #     filename = message.data['flac_filename']
            # else:
            #     filename = ''
        else:
            message = dig_for_message()
            filename = ''
            # cc_data = {}
            # profiles = {}
            if message:
                # filename = message.context.get("flac_filename", "")
                # cc_data = message.context.get("cc_data", {})
                # profiles = message.context.get("nick_profiles", {})
                if not speaker:
                    speaker = message.data.get("speaker", {})

        # registers the skill as being active
        # print(f'{cc_data} is cc_data')
        # self.enclosure.register(self.name)
        nick = ""
        # LOG.debug(nick)
        data = {"utterance": utterance,
                "expect_response": expect_response,
                "meta": meta,
                "speaker": speaker}

        # devices might not want to do these logs either... weird characters cause a logging error
        if not SKILL.server:
            LOG.info(f'{speaker} Speak: {utterance}')
            # LOG.info('Speak data = ' + str(data))
        # LOG.info(filename)
        if not message:
            message = dig_for_message()

        if message and message.context.get("cc_data", {}).get("emit_response"):
            LOG.debug(f"DM: {data}")
            msg_to_emit = message.reply("skills:execute.response", data)

        elif message and message.msg_type != "mycroft.ready":
            message.context.get("timing", {})["speech_start"] = time.time()
            LOG.info("message True, " + str(data))
            # LOG.info(message)
            # TODO: This is where we have the most complete timing profile for an utterance
            # LOG.debug(f"TIME: to_speak, {time.time()}, {message.context['flac_filename']}, {data['utterance']}, "
            #           f"{message.context}")
            # self.bus.emit(message.reply("speak", data))
            msg_to_emit = message.reply("speak", data)
            LOG.debug(f">>>> Skill speak! {data}, {message.context}")
        else:
            LOG.warning("message False, " + str(data))
            # self.bus.emit(Message("speak", data))
            msg_to_emit = Message("speak", data)
        LOG.debug(msg_to_emit.msg_type)
        SKILL.bus.emit(msg_to_emit)
    else:
        LOG.warning("Null utterance passed to speak")
        LOG.warning(f"{SKILL.name} | message={message}")

    if wait:
        wait_while_speaking()


def dig_for_message():
    """Dig Through the stack for message."""
    import inspect

    stack = inspect.stack()
    # Limit search to 10 frames back
    stack = stack if len(stack) < 10 else stack[:10]
    local_vars = [frame[0].f_locals for frame in stack]
    for var in local_vars:
        if 'message' in var and isinstance(var['message'], Message):
            return var['message']


# TODO: Are the below methods from elsewhere in core (not skills)? DM
def wait_while_speaking():
    """Pause as long as Text to Speech is still happening

    Pause while Text to Speech is still happening.  This always pauses
    briefly to ensure that any preceding request to speak has time to
    begin.
    """
    LOG.debug("Wait while speaking!")
    time.sleep(0.3)  # Wait briefly in for any queued speech to begin
    while is_speaking():
        time.sleep(0.1)


def is_speaking(sec_lifetime=-1):
    """Determine if Text to Speech is occurring

    Args:
        sec_lifetime (int, optional): How many seconds the signal should
            remain valid.  If 0 or not specified, it is a single-use signal.
            If -1, it never expires.

    Returns:
        bool: True while still speaking
    """
    return check_for_signal("isSpeaking", sec_lifetime)


def check_yes_no_response(message):
    """
    Used in converse methods to check if a response confirms or declines an action. Differs from ask_yesno in that
    this does not assume input will be spoken with wake words enabled
    :param message: incoming message object to evaluate
    :return: False if declined, numbers if confirmed numerically, True if confirmed with no numbers
    """
    from neon_utils import SKILL

    utterance = message.data.get("utterances")[0]
    if SKILL.voc_match(utterance, "no"):
        LOG.info("User Declined")
        return False
    elif SKILL.voc_match(utterance, "yes"):
        LOG.info("User Accepted")
        numbers = [str(s) for s in utterance.split() if s.isdigit()]
        if numbers and len(numbers) > 0:
            confirmation = "".join(numbers)
            LOG.info(f"Got confirmation: {confirmation}")
            return confirmation
        return True
    else:
        LOG.debug("User response not valid")
        return -1
