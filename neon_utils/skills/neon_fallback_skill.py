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

import yaml
import json
import os
import pathlib
import pickle
import time
from copy import deepcopy
from functools import wraps
from threading import Event
from typing import List, Any, Optional

from dateutil.tz import gettz
from json_database import JsonStorage
from ovos_bus_client import Message
from ovos_plugin_manager.language import OVOSLangDetectionFactory, OVOSLangTranslationFactory
from ovos_utils.gui import is_gui_connected
from ovos_utils.log import LOG, log_deprecation, deprecated
from ovos_utils.skills import get_non_properties
from ovos_utils.xdg_utils import xdg_cache_home
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.skills.fallback import FallbackSkillV1

from neon_utils.cache_utils import LRUCache
from neon_utils.file_utils import resolve_neon_resource_file
from neon_utils.location_utils import to_system_time
from neon_utils.message_utils import dig_for_message, resolve_message, get_message_user
from neon_utils.skills.neon_skill import CACHE_TIME_OFFSET, DEFAULT_SPEED_MODE, SPEED_MODE_EXTENSION_TIME, NeonSkill, \
    save_settings
from neon_utils.user_utils import get_user_prefs


class NeonFallbackSkill(FallbackSkillV1):
    """
    Class that extends the NeonSkill and FallbackSkill classes to provide
    NeonSkill functionality to any Fallback skill subclassing this class.
    """
    def __init__(self, *args, **kwargs):
        log_deprecation("This class is deprecated. Implement "
                        "`ovos_workshop.skills.fallback.FallbackSkill`",
                        "2.0.0")

        FallbackSkillV1.__init__(self, *args, **kwargs)
        LOG.debug(f"instance_handlers={self.instance_fallback_handlers}")
        LOG.debug(f"class_handlers={FallbackSkillV1.fallback_handlers}")

        # Manual init of NeonSkill
        self.cache_loc = os.path.join(xdg_cache_home(), "neon")
        os.makedirs(self.cache_loc, exist_ok=True)
        self.lru_cache = LRUCache()
        self._gui_connected = False

        try:
            import neon_core
            self._neon_core = True
        except ImportError:
            self._neon_core = False

        self._actions_to_confirm = dict()

        self._lang_detector = None
        self._translator = None

        # TODO: Should below defaults be global config?
        # allow skills to specify timeout overrides per-skill
        self._speak_timeout = 30
        self._get_response_timeout = 15  # 10 for listener, 5 for STT, then timeout

    def initialize(self):
        # schedule an event to load the cache on disk every CACHE_TIME_OFFSET seconds
        self.schedule_event(self._write_cache_on_disk, CACHE_TIME_OFFSET,
                            name="neon.load_cache_on_disk")

    @property
    # @deprecated("Call `dateutil.tz.gettz` directly", "2.0.0")
    def sys_tz(self):
        # TODO: Is this deprecated?
        return gettz()

    @property
    @deprecated("Nothing should depend on `neon_core` vs other cores", "2.0.0")
    def neon_core(self):
        return self._neon_core

    @property
    @deprecated("Skills should track this internally or use converse",
                "2.0.0")
    def actions_to_confirm(self) -> dict:
        return self._actions_to_confirm

    @actions_to_confirm.setter
    @deprecated("Skills should track this internally or use converse",
                "2.0.0")
    def actions_to_confirm(self, val: dict):
        self._actions_to_confirm = val

    @property
    def lang_detector(self):
        if not self._lang_detector and OVOSLangDetectionFactory:
            try:
                self._lang_detector = \
                    OVOSLangDetectionFactory.create(self.config_core)
            except ValueError as x:
                LOG.error(f"Configured lang plugins not available: {x}")
        return self._lang_detector

    @property
    def translator(self):
        if not self._translator and OVOSLangTranslationFactory:
            try:
                self._translator = \
                    OVOSLangTranslationFactory.create(self.config_core)
            except ValueError as x:
                LOG.error(f"Configured lang plugins not available: {x}")
        return self._translator

    @property
    @deprecated("This is now configured in CommonQuery", "2.0.0")
    def skill_mode(self) -> str:
        """
        Determine the "speed mode" requested by the user
        """
        return get_user_prefs(dig_for_message()).get(
            'response_mode', {}).get('speed_mode') or DEFAULT_SPEED_MODE

    @property
    @deprecated("This is now configured in CommonQuery", "2.0.0")
    def extension_time(self) -> int:
        """
        Determine how long the skill should extend CommonSkill request timeouts
        """
        return SPEED_MODE_EXTENSION_TIME.get(self.skill_mode) or 10

    @property
    @deprecated("Always emit GUI events for the GUI module to manage", "2.0.0")
    def gui_enabled(self) -> bool:
        """
        If True, skill should display GUI pages
        """
        try:
            self._gui_connected = self._gui_connected or \
                                  is_gui_connected(self.bus)
            return self._gui_connected
        except Exception as x:
            # In container environments, this check fails so assume True
            LOG.exception(x)
            return True

    @property
    @deprecated("reference `self.settings` directly", "2.0.0")
    def ngi_settings(self):
        return self.preference_skill()

    @deprecated("reference `self.settings` directly", "2.0.0")
    def preference_skill(self, message=None) -> dict:
        """
        Returns the skill settings configuration
        Equivalent to self.settings if settings not in message context
        :param message: Message associated with request
        :return: dict of skill preferences
        """
        message = message or dig_for_message()
        return get_user_prefs(
            message).get("skills", {}).get(self.skill_id) or self.settings

    @deprecated("implement `neon_utils.user_utils.update_user_profile`",
                "2.0.0")
    def update_profile(self, new_preferences: dict, message: Message = None):
        """
        Updates a user profile with the passed new_preferences
        :param new_preferences: dict of updated preference values.
            Should follow {section: {key: val}} format
        :param message: Message associated with request
        """
        from neon_utils.user_utils import update_user_profile
        message = message or dig_for_message()
        try:
            update_user_profile(new_preferences, message, self.bus)
        except Exception as x:
            LOG.error(x)

    @resolve_message
    def update_skill_settings(self, new_preferences: dict,
                              message: Message = None, skill_global=True):
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
        if not skill_global:
            new_preferences["skill_id"] = self.skill_id
            self.update_profile({"skills": {self.skill_id: new_settings}},
                                message)
        else:
            self.settings = new_settings
            if isinstance(self.settings, JsonStorage):
                self.settings.store()
            else:
                save_settings(self.file_system.path, self.settings)

    def send_with_audio(self, text_shout, audio_file, message, lang="en-us",
                        private=False, speaker=None):
        """
        Sends a Neon response with the passed text phrase and audio file
        :param text_shout: (str) Text to shout
        :param audio_file: (str) Full path to an arbitrary audio file to
            attach to shout; must be readable/accessible
        :param message: Message associated with request
        :param lang: (str) Language of wav_file
        :param private: (bool) Whether or not shout is private to the user
        :param speaker: (dict) Message sender data
        """
        # TODO: Update 'speak' to handle audio files
        # from shutil import copyfile
        if not speaker:
            speaker = {"name": "Neon", "language": None, "gender": None,
                       "voice": None}

        # Play this back regardless of user prefs
        speaker["override_user"] = True

        # Either gender should be fine
        responses = {lang: {"sentence": text_shout,
                            "male": audio_file,
                            "female": audio_file}}
        message.context["private"] = private
        LOG.info(f"sending klat.response with responses={responses} | "
                 f"speaker={speaker}")
        self.bus.emit(message.forward("klat.response",
                                      {"responses": responses,
                                       "speaker": speaker}))

    @deprecated("implement `neon_utils.user_utils.neon_must_respond`", "2.0.0")
    def neon_must_respond(self, message: Message = None) -> bool:
        """
        Checks if Neon must respond to an utterance (i.e. a server request)
        :param message: message associated with user request
        :returns: True if Neon must provide a response to this request
        """
        from neon_utils.message_utils import neon_must_respond
        return neon_must_respond(message)

    def voc_match(self, utt, voc_filename, lang=None, exact=False):
        # TODO: This should be addressed in vocab resolver classes
        try:
            super_return = super().voc_match(utt, voc_filename, lang, exact)
        except FileNotFoundError:
            super_return = None
        lang = lang or self.lang

        if super_return:
            return super_return
        elif super_return is False:
            if self.voc_match_cache.get(lang + voc_filename):
                return super_return

        LOG.warning(f"`{voc_filename}` not found, checking in neon_core")
        voc = resolve_neon_resource_file(f"text/{lang}/{voc_filename}.voc")
        if not voc:
            raise FileNotFoundError(voc)
        from ovos_utils.file_utils import read_vocab_file
        from itertools import chain
        import re
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

    @deprecated("WW status can be queried via messagebus", "2.0.0")
    def neon_in_request(self, message: Message) -> bool:
        """
        Checks if the utterance is intended for Neon.
        Server utilizes current conversation, otherwise wake-word status
        and message "Neon" parameter used
        """
        if not self._neon_core:
            return True

        from neon_utils.message_utils import request_for_neon
        ww_enabled = self.config_core.get("listener",
                                          {}).get("wake_word_enabled", True)
        # TODO: Listen for WW state changes on the bus
        return request_for_neon(message, "neon", self.voc_match, ww_enabled)

    def report_metric(self, name, data):
        """Report a skill metric to the Mycroft servers.

        Arguments:
            name (str): Name of metric. Must use only letters and hyphens
            data (dict): JSON dictionary to report. Must be valid JSON
        """
        combined = deepcopy(data)
        combined["name"] = name
        self.bus.emit(Message("neon.metric", combined))

    def send_email(self, title, body, message=None, email_addr=None,
                   attachments=None):
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
        try:
            from neon_utils.mq_utils import send_mq_request
        except ImportError:
            LOG.warning("MQ Dependencies not installed")
            send_mq_request = None

        message = message or dig_for_message()
        if not email_addr and message:
            email_addr = get_user_prefs(message)["user"].get("email")

        if email_addr and send_mq_request:
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

    def schedule_event(self, handler, when, data=None, name=None, context=None):
        # TODO: should 'when' already be a datetime? DM
        if isinstance(when, int) or isinstance(when, float):
            from datetime import datetime as dt, timedelta
            when = to_system_time(dt.now(self.sys_tz)) + timedelta(seconds=when)
            LOG.debug(f"Made a datetime: {when}")
        super().schedule_event(handler, when, data, name, context)

    @deprecated("This method is deprecated", "2.0.0")
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

    def _register_chat_handler(self, name: str, method: callable):
        """
        Register a chat handler entrypoint. Decorated methods must
        return a string response that will be emitted as a response to the
        incoming Message.
        :param name: name of the chat handler
        :param method: method to handle incoming chat Messages
        """

        def wrapped_handler(message):
            response = method(message)
            self.bus.emit(message.response(data={'response': response},
                                           context={'skill_id': self.skill_id}))

        self.add_event(f'chat.{name}', wrapped_handler)
        msg = dig_for_message() or Message("",
                                           context={'skill_id': self.skill_id})
        self.bus.emit(msg.forward("register_chat_handler", {'name': name}))

    def _register_decorated(self):
        for attr_name in get_non_properties(self):
            method = getattr(self, attr_name)
            if hasattr(method, 'intents'):
                for intent in getattr(method, 'intents'):
                    self.register_intent(intent, method)

            if hasattr(method, 'intent_files'):
                for intent_file in getattr(method, 'intent_files'):
                    self.register_intent_file(intent_file, method)

            if hasattr(method, 'chat_handler'):
                self._register_chat_handler(getattr(method, 'chat_handler'),
                                            method)

    @property
    def location(self):
        """
        Backwards-compatible location property. Returns core location config if
        user location isn't specified.
        """
        from neon_utils.configuration_utils import get_mycroft_compatible_location
        return get_mycroft_compatible_location(get_user_prefs()["location"])

    def _init_settings(self):
        """
        Extends the default method to handle settingsmeta defaults locally
        """
        from neon_utils.configuration_utils import dict_update_keys
        OVOSSkill._init_settings(self)
        settings_from_disk = dict(self.settings)
        dict_update_keys(self._settings, self._read_default_settings())
        if self._settings != settings_from_disk:
            LOG.info("Updated default settings from skill metadata")
            self._settings.store()
            self._initial_settings = dict(self._settings)
        LOG.info(f"Skill initialized with settings: {self.settings}")

    def _handle_converse_request(self, message: Message):
        # TODO: Remove patch after ovos-core 0.0.8
        if message.msg_type == "skill.converse.request" and \
                message.data.get('skill_id') != self.skill_id:
            # Legacy request not for Neon
            return
        if message.msg_type == "skill.converse.request":
            message.msg_type = "neon.converse.request"
        OVOSSkill._handle_converse_request(self, message)

    def _read_default_settings(self):
        from neon_utils.configuration_utils import parse_skill_default_settings
        yaml_path = os.path.join(self.root_dir, "settingsmeta.yml")
        json_path = os.path.join(self.root_dir, "settingsmeta.json")
        if os.path.isfile(yaml_path):
            with open(yaml_path) as f:
                self.settings_meta = yaml.safe_load(f) or dict()
        elif os.path.isfile(json_path):
            with open(json_path) as f:
                self.settings_meta = json.load(f)
        else:
            return dict()
        return parse_skill_default_settings(self.settings_meta)

    @resolve_message
    def speak(self, utterance, expect_response=False, wait=False, meta=None,
              message=None, private=False, speaker=None):
        """
        Speak an utterance.
        Arguments:
            utterance (str):        sentence mycroft should speak
            expect_response (bool): set to True if Mycroft should listen for a response immediately after
                                    speaking the utterance.
            wait (bool):            set to True to block while the text is being spoken.
            meta:                   Information of what built the sentence.
            message (Message):      message associated with the input that this speak is associated with
            private (bool):         flag to indicate this message contains data that is private to the requesting user
            speaker (dict):         dict containing language or voice data to override user preference values

        """
        from neon_utils.signal_utils import check_for_signal, wait_for_signal_clear
        # registers the skill as being active
        meta = meta or {}
        meta['skill'] = self.name
        self.enclosure.register(self.name)
        if utterance:
            if not message:
                LOG.debug('message is None.')
                message = Message("speak")
            if not speaker:
                speaker = message.data.get("speaker", None)

            nick = get_message_user(message)

            if private and message.context.get("klat_data"):
                LOG.debug("Private Message")
                title = message.context["klat_data"].get("title") or \
                    "!PRIVATE:Neon"
                need_at_sign = True
                if title.startswith("!PRIVATE"):
                    users = title.split(':')[1].split(',')
                    for idx, val in enumerate(users):
                        users[idx] = val.strip()
                    if len(users) == 2 and "Neon" in users:
                        need_at_sign = False
                    elif len(users) == 1:
                        need_at_sign = False
                    elif nick.startswith("guest"):
                        need_at_sign = False
                if need_at_sign:
                    LOG.debug("Send message to private cid!")
                    utterance = f"@{nick} {utterance}"

            data = {"utterance": utterance,
                    "lang": self.lang,
                    "expect_response": expect_response,
                    "meta": meta,
                    "speaker": speaker,
                    "speak_ident": str(time.time())}

            if message.context.get("cc_data", {}).get("emit_response"):
                msg_to_emit = message.reply("skills:execute.response", data,
                                            {"destination": ["skills"],
                                             "source": ["skills"]})
            else:
                message.context.get("timing", {})["speech_start"] = time.time()
                msg_to_emit = message.reply("speak", data,
                                            {"destination": ["skills"],
                                             "source": ["audio"]})
                LOG.debug(f"Skill speak! {data}")
            LOG.debug(msg_to_emit.msg_type)

            if wait and check_for_signal("neon_speak_api", -1):
                self.bus.wait_for_response(msg_to_emit,
                                           msg_to_emit.data['speak_ident'],
                                           self._speak_timeout)
            else:
                self.bus.emit(msg_to_emit)
                if wait and not message.context.get("klat_data"):
                    LOG.debug("Using legacy isSpeaking signal")
                    wait_for_signal_clear('isSpeaking')

        else:
            LOG.warning("Null utterance passed to speak")
            LOG.warning(f"{self.name} | message={message}")

    @resolve_message
    def speak_dialog(self, key, data=None, expect_response=False, wait=False,
                     message=None, private=False, speaker=None):
        """ Speak a random sentence from a dialog file.

        Arguments:
            :param key: dialog file key (e.g. "hello" to speak from the file
                "locale/en-us/hello.dialog")
            :param data: information used to populate key
            :param expect_response: set to True if Mycroft should listen for a
                response immediately after speaking.
            :param wait: set to True to block while the text is being spoken.
            :param message: associated message from request
            :param private: private flag (server use only)
            :param speaker: optional dict of speaker info to use
        """
        data = data or {}
        LOG.debug(f"data={data}")
        if self.dialog_renderer:  # TODO: Pass index (0) here to use non-random responses DM
            to_speak = self.dialog_renderer.render(key, data)
        else:
            to_speak = key
        self.speak(to_speak,
                   expect_response, message=message, private=private,
                   speaker=speaker, wait=wait, meta={'dialog': key,
                                                     'data': data})

    @resolve_message
    def get_response(self, dialog: str = '', data: Optional[dict] = None,
                     validator=None, on_fail=None, num_retries: int = -1,
                     message: Optional[Message] = None) -> Optional[str]:
        """
        Gets a response from a user. Speaks the passed dialog file or string
        and then optionally plays a listening confirmation sound and
        starts listening if in wake words mode.
        Wraps the default Mycroft method to add support for multiple users and
        running without a wake word.

        Arguments:
            dialog (str): Optional dialog to speak to the user
            data (dict): Data used to render the dialog
            validator (any): Function with following signature
                def validator(utterance):
                    return utterance != "red"
            on_fail (any): Dialog or function returning literal string
                           to speak on invalid input.  For example:
                def on_fail(utterance):
                    return "nobody likes the color red, pick another"
            num_retries (int): Times to ask user for input, -1 for infinite
                NOTE: User can not respond and timeout or say "cancel" to stop
            message (Message): Message associated with request

        Returns:
            str: User's reply or None if timed out or canceled
        """
        user = get_message_user(message) or "local" if message else "local"
        data = data or {}

        def on_fail_default(utterance):
            fail_data = data.copy()
            fail_data['utterance'] = utterance

            if on_fail:
                to_speak = on_fail
            else:
                to_speak = dialog
            if self.dialog_renderer:
                return self.dialog_renderer.render(to_speak, data)
            else:
                return to_speak

        def is_cancel(utterance):
            return self.voc_match(utterance, 'cancel')

        def validator_default(utterance):
            # accept anything except 'cancel'
            return not is_cancel(utterance)

        on_fail_fn = on_fail if callable(on_fail) else on_fail_default
        validator = validator or validator_default

        # Ensure we have a message to forward
        message = message or dig_for_message()
        if not message:
            LOG.warning(f"Could not locate message associated with request!")
            message = Message("get_response")

        # If skill has dialog, render the input
        if self.dialog_renderer:
            dialog = self.dialog_renderer.render(dialog, data)

        if dialog:
            self.speak(dialog, wait=True, message=message, private=True)
        self.bus.emit(message.forward('mycroft.mic.listen'))
        return self._wait_response(is_cancel, validator, on_fail_fn,
                                   num_retries, message, user)

    def _wait_response(self, is_cancel, validator, on_fail, num_retries,
                       message=None, user: str = None):
        """
        Loop until a valid response is received from the user or the retry
        limit is reached.

        Arguments:
            is_cancel (callable): function checking cancel criteria
            validator (callable): function checking for a valid response
            on_fail (callable): function handling retries
            message (Message): message associated with request
        """
        user = user or "local"
        num_fails = 0
        while True:
            response = self.__get_response(user)

            if response is None:  # No Response
                # if nothing said, only prompt one more time
                num_none_fails = 1 if num_retries < 0 else num_retries
                LOG.debug(f"num_none_fails={num_none_fails}|"
                          f"num_fails={num_fails}")
                if num_fails >= num_none_fails:
                    LOG.info("No user response")
                    return None
            else:  # Some response
                # catch user saying 'cancel'
                if is_cancel(response):
                    LOG.info("User cancelled")
                    return None
                validated = validator(response)
                # returns the validated value or the response
                # (backwards compat)
                if validated is not False and validated is not None:
                    LOG.debug(f"Returning validated response")
                    return response if validated is True else validated
                LOG.debug(f"User response not validated: {response}")
            # Unvalidated or no response
            num_fails += 1
            if 0 < num_retries < num_fails:
                LOG.info(f"Failed ({num_fails}) through all retries "
                         f"({num_retries})")
                return None

            # Validation failed, retry
            line = on_fail(response)
            if line:
                LOG.debug(f"Speaking failure dialog: {line}")
                self.speak(line, wait=True, message=message, private=True)

            LOG.debug("Listen for another response")
            msg = message.reply('mycroft.mic.listen') or \
                Message('mycroft.mic.listen',
                        context={"skill_id": self.skill_id})
            self.bus.emit(msg)

    def __get_response(self, user="local"):
        """
        Helper to get a response from the user

        Arguments:
            user (str): user associated with response
        Returns:
            str: user's response or None on a timeout
        """
        event = Event()

        def converse(message):
            resp_user = get_message_user(message) or "local"
            if resp_user == user:
                utterances = message.data.get("utterances")
                converse.response = utterances[0] if utterances else None
                event.set()
                LOG.info(f"Got response: {converse.response}")
                return True
            LOG.debug(f"Ignoring input from: {resp_user}")
            return False

        # install a temporary conversation handler
        self.make_active()
        converse.response = None
        default_converse = self.converse
        self.converse = converse

        if not event.wait(self._get_response_timeout):
            LOG.warning("Timed out waiting for user response")
        self.converse = default_converse
        return converse.response

    # renamed in base class for naming consistency
    # refactored to use new resource utils
    def translate(self, text: str, data: Optional[dict] = None):
        """
        Deprecated method for translating a dialog file.
        use self.resources.render_dialog(text, data) instead
        """
        log_deprecation("Use `resources.render_dialog`", "2.0.0")
        return self.resources.render_dialog(text, data)

    # renamed in base class for naming consistency
    # refactored to use new resource utils
    def translate_namedvalues(self, name: str, delim: str = ','):
        """
        Deprecated method for translating a name/value file.
        use self.resources.load_named_value_filetext, data) instead
        """
        log_deprecation("Use `resources.load_named_value_file`", "2.0.0")
        return self.resources.load_named_value_file(name, delim)

    # renamed in base class for naming consistency
    # refactored to use new resource utils
    def translate_list(self, list_name: str, data: Optional[dict] = None):
        """
        Deprecated method for translating a list.
        use delf.resources.load_list_file(text, data) instead
        """
        log_deprecation("Use `resources.load_list_file`", "2.0.0")
        return self.resources.load_list_file(list_name, data)

    # renamed in base class for naming consistency
    # refactored to use new resource utils
    def translate_template(self, template_name: str,
                           data: Optional[dict] = None):
        """
        Deprecated method for translating a template file
        use self.resources.template_file(text, data) instead
        """
        log_deprecation("Use `resources.template_file`", "2.0.0")
        return self.resources.load_template_file(template_name, data)

    def init_dialog(self, root_directory: Optional[str] = None):
        """
        DEPRECATED: use load_dialog_files instead
        """
        log_deprecation("Use `load_dialog_files`", "2.0.0")
        self.load_dialog_files(root_directory)
