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
from neon_utils.user_utils import get_user_prefs

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
        self._user_config = None
        self._local_config = None
        # TODO: Move caches to skill.file_system
        self.cache_loc = os.path.expanduser(
            self.local_config.get('dirVars', {}).get('cacheDir') or
            "~/.local/share/neon/cache")
        if not os.path.isdir(self.cache_loc):
            LOG.debug(f"Creating cache directory: {self.cache_loc}")
            os.makedirs(self.cache_loc, exist_ok=True)
        self.lru_cache = LRUCache()

        self.sys_tz = gettz()

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
    def gui_enabled(self) -> bool:
        """
        If True, skill should display GUI pages
        """
        return self.local_config.get("prefFlags",
                                     {}).get("guiEvents", True) or \
            is_gui_running()

    @property
    def user_config(self):
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated, "
                    "use neon_utils.user_utils.get_user_prefs directly - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        if not self._user_config:
            self._user_config = get_neon_user_config()
        return self._user_config

    @property
    def local_config(self):
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated, use self.config_core - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        if not self._local_config:
            self._local_config = get_neon_local_config()
        return self._local_config

    @property
    def user_info_available(self):
        # TODO: Backwards-compat. deprecate in v1.0.0
        return self.user_config.content

    @property
    def configuration_available(self):
        # TODO: Backwards-compat. deprecate in v1.0.0
        return self.local_config.content

    @property
    def ngi_settings(self):
        return self.preference_skill()

    @staticmethod
    def create_signal(*args, **kwargs):
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated. "
                    "Import from neon_utils.signal_utils directly - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        create_signal(*args, **kwargs)

    @staticmethod
    def check_for_signal(*args, **kwargs):
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated. "
                    "Import from neon_utils.signal_utils directly - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        check_for_signal(*args, **kwargs)

    @staticmethod
    def preference_brands(message=None) -> dict:
        """
        Returns a brands dictionary for the user
        Equivalent to self.user_config["brands"] for non-server use
        """
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated."
                    "Use neon_utils.user_utils.get_user_prefs directly - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        return get_user_prefs(message)["brands"]

    @staticmethod
    def preference_user(message=None) -> dict:
        """
        Returns the user dictionary with name, email
        Equivalent to self.user_config["user"] for non-server use
        """
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated."
                    "Use neon_utils.user_utils.get_user_prefs directly - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        return get_user_prefs(message)["user"]

    @staticmethod
    def preference_location(message=None) -> dict:
        """
        Get the JSON data structure holding location information.
        Equivalent to self.user_config["location"] for non-server use
        """
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated."
                    "Use neon_utils.user_utils.get_user_prefs directly - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        return get_user_prefs(message)["location"]

    @staticmethod
    def preference_unit(message=None) -> dict:
        """
        Returns the units dictionary that contains
        time, date, measure formatting preferences
        Equivalent to self.user_config["units"] for non-server use
        """
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated."
                    "Use neon_utils.user_utils.get_user_prefs directly - "
                    f"{name}:{call.lineno}")
        # TODO: Backwards-compat. deprecate in v1.0.0
        return get_user_prefs(message)["units"]

    @staticmethod
    def preference_speech(message=None) -> dict:
        """
        Returns the speech dictionary that contains
        language and spoken response preferences
        Equivalent to self.user_config["speech"] for non-server use
        """
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning("This reference is deprecated."
                    "Use neon_utils.user_utils.get_user_prefs directly - "
                    f"{name}:{call.lineno}")
        return get_user_prefs(message)["speech"]

    @resolve_message
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
        LOG.warning("This method is being deprecated")
        # TODO: Backwards-compat. deprecate in v1.0.0
        merged_dict = {**self.preference_speech(message),
                       **self.preference_user(message),
                       **self.preference_brands(message),
                       **self.preference_location(message),
                       **self.preference_unit(message)}
        for key, value in merged_dict.items():
            if value == "":
                merged_dict[key] = -1
        return merged_dict

    def build_combined_skill_object(self, message=None) -> list:
        LOG.error(f"This method is depreciated!")
        # TODO: Backwards-compat. deprecate in v1.0.0
        user = self.get_utterance_user(message)
        skill_dict = message.context["nick_profiles"][user]["skills"]
        skill_list = list(skill_dict.values())
        return skill_list

    @resolve_message
    def update_profile(self, new_preferences: dict, message: Message = None):
        """
        Updates a user profile with the passed new_preferences
        :param new_preferences: dict of updated preference values.
            Should follow {section: {key: val}} format
        :param message: Message associated with request
        """
        from neon_utils.user_utils import update_user_profile

        def _write_yml_changes():
            for section, settings in new_preferences.items():
                # section in user, brands, units, etc.
                for key, val in settings.items():
                    self.user_config[section][key] = val
            self.user_config.write_changes()

        try:
            update_user_profile(new_preferences, message, self.bus)
        except Exception as x:
            LOG.error(x)
            LOG.warning("Updating global YML config")
            _write_yml_changes()

    @resolve_message
    def update_skill_settings(self, new_preferences: dict,
                              message: Message = None, skill_global=False):
        """
        Updates skill settings with the passed new_preferences
        :param new_preferences: dict of updated preference values. {key: val}
        :param message: Message associated with request
        :param skill_global: Boolean to indicate these are
            global/non-user-specific variables
        """
        # TODO: Spec how to handle global vs per-user settings
        LOG.debug(f"Update skill settings with new: {new_preferences}")
        new_settings = {**self.preference_skill(message), **new_preferences}
        if self.server and not skill_global:
            new_preferences["skill_id"] = self.skill_id
            self.update_profile({"skills": {self.skill_id: new_settings}},
                                message)
        else:
            self.settings = new_settings
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
        # TODO: Move this to message_utils DM
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
        LOG.warning(f"This method is depreciated!")
        # TODO: Backwards-compat. deprecate in v1.0.0
        fmt_args = ""
        for key, value in arguments:
            fmt_args += f"&{key}={value}"
        if self.server:
            emit_data = [action, fmt_args, message.context["klat_data"]["request_id"]]
            self.bus.emit(Message("css.emit", {"event": "mobile skill intent", "data": emit_data}))
        else:
            LOG.warning("Mobile intents are not supported on this device yet.")

    def socket_emit_to_server(self, event: str, data: list):
        LOG.warning(f"This method is depreciated!")
        # TODO: Backwards-compat. deprecate in v1.0.0
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
        # TODO: Update 'speak' to handle audio files
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

    @resolve_message
    def neon_must_respond(self, message: Message = None) -> bool:
        """
        Checks if Neon must respond to an utterance (i.e. a server request)
        :param message: message associated with user request
        :returns: True if Neon must provide a response to this request
        """
        if not message:
            return False
        if self.server:
            title = message.context.get("klat_data", {}).get("title", "")
            LOG.debug(message.data.get("utterance"))
            if message.data.get("utterance", "").startswith("Welcome to your private conversation"):
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
                    elif message.data.get("utterance", "").lower().startswith("neon"):
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
            LOG.warning(f"`{voc_filename}` not found, checking in neon_core")
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

    def neon_in_request(self, message: Message) -> bool:
        """
        Checks if the utterance is intended for Neon.
        Server utilizes current conversation, otherwise wake-word status
        and message "Neon" parameter used
        """
        if not is_neon_core():
            return True

        from neon_utils.message_utils import request_for_neon
        ww_enabled = self.local_config.get("interface",
                                           {}).get("wake_word_enabled",
                                                   True)
        return request_for_neon(message, "neon", self.voc_match, ww_enabled)

    def check_yes_no_response(self, message):
        """
        Used in converse methods to check if a response confirms or declines an action. Differs from ask_yesno in that
        this does not assume input will be spoken with wake words enabled
        :param message: incoming message object to evaluate
        :return: False if declined, numbers if confirmed numerically, True if confirmed with no numbers
        """
        LOG.warning(f"This method is depreciated. Use self.ask_yesno")
        # TODO: Backwards-compat. deprecate in v1.0.0

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
        combined = deepcopy(data)
        combined["name"] = name
        self.bus.emit(Message("neon.metric", combined))

    def send_email(self, title, body, message=None, email_addr=None, attachments=None):
        """
        Send an email to the registered user's email.
        Method here for backwards compatibility with Mycroft skills.
        Email address priority: email_addr, user prefs from message,
         fallback to DeviceApi for Mycroft method

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
            data = send_mq_request("/neon_emails", request_data,
                                   "neon_emails_input")
            return data.get("success")
        else:
            LOG.warning("Attempting to send email via Mycroft Backend")
            super().send_email(title, body)

    def make_active(self, duration_minutes=5):
        """Bump skill to active_skill list in intent_service.

        This enables converse method to be called even without skill being
        used in last 5 minutes.
        :param duration_minutes: duration in minutes for skill to remain active
         (-1 for infinite)
        """
        self.bus.emit(Message("active_skill_request",
                              {"skill_id": self.skill_id,
                               "timeout": duration_minutes}))

    def register_decorated(self):
        """
        Accessor method
        """
        LOG.warning(f"This method is depreciated!")
        # TODO: Backwards-compat. deprecate in v1.0.0
        self._register_decorated()

    def schedule_event(self, handler, when, data=None, name=None, context=None):
        # TODO: should 'when' already be a datetime? DM
        if isinstance(when, int) or isinstance(when, float):
            from datetime import datetime as dt, timedelta
            when = to_system_time(dt.now(self.sys_tz)) + timedelta(seconds=when)
            LOG.info(f"Made a datetime: {when}")
        super().schedule_event(handler, when, data, name, context)

    def request_check_timeout(self, time_wait: int,
                              intent_to_check: List[str]):
        """
        Set the specified intent to be disabled after the specified time
        :param time_wait: Time in seconds to wait before deactivating intent
        :param intent_to_check: list of intents to disable
        """
        # TODO: Consider unit tests or deprecation of this method DM
        LOG.debug(time_wait)
        LOG.debug(intent_to_check)
        if isinstance(intent_to_check, str):
            LOG.warning(f"Casting string to list: {intent_to_check}")
            intent_to_check = [intent_to_check]

        for intent in intent_to_check:
            data = {'time_out': time_wait,
                    'intent_to_check': f"{self.skill_id}:{intent}"}
            LOG.debug(f"Set Timeout: {data}")
            self.bus.emit(Message("set_timeout", data))

    def await_confirmation(self, user, actions, timeout=None):
        """
        Used to add an action for which to await a response (note: this will disable skill reload when called and enable
        on timeout)
        :param user: username ("local" for non-server)
        :param actions: string action name (or list of action names) we are confirming,
                       handled in skill's converse method
        :param timeout: duration to wait in seconds before removing the action from the list
        """
        LOG.warning(f"This method is depreciated! use self.get_response")
        # TODO: Backwards-compat. deprecate in v1.0.0
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
        self.schedule_event(self._confirmation_timeout,
                            to_system_time(expiration),
                            data={"user": user,
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
        LOG.warning(f"This method is depreciated!")
        # TODO: Backwards-compat. deprecate in v1.0.0
        from datetime import datetime as dt, timedelta
        expiration = dt.now(self.sys_tz) + timedelta(seconds=timeout_seconds)
        self.schedule_event(self._clear_gui_timeout,
                            to_system_time(expiration))

    def _clear_gui_timeout(self):
        """
        Handler for clear_gui_timeout function
        """
        # TODO: Backwards-compat. deprecate in v1.0.0
        LOG.info("Reset GUI!")
        self.gui.clear()

    def clear_signals(self, prefix: str):
        """
        Clears all signals that begin with the passed prefix.
        Used with skill prefix for a skill to clear any signals it
        may have set
        :param prefix: prefix to match
        """
        LOG.warning(f"Signal use is being depreciated. Transition to internal variables.")
        # TODO: Backwards-compat. deprecate in v1.0.0
        os.makedirs(f"{self.local_config['dirVars']['ipcDir']}/signal", exist_ok=True)
        for signal in os.listdir(self.local_config['dirVars']['ipcDir'] + '/signal'):
            if str(signal).startswith(prefix) or f"_{prefix}_" in str(signal):
                # LOG.info('Removing ' + str(signal))
                # os.remove(self.configuration_available['dirVars']['ipcDir'] + '/signal/' + signal)
                self.check_for_signal(signal)

    def update_cached_data(self, filename: str, new_element: Any):
        """
        Updates a generic cache file
        :param filename: filename of cache object to update (relative to cacheDir)
        :param new_element: object to cache at passed location
        """
        # TODO: Move to static function with XDG compat.
        with open(os.path.join(self.cache_loc, filename), 'wb+') as file_to_update:
            pickle.dump(new_element, file_to_update, protocol=pickle.HIGHEST_PROTOCOL)

    def get_cached_data(self, filename: str,
                        file_loc: Optional[str] = None) -> dict:
        """
        Retrieves cache data from a file created/updated with update_cached_data
        :param filename: (str) filename of cache object to update
        :param file_loc: (str) path to directory containing filename (defaults to cache dir)
        :return: (dict) cache data
        """
        # TODO: Move to static function with XDG compat.
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
        # TODO: Backwards-compat. deprecate in v1.0.0
        import inspect
        call = inspect.stack()[1]
        module = inspect.getmodule(call.frame)
        name = module.__name__ if module else call.filename
        LOG.warning(f"This method is deprecated, use get_message_user - "
                    f"{name}:{call.lineno}")
        from neon_utils.user_utils import get_default_user_config
        return get_message_user(message) or \
            get_default_user_config()["user"]["username"]

    @staticmethod
    def newest_file_in_dir(path, ext=None):
        # TODO: Backwards-compat. deprecate in v1.0.0
        LOG.warning("This method is depreciated, "
                    "use file_utils.get_most_recent_file_in_dir() directly")
        return get_most_recent_file_in_dir(path, ext)

    @staticmethod
    def request_from_mobile(message):
        # TODO: Backwards-compat. deprecate in v1.0.0
        LOG.warning("This method is depreciated, "
                    "use message_utils.request_from_mobile() directly")
        return request_from_mobile(message)

    @staticmethod
    def to_system_time(dt):
        # TODO: Backwards-compat. deprecate in v1.0.0
        LOG.warning("This method is depreciated, "
                    "use location_utils.to_system_time() directly")
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
