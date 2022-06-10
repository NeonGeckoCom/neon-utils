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
import time
import os

from copy import deepcopy
from functools import wraps
from json_database import JsonStorage
from mycroft.skills.settings import save_settings
from mycroft_bus_client.message import Message
from typing import Optional, List, Any

from neon_utils.configuration_utils import get_neon_lang_config
from neon_utils.logger import LOG
from neon_utils.message_utils import get_message_user, dig_for_message, \
    resolve_message
from neon_utils.cache_utils import LRUCache
from neon_utils.mq_utils import send_mq_request
from neon_utils.skills.mycroft_skill import PatchedMycroftSkill as MycroftSkill
from neon_utils.user_utils import get_user_prefs

try:
    from ovos_plugin_manager.language import OVOSLangDetectionFactory,\
        OVOSLangTranslationFactory
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
        self.lru_cache = LRUCache()

        self.actions_to_confirm = dict()

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
        # schedule an event to load the cache on disk
        self.schedule_event(self._write_cache_on_disk, CACHE_TIME_OFFSET,
                            name="neon.load_cache_on_disk")

    @property
    def _cahce_loc(self):
        return os.path.join(self.file_system, "cache")

    @resolve_message
    def preference_skill(self, message=None) -> dict:
        """
        Returns the skill settings configuration
        Equivalent to self.settings for non-server
        :param message: Message associated with request
        :return: dict of skill preferences
        """
        nick = get_message_user(message) if message else None
        if nick and message.context.get("nick_profiles",
                                        {}).get("nick").get("skills"):
            try:
                skill = self.skill_id
                LOG.info(f"Get server prefs for skill={skill}")
                user_overrides = \
                    message.context["nick_profiles"][nick]["skills"].get(
                        self.skill_id, dict())
                LOG.debug(user_overrides)
                merged_settings = {**self.settings, **user_overrides}
                if user_overrides.keys() != merged_settings.keys():
                    LOG.info(f"New settings keys: user={nick}|"
                             f"skill={self.skill_id}|user={user_overrides}")
                    self.update_skill_settings(merged_settings, message)
                return merged_settings
            except Exception as x:
                LOG.error(x)
        return self.settings

    @resolve_message
    def update_profile(self, new_preferences: dict, message: Message = None):
        """
        Updates a user profile with the passed new_preferences
        :param new_preferences: dict of updated preference values.
            Should follow {section: {key: val}} format
        :param message: Message associated with request
        """
        from neon_utils.user_utils import update_user_profile

        try:
            update_user_profile(new_preferences, message, self.bus)
        except Exception as x:
            LOG.error(x)

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
        if message and message.context.get("klat_data") and not skill_global:
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
        :param audio_file: (str) Full path to an arbitrary audio file
            to attach to shout; must be readable/accessible
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

    @resolve_message
    def neon_must_respond(self, message: Message = None) -> bool:
        """
        Checks if Neon must respond to an utterance (i.e. a server request)
        :param message: message associated with user request
        :returns: True if Neon must provide a response to this request
        """
        if not message:
            return False
        if message.context.get("klat_data"):
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
            email_addr = get_user_prefs(message)["user"].get("email")

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

    def _confirmation_timeout(self, message):
        user = message.data.get("user", "local")
        try:
            if user in self.actions_to_confirm.keys():
                removed = self.actions_to_confirm.pop(user)
                LOG.info(f"confirmation timed out ({time.time()}): {removed}")
        except Exception as x:
            # Catches if the item was already popped
            LOG.error(x)
        if len(self.actions_to_confirm.keys()) == 0:
            self.reload_skill = True

    def update_cached_data(self, filename: str, new_element: Any):
        """
        Updates a generic cache file
        :param filename: file basename of cache object to update
        :param new_element: object to cache at passed location
        """
        # TODO: Move to static function with XDG compat.
        if not os.path.isdir(self._cache_loc):
            LOG.debug(f"Creating cache directory: {self._cache_loc}")
            os.makedirs(self._cache_loc, exist_ok=True)
        with open(os.path.join(self._cache_loc, filename),
                  'wb+') as file_to_update:
            pickle.dump(new_element, file_to_update,
                        protocol=pickle.HIGHEST_PROTOCOL)

    def get_cached_data(self, filename: str,
                        file_loc: Optional[str] = None) -> dict:
        """
        Retrieves cache data from a file created by update_cached_data
        :param filename: (str) filename of cache object to update
        :param file_loc: (str) path to directory containing filename
            (defaults to cache dir)
        :return: (dict) cache data
        """
        # TODO: Move to static function with XDG compat.
        if not os.path.isdir(self._cache_loc):
            LOG.debug(f"Creating cache directory: {self._cache_loc}")
            os.makedirs(self._cache_loc, exist_ok=True)
        if not file_loc:
            file_loc = self._cache_loc
        cached_location = os.path.join(file_loc, filename)
        if pathlib.Path(cached_location).exists():
            with open(cached_location, 'rb') as file:
                return pickle.load(file)
        else:
            return {}

    def decorate_api_call_use_lru(self, func):
        """
        Decorate the API-call function to use LRUcache.
        NOTE: the wrapper adds an additional argument, so
        decorated functions MUST be called with it!

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
        This handler is enabled by scheduling an event in NeonSkill.initialize
        Returns:
        """
        filename = f"lru_{self.skill_id}"
        data_load = self.lru_cache.jsonify()
        self.update_cached_data(filename=filename, new_element=data_load)
        self.lru_cache.clear()
        self.schedule_event(self._write_cache_on_disk, CACHE_TIME_OFFSET,
                            name="neon.load_cache_on_disk")
        return
