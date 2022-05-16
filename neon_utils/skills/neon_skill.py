# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
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

import pathlib
import pickle
import json
import time
import os

from copy import deepcopy
from functools import wraps
from json_database import JsonStorage
from mycroft.skills.settings import save_settings
from mycroft_bus_client.message import Message
from typing import Optional, List, Any
from dateutil.tz import gettz
from ovos_utils.gui import is_gui_running

from neon_utils.signal_utils import create_signal, check_for_signal
from neon_utils.configuration_utils import is_neon_core, \
    get_neon_lang_config, get_neon_user_config, get_neon_local_config
from neon_utils.location_utils import to_system_time
from neon_utils.logger import LOG
from neon_utils.message_utils import request_from_mobile, get_message_user, dig_for_message, resolve_message
from neon_utils.cache_utils import LRUCache
from neon_utils.mq_utils import send_mq_request
from neon_utils.skills.mycroft_skill import PatchedMycroftSkill as MycroftSkill
from neon_utils.file_utils import get_most_recent_file_in_dir, resolve_neon_resource_file

try:
    from ovos_plugin_manager.language import OVOSLangDetectionFactory, OVOSLangTranslationFactory
except ImportError as e:
    OVOSLangDetectionFactory, OVOSLangTranslationFactory = None, None

# TODO if accepted, make changes to QASkill and WikipediaSkill
# Available_modes are 1) quick; 2) thoughtful.
SPEED_MODE_EXTENSION_TIME = {
    "quick": 1,
    "thoughtful": 10
}
DEFAULT_SPEED_MODE = "thoughtful"
CACHE_TIME_OFFSET = 24*60*60  # seconds in 24 hours


class NeonSkill(MycroftSkill):
    def __init__(self, name=None, bus=None, use_settings=True):
        super(NeonSkill, self).__init__(name, bus, use_settings)
        self.user_config = get_neon_user_config()
        self.local_config = get_neon_local_config()
        self.cache_loc = os.path.expanduser(
            self.local_config.get('dirVars', {}).get('cacheDir') or
            "~/.local/share/neon/cache")
        if not os.path.isdir(self.cache_loc):
            LOG.debug(f"Creating cache directory: {self.cache_loc}")
            os.makedirs(self.cache_loc, exist_ok=True)
        self.lru_cache = LRUCache()

        # TODO: Depreciate these references, signal use is discouraged DM
        self.create_signal = create_signal
        self.check_for_signal = check_for_signal

        self.sys_tz = gettz()
        self.gui_enabled = self.local_config.get("prefFlags",
                                                 {}).get("guiEvents", False)

        self.scheduled_repeats = []

        # Server-specific imports and timeout setting
        # A server is a device that hosts the core and skills to serve clients,
        # but that a user will not interact with directly.
        # A server will likely serve multiple users and devices concurrently.
        if self.local_config.get("devVars", {}).get("devType",
                                                    "generic") == "server":
            self.server = True
            self.default_intent_timeout = 90
        else:
            self.server = False
            self.default_intent_timeout = 60

        try:
            import neon_core
            self.neon_core = True
        except ImportError:
            self.neon_core = False

        self.actions_to_confirm = dict()

        self.skill_mode = self.user_config.content.get(
            'response_mode', {}).get('speed_mode') or DEFAULT_SPEED_MODE
        self.extension_time = SPEED_MODE_EXTENSION_TIME.get(self.skill_mode)

        # TODO: Consider moving to properties to avoid unused init? DM
        try:
            if not OVOSLangDetectionFactory:
                LOG.info("OPM not available, skipping language plugin load")
                self.lang_detector, self.translator = None, None
            else:
                language_config = get_neon_lang_config()
                self.lang_detector = \
                    OVOSLangDetectionFactory.create(language_config)
                self.translator = \
                    OVOSLangTranslationFactory.create(language_config)
        except ValueError as e:
            LOG.error(f"Configured lang plugins not available: {e}")
            self.lang_detector, self.translator = None, None

    def initialize(self):
        # schedule an event to load the cache on disk every CACHE_TIME_OFFSET seconds
        self.schedule_event(self._write_cache_on_disk, CACHE_TIME_OFFSET,
                            name="neon.load_cache_on_disk")

    @property
    def user_info_available(self):
        LOG.warning("This reference is deprecated, "
                    "use self.preference_x methods for user preferences")
        return self.user_config.content

    @property
    def configuration_available(self):
        LOG.warning("This reference is deprecated, use self.local_config directly")
        return self.local_config.content

    @property
    def ngi_settings(self):
        LOG.error("This reference is depreciated. "
                  "Use self.preference_skill for per-user skill settings")
        return self.preference_skill()

    @property
    def location_timezone(self) -> str:
        """Get the timezone code, such as 'America/Los_Angeles'"""
        LOG.warning("This method does not support user-specific location and will use device default")
        return self.preference_location()["tz"]

    def preference_brands(self, message=None) -> dict:
        """
        Returns a brands dictionary for the user
        Equivalent to self.user_config["speech"] for non-server use
        """
        try:
            nick = get_message_user(message) if message else None
            if self.server:
                if not message or not nick:
                    LOG.warning("No message given!")
                    return self.user_config['brands']

                if message.context.get("nick_profiles"):
                    return message.context["nick_profiles"][nick]["brands"]
                else:
                    LOG.error(f"Unable to get user settings! message={message.data}")
            else:
                return self.user_config['brands']
        except Exception as x:
            LOG.error(x)
        return {'ignored_brands': {},
                'favorite_brands': {},
                'specially_requested': {}}

    def preference_user(self, message=None) -> dict:
        """
        Returns the user dictionary with name, email
        Equivalent to self.user_config["user"] for non-server use
        """
        try:
            nick = get_message_user(message) if message else None
            if self.server:
                if not message or not nick:
                    LOG.warning("No message given!")
                    return self.user_config['user']
                if message.context.get("nick_profiles"):
                    return message.context["nick_profiles"][nick]["user"]
                else:
                    LOG.error(f"Unable to get user settings! message={message.data}")
            else:
                return self.user_config['user']
        except Exception as x:
            LOG.error(x)
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

    def preference_location(self, message=None) -> dict:
        """
        Get the JSON data structure holding location information.
        Equivalent to self.user_config["location"] for non-server use
        """
        try:
            nick = get_message_user(message) if message else None
            if self.server:
                if not message or not nick:
                    LOG.warning("No message given!")
                    return self.user_config['location']
                if message.context.get("nick_profiles"):
                    return message.context["nick_profiles"][nick]["location"]
                else:
                    LOG.error(f"Unable to get user settings! message={message.data}")
            else:
                return self.user_config['location']
        except Exception as x:
            LOG.error(x)
        return {'lat': 47.4799078,
                'lng': -122.2034496,
                'city': 'Renton',
                'state': 'Washington',
                'country': 'USA',
                'tz': 'America/Los_Angeles',
                'utc': -8.0
                }

    def preference_unit(self, message=None) -> dict:
        """
        Returns the units dictionary that contains time, date, measure formatting preferences
        Equivalent to self.user_config["units"] for non-server use
        """
        try:
            nick = get_message_user(message) if message else None
            if self.server:
                if not message or not nick:
                    LOG.warning("No message given!")
                    return self.user_config['units']

                if message.context.get("nick_profiles"):
                    return message.context["nick_profiles"][nick]["units"]
                else:
                    LOG.error(f"Unable to get user settings! message={message.data}")
            else:
                return self.user_config['units']
        except Exception as x:
            LOG.error(x)
        return {'time': 12,
                'date': 'MDY',
                'measure': 'imperial'
                }

    def preference_speech(self, message=None) -> dict:
        """
        Returns the speech dictionary that contains language and spoken response preferences
        Equivalent to self.user_config["speech"] for non-server use
        """
        try:
            nick = get_message_user(message) if message else None
            if self.server:
                if not message or not nick:
                    LOG.warning("No message given!")
                    return self.user_config['speech']

                if message.context.get("nick_profiles"):
                    return message.context["nick_profiles"][nick]["speech"]
                else:
                    LOG.error(f"Unable to get user settings! message={message.data}")
            else:
                return self.user_config['speech']
        except Exception as x:
            LOG.error(x)
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

    def preference_skill(self, message=None) -> dict:
        """
        Returns the skill settings configuration
        Equivalent to self.settings for non-server
        :param message: Message associated with request
        :return: dict of skill preferences
        """
        nick = get_message_user(message) if message else None
        if self.server and nick:
            try:
                skill = self.skill_id
                LOG.info(f"Get server prefs for skill={skill}")
                user_overrides = message.context["nick_profiles"][nick]["skills"].get(self.skill_id, dict())
                LOG.debug(user_overrides)
                merged_settings = {**self.settings, **user_overrides}
                if user_overrides.keys() != merged_settings.keys():
                    LOG.info(f"New settings keys: user={nick}|skill={self.skill_id}|user={user_overrides}")
                    self.update_skill_settings(merged_settings, message)
                return merged_settings
            except Exception as e:
                LOG.error(e)
        return self.settings

    def build_user_dict(self, message=None) -> dict:
        """
        Builds a merged dictionary containing all user preferences in a single-level dictionary.
        Used to build a dictionary for server profile updates
        :param message: Message associate with request
        """
        merged_dict = {**self.preference_speech(message), **self.preference_user(message),
                       **self.preference_brands(message), **self.preference_location(message),
                       **self.preference_unit(message)}
        for key, value in merged_dict.items():
            if value == "":
                merged_dict[key] = -1
        return merged_dict

    def build_combined_skill_object(self, message=None) -> list:
        # TODO: Depreciated? DM
        LOG.error(f"This method is depreciated!")
        user = self.get_utterance_user(message)
        skill_dict = message.context["nick_profiles"][user]["skills"]
        skill_list = list(skill_dict.values())
        return skill_list

    def update_profile(self, new_preferences: dict, message: Message = None):
        """
        Updates a user profile with the passed new_preferences
        :param new_preferences: dict of updated preference values. Should follow {section: {key: val}} format
        :param message: Message associated with request
        """
        if self.server:
            nick = get_message_user(message) if message else None
            new_skills_prefs = new_preferences.pop("skills")
            old_skills_prefs = message.context["nick_profiles"][nick]["skills"]
            combined_skill_prefs = {**old_skills_prefs, **new_skills_prefs}
            combined_changes = {k: v for dic in new_preferences.values() for k, v in dic.items()}
            if new_skills_prefs:
                combined_changes["skill_settings"] = json.dumps(list(combined_skill_prefs.values()))
                new_preferences["skills"] = combined_skill_prefs
                LOG.debug(f"combined_skill_prefs={combined_skill_prefs}")
            combined_changes["username"] = nick
            self.socket_emit_to_server("update profile", ["skill", combined_changes,
                                                          message.context["klat_data"]["request_id"]])
            self.bus.emit(Message("neon.remove_cache_entry", {"nick": nick}))
            old_preferences = message.context["nick_profiles"][nick]
            message.context["nick_profiles"][nick] = {**old_preferences, **new_preferences}
        else:
            for section, settings in new_preferences.items():
                # section in user, brands, units, etc.
                for key, val in settings.items():
                    self.user_config[section][key] = val
            self.user_config.write_changes()

    def update_skill_settings(self, new_preferences: dict,
                              message: Message = None, skill_global=False):
        """
        Updates skill settings with the passed new_preferences
        :param new_preferences: dict of updated preference values. {key: val}
        :param message: Message associated with request
        :param skill_global: Boolean to indicate these are global/non-user-specific variables
        """
        LOG.debug(f"Update skill settings with new: {new_preferences}")
        if self.server and not skill_global:
            new_preferences["skill_id"] = self.skill_id
            self.update_profile({"skills": {self.skill_id: new_preferences}},
                                message)
        else:
            for key, val in new_preferences.items():
                self.settings[key] = val
            if isinstance(self.settings, JsonStorage):
                self.settings.store()
            else:
                save_settings(self.file_system.path, self.settings)

    def build_message(self, kind, utt, message, speaker=None):
        """
        Build a message for user input or neon response
        :param kind: "neon speak" or "execute"
        :param utt: string to emit
        :param message: incoming message object
        :param speaker: speaker data dictionary
        :return: Message object
        """
        LOG.debug(speaker)

        default_speech = self.preference_speech(message)
        # Override user preference for all script responses
        if not speaker:
            speaker = {"name": "Neon",
                       "language": default_speech["tts_language"],
                       "gender": default_speech["tts_gender"],
                       "voice": default_speech["neon_voice"],
                       "override_user": True}
        elif speaker and speaker.get("language"):
            speaker["override_user"] = True
        else:
            speaker = None

        LOG.debug(f"data={message.data}")
        # LOG.debug(f"context={message.context}")

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
                    "neon_should_respond": True,
                    "cc_data": {"request": utt,
                                "emit_response": emit_response,
                                "execute_from_script": True
                                }
                })
            elif kind == "neon speak":
                added_context = {"cc_data": message.context.get("cc_data", {})}
                added_context["cc_data"]["request"] = utt

                return message.reply("speak", {"lang": message.data.get("lang", "en-US"),
                                               "speaker": speaker
                                               }, added_context)
        except Exception as x:
            LOG.error(x)

    def mobile_skill_intent(self, action: str, arguments: dict, message: Message):
        """
        Handle a mobile skill intent response
        :param action: Name of action or event for mobile device to handle
        :param arguments: dict of key/value arguments to pass with action
        :param message: Message associated with request
        """
        fmt_args = ""
        for key, value in arguments:
            fmt_args += f"&{key}={value}"
        if self.server:
            emit_data = [action, fmt_args, message.context["klat_data"]["request_id"]]
            self.bus.emit(Message("css.emit", {"event": "mobile skill intent", "data": emit_data}))
        else:
            LOG.warning("Mobile intents are not supported on this device yet.")

    def socket_emit_to_server(self, event: str, data: list):
        LOG.debug(f"Emit event={event}, data={data}")
        self.bus.emit(Message("css.emit", {"event": event, "data": data}))

    def send_with_audio(self, text_shout, audio_file, message, lang="en-us", private=False, speaker=None):
        """
        Sends a Neon response with the passed text phrase and audio file
        :param text_shout: (str) Text to shout
        :param audio_file: (str) Full path to an arbitrary audio file to attach to shout; must be readable/accessible
        :param message: Message associated with request
        :param lang: (str) Language of wav_file
        :param private: (bool) Whether or not shout is private to the user
        :param speaker: (dict) Message sender data
        """
        # from shutil import copyfile
        if not speaker:
            speaker = {"name": "Neon", "language": None, "gender": None, "voice": None}

        # Play this back regardless of user prefs
        speaker["override_user"] = True

        # Either gender should be fine
        responses = {lang: {"sentence": text_shout,
                            "male": audio_file,
                            "female": audio_file}}
        message.context["private"] = private
        LOG.info(f"sending klat.response with responses={responses} | speaker={speaker}")
        self.bus.emit(message.forward("klat.response", {"responses": responses, "speaker": speaker}))

    def neon_must_respond(self, message):
        """
        Checks if Neon must respond to an utterance (i.e. a server request)
        @param message:
        @return:
        """
        if self.server:
            title = message.context.get("klat_data", {}).get("title", "")
            LOG.debug(message.data.get("utterance"))
            if message.data.get("utterance").startswith("Welcome to your private conversation"):
                return False
            if title.startswith("!PRIVATE:"):
                if ',' in title:
                    users = title.split(':')[1].split(',')
                    for idx, val in enumerate(users):
                        users[idx] = val.strip()
                    if len(users) == 2 and "Neon" in users:
                        # Private with Neon
                        # LOG.debug("DM: Private Conversation with Neon")
                        return True
                    elif message.data.get("utterance").lower().startsWith("neon"):
                        # Message starts with "neon", must respond
                        return True
                else:
                    # Solo Private
                    return True
        return False

    def voc_match(self, utt, voc_filename, lang=None, exact=False):
        # TODO: Handles bug to be addressed in: https://github.com/OpenVoiceOS/ovos_utils/issues/73
        try:
            return super().voc_match(utt, voc_filename, lang, exact)
        except FileNotFoundError:
            LOG.info(f"`{voc_filename}` not found, checking in neon_core")
            from mycroft.skills.skill_data import read_vocab_file
            from neon_utils.packaging_utils import get_core_root
            from itertools import chain
            import re
        lang = lang or self.lang
        voc = resolve_neon_resource_file(f"text/{lang}/{voc_filename}.voc")
        if not voc:
            raise FileNotFoundError(voc)
        vocab = read_vocab_file(voc)
        cache_key = lang + voc_filename
        self.voc_match_cache[cache_key] = list(chain(*vocab))
        if utt:
            if exact:
                # Check for exact match
                return any(i.strip() == utt
                           for i in self.voc_match_cache[cache_key])
            else:
                # Check for matches against complete words
                return any([re.match(r'.*\b' + i + r'\b.*', utt)
                            for i in self.voc_match_cache[cache_key]])
        else:
            return False

    def neon_in_request(self, message):
        """
        Checks if the utterance is intended for Neon. Server utilizes current conversation, otherwise wake-word status
        and message "Neon" parameter used
        """
        if not is_neon_core():
            return True

        from neon_utils.message_utils import request_for_neon
        ww_enabled = self.local_config.get("interface",
                                           {}).get("wake_word_enabled",
                                                   True)
        return request_for_neon(message, "neon", self.voc_match, ww_enabled)

    def show_settings_gui(self):
        """
        Function to update and
        :return:
        """
        try:
            # TODO: Conditionalize register, only needs to happen once but only after skill init DM
            self.gui.register_settings()
            self.gui.show_settings()
        except Exception as e:
            LOG.error(e)

    def check_yes_no_response(self, message):
        """
        Used in converse methods to check if a response confirms or declines an action. Differs from ask_yesno in that
        this does not assume input will be spoken with wake words enabled
        :param message: incoming message object to evaluate
        :return: False if declined, numbers if confirmed numerically, True if confirmed with no numbers
        """
        utterance = message.data.get("utterances")[0]
        if self.voc_match(utterance, "no"):
            LOG.info("User Declined")
            return False
        elif self.voc_match(utterance, "yes"):
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

    def report_metric(self, name, data):
        """Report a skill metric to the Mycroft servers.

        Arguments:
            name (str): Name of metric. Must use only letters and hyphens
            data (dict): JSON dictionary to report. Must be valid JSON
        """
        combinded = deepcopy(data)
        combinded["name"] = name
        self.bus.emit(Message("neon.metric", combinded))

    def send_email(self, title, body, message=None, email_addr=None, attachments=None):
        """
        Send an email to the registered user's email. Method here for backwards compatibility with Mycroft skills.
        Email address priority: email_addr, user prefs from message, fallback to DeviceApi for Mycroft method

        Arguments:
            title (str): Title of email
            body  (str): HTML body of email. This supports
                         simple HTML like bold and italics
            email_addr (str): Optional email address to send message to
            attachments (dict): Optional dict of file names to Base64 encoded files
            message (Message): Optional message to get email from
        """
        message = message or dig_for_message()
        if not email_addr and message:
            email_addr = self.preference_user(message).get("email")

        if email_addr:
            LOG.info("Send email via Neon Server")
            request_data = {"recipient": email_addr,
                            "subject": title,
                            "body": body,
                            "attachments": attachments}
            data = send_mq_request("/neon_emails", request_data, "neon_emails_input")
            return data.get("success")
        else:
            LOG.warning("Attempting to send email via Mycroft Backend")
            super().send_email(title, body)

    def make_active(self, duration_minutes=5):
        """Bump skill to active_skill list in intent_service.

        This enables converse method to be called even without skill being
        used in last 5 minutes.
        :param duration_minutes: duration in minutes for skill to remain active (-1 for infinite)
        """
        self.bus.emit(Message("active_skill_request",
                              {"skill_id": self.skill_id,
                               "timeout": duration_minutes}))

    def register_decorated(self):
        """
        Accessor method
        """
        self._register_decorated()

    def schedule_event(self, handler, when, data=None, name=None, context=None):
        # TODO: should 'when' already be a datetime? DM
        if isinstance(when, int) or isinstance(when, float):
            from datetime import datetime as dt, timedelta
            when = to_system_time(dt.now(self.sys_tz)) + timedelta(seconds=when)
            LOG.info(f"Made a datetime: {when}")
        super().schedule_event(handler, when, data, name, context)

    def request_check_timeout(self, time_wait, intent_to_check):
        LOG.info("request received")
        LOG.info(time_wait)
        LOG.info(len(intent_to_check))
        try:
            if isinstance(intent_to_check, str):
                intent_to_check = [intent_to_check]

            for intent in intent_to_check:
                data = {'time_out': time_wait,
                        'intent_to_check': f"{self.skill_id}:{intent}"}
                LOG.debug(f"DM: Set Timeout: {data}")
                self.bus.emit(Message("set_timeout", data))
        except Exception as x:
            LOG.error(x)

    def await_confirmation(self, user, actions, timeout=None):
        """
        Used to add an action for which to await a response (note: this will disable skill reload when called and enable
        on timeout)
        :param user: username ("local" for non-server)
        :param actions: string action name (or list of action names) we are confirming,
                       handled in skill's converse method
        :param timeout: duration to wait in seconds before removing the action from the list
        """
        from datetime import datetime as dt, timedelta
        self.reload_skill = False
        if isinstance(actions, str):
            actions = [actions]
        self.actions_to_confirm[user] = actions
        if not timeout:
            timeout = self.default_intent_timeout
        expiration = dt.now(self.sys_tz) + timedelta(seconds=timeout)

        self.cancel_scheduled_event(user)
        time.sleep(1)
        self.schedule_event(self._confirmation_timeout, to_system_time(expiration), data={"user": user,
                                                                                          "action": actions},
                            name=user)
        LOG.debug(f"Scheduled {user}")

    def _confirmation_timeout(self, message):
        user = message.data.get("user", "local")
        try:
            if user in self.actions_to_confirm.keys():
                removed = self.actions_to_confirm.pop(user)
                LOG.info(f"confirmation timed out ({time.time()}): {removed}")
        except Exception as e:
            # Catches if the item was already popped
            LOG.error(e)
        if len(self.actions_to_confirm.keys()) == 0:
            self.reload_skill = True

    def clear_gui_timeout(self, timeout_seconds=60):
        """
        Called by a skill to clear its gui display after the specified timeout
        :param timeout_seconds: seconds to wait before clearing gui display
        """
        from datetime import datetime as dt, timedelta
        expiration = dt.now(self.sys_tz) + timedelta(seconds=timeout_seconds)
        self.schedule_event(self._clear_gui_timeout, to_system_time(expiration))

    def _clear_gui_timeout(self):
        """
        Handler for clear_gui_timeout function
        """
        LOG.info("Reset GUI!")
        self.gui.clear()

    def clear_signals(self, prefix: str):
        """
        Clears all signals that begin with the passed prefix. Used with skill prefix for a skill to clear any signals it
        may have set
        :param prefix: prefix to match
        """
        LOG.warning(f"Signal use is being depreciated. Transition to internal variables.")
        os.makedirs(f"{self.local_config['dirVars']['ipcDir']}/signal", exist_ok=True)
        for signal in os.listdir(self.local_config['dirVars']['ipcDir'] + '/signal'):
            if str(signal).startswith(prefix) or f"_{prefix}_" in str(signal):
                # LOG.info('Removing ' + str(signal))
                # os.remove(self.configuration_available['dirVars']['ipcDir'] + '/signal/' + signal)
                self.check_for_signal(signal)

    def update_cached_data(self, filename, new_element):
        """
        Updates cache file of skill responses to translated responses when non-english responses are requested.
        :param filename: (str) filename of cache object to update (relative to cacheDir)
        :param new_element: (any) object to cache at passed location
        """
        with open(os.path.join(self.cache_loc, filename), 'wb+') as file_to_update:
            pickle.dump(new_element, file_to_update, protocol=pickle.HIGHEST_PROTOCOL)

    def get_cached_data(self, filename, file_loc=None):
        """
        Retrieves cache data from a file created/updated with update_cached_data
        :param filename: (str) filename of cache object to update
        :param file_loc: (str) path to directory containing filename (defaults to cache dir)
        :return: (dict) cache data
        """
        if not file_loc:
            file_loc = self.cache_loc
        cached_location = os.path.join(file_loc, filename)
        if pathlib.Path(cached_location).exists():
            with open(cached_location, 'rb') as file:
                return pickle.load(file)
        else:
            return {}

    def get_utterance_user(self, message: Optional[Message]) -> str:
        """
        Gets the user associated with the given message. Returns default 'local' or 'server' if no user specified.
        Args:
            message: Message associated with request

        Returns:
            Username associated with the message or a default value of 'local' or 'server'.
        """
        if self.server:
            default_user = "server"
        else:
            default_user = self.preference_user(message).get("username", "local")
        if not message:
            return default_user

        try:
            return get_message_user(message) or default_user
        except Exception as e:
            LOG.error(e)
            # TODO: Depreciate this and fix underlying error DM
            return default_user

    @staticmethod
    def newest_file_in_dir(path, ext=None):
        LOG.warning("This method is depreciated, use file_utils.get_most_recent_file_in_dir() directly")
        return get_most_recent_file_in_dir(path, ext)

    @staticmethod
    def request_from_mobile(message):
        LOG.warning("This method is depreciated, use message_utils.request_from_mobile() directly")
        return request_from_mobile(message)

    @staticmethod
    def to_system_time(dt):
        LOG.warning("This method is depreciated, use location_utils.to_system_time() directly")
        return to_system_time(dt)

    def decorate_api_call_use_lru(self, func):
        """
        Decorate the API-call function to use LRUcache.
        NOTE: the wrapper adds an additional argument, so decorated functions MUST be called with it!

        from wikipedia_for_humans import summary
        summary = decorate_api_call_use_lru(summary)
        result = summary(lru_query='neon', query='neon', lang='en')

        Args:
            func: the function to be decorated
        Returns: decorated function
        """
        @wraps(func)
        def wrapper(lru_query: str, *args, **kwargs):
            # TODO might use an abstract method for cached API call to define a signature
            result = self.lru_cache.get(lru_query)
            if not result:
                result = func(*args, **kwargs)
                self.lru_cache.put(key=lru_query, value=result)
            return result
        return wrapper

    def _write_cache_on_disk(self):
        """
        Write the cache on disk, reset the cache and reschedule the event.
        This handler is enabled by scheduling an event in NeonSkill.initialize().
        Returns:
        """
        filename = f"lru_{self.skill_id}"
        data_load = self.lru_cache.jsonify()
        self.update_cached_data(filename=filename, new_element=data_load)
        self.lru_cache.clear()
        self.schedule_event(self._write_cache_on_disk, CACHE_TIME_OFFSET, name="neon.load_cache_on_disk")
        return
