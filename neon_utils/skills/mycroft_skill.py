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

import sys
import json
import time
import os.path

from copy import deepcopy
from threading import Event
from typing import Optional

from ruamel.yaml import YAML
from mycroft_bus_client.message import Message

from neon_utils.skill_override_functions import wait_while_speaking
from neon_utils.signal_utils import wait_for_signal_clear
from neon_utils.skills.skill_gui import SkillGUI
from neon_utils.logger import LOG
from neon_utils.message_utils import get_message_user, dig_for_message
from neon_utils.configuration_utils import dict_update_keys, parse_skill_default_settings, \
    is_neon_core, get_neon_local_config, get_mycroft_compatible_config

from mycroft.skills import MycroftSkill
from mycroft.skills.settings import get_local_settings
from mycroft.filesystem import FileSystemAccess


class PatchedMycroftSkill(MycroftSkill):
    def __init__(self, name=None, bus=None, use_settings=True):
        self.name = name or self.__class__.__name__
        skill_id = os.path.basename(os.path.dirname(os.path.abspath(sys.modules[self.__module__].__file__)))

        # TODO: Use XDG spec to read config path from config DM

        self.file_system = FileSystemAccess(os.path.join('skills', skill_id))
        if is_neon_core():
            neon_conf_path = os.path.join(os.path.expanduser(get_neon_local_config()["dirVars"].get("confDir")
                                                             or "~/.config/neon"), "skills", skill_id)
            if neon_conf_path != self.file_system.path:
                LOG.info("Patching skill file system path")
                if os.listdir(self.file_system.path):
                    LOG.warning(f"Files found in unused path: {self.file_system.path}")
                else:
                    os.rmdir(self.file_system.path)
                self.file_system.path = neon_conf_path
                if not os.path.isdir(self.file_system.path):
                    os.makedirs(self.file_system.path)
        fs_path = deepcopy(self.file_system.path)
        super(PatchedMycroftSkill, self).__init__(name, bus, use_settings)
        if self.file_system.path != fs_path:
            if os.listdir(self.file_system.path):
                LOG.warning(f"Files found in unused path: {self.file_system.path}")
            else:
                LOG.debug(f"Removing Mycroft-created file_system")
                os.rmdir(self.file_system.path)
            self.file_system.path = fs_path
        self.config_core = get_mycroft_compatible_config()
        self.gui = SkillGUI(self)

    def _init_settings(self):
        self.settings_write_path = self.file_system.path
        skill_settings = get_local_settings(self.settings_write_path, self.name)
        settings_from_disk = dict(skill_settings)
        self.settings = dict_update_keys(skill_settings, self._read_default_settings())
        if self.settings != settings_from_disk:
            with open(os.path.join(self.settings_write_path, 'settings.json'), "w+") as f:
                json.dump(self.settings, f, indent=4)
        self._initial_settings = dict(self.settings)

    def _read_default_settings(self):
        yaml_path = os.path.join(self.root_dir, "settingsmeta.yml")
        json_path = os.path.join(self.root_dir, "settingsmeta.json")
        if os.path.isfile(yaml_path):
            with open(yaml_path) as f:
                self.settings_meta = YAML().load(f) or dict()
        elif os.path.isfile(json_path):
            with open(json_path) as f:
                self.settings_meta = json.load(f)
        else:
            return dict()
        return parse_skill_default_settings(self.settings_meta)

    def speak(self, utterance, expect_response=False, wait=False, meta=None, message=None, private=False, speaker=None):
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
        # registers the skill as being active
        meta = meta or {}
        meta['skill'] = self.name
        self.enclosure.register(self.name)
        if utterance:
            if not message:
                # Find the associated message
                LOG.debug('message is None.')
                message = dig_for_message()
                if not message:
                    message = Message("speak")
            if not speaker:
                speaker = message.data.get("speaker", None)

            nick = get_message_user(message)

            if private and message.context.get("klat_data"):
                LOG.debug("Private Message")
                title = message.context["klat_data"]["title"]
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
                    "expect_response": expect_response,
                    "meta": meta,
                    "speaker": speaker}

            if message.context.get("cc_data", {}).get("emit_response"):
                msg_to_emit = message.reply("skills:execute.response", data)
            else:
                message.context.get("timing", {})["speech_start"] = time.time()
                msg_to_emit = message.reply("speak", data, message.context)
                LOG.debug(f"Skill speak! {data}")

            LOG.debug(msg_to_emit.msg_type)
            self.bus.emit(msg_to_emit)
        else:
            LOG.warning("Null utterance passed to speak")
            LOG.warning(f"{self.name} | message={message}")

        if wait:
            wait_for_signal_clear('isSpeaking')

    def speak_dialog(self, key, data=None, expect_response=False, wait=False,
                     message=None, private=False, speaker=None):
        """ Speak a random sentence from a dialog file.

        Arguments:
            :param key: dialog file key (e.g. "hello" to speak from the file "locale/en-us/hello.dialog")
            :param data: information used to populate key
            :param expect_response: set to True if Mycroft should listen for a response immediately after speaking.
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
                   speaker=speaker, wait=wait, meta={'dialog': key, 'data': data})

    def get_response(self, dialog: str = '', data: Optional[dict] = None, validator=None,
                     on_fail=None, num_retries: int = -1, message: Optional[Message] = None) -> Optional[str]:
        """
        Gets a response from a user. Speaks the passed dialog file or string and then optionally plays a listening
        confirmation sound and starts listening if in wake words mode.
        Wraps the default Mycroft method to add support for multiple users and running without a wake word.

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
        message = message or dig_for_message()
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

        # If skill has dialog, render the input in case it is referencing a dialog file
        if self.dialog_renderer:
            dialog = self.dialog_renderer.render(dialog, data)

        if dialog:
            self.speak(dialog, expect_response=True, wait=False, message=message)
        else:
            self.bus.emit(message.forward('mycroft.mic.listen'))
        return self._wait_response(is_cancel, validator, on_fail_fn,
                                   num_retries, message, user)

    def _wait_response(self, is_cancel, validator, on_fail, num_retries, message=None, user: str = None):
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

            if response is None:
                # if nothing said, prompt one more time
                num_none_fails = 1 if num_retries < 0 else num_retries
                if num_fails >= num_none_fails:
                    return None
            else:
                if validator(response):
                    return response

                # catch user saying 'cancel'
                if is_cancel(response):
                    return None

            num_fails += 1
            if 0 < num_retries < num_fails:
                return None

            line = on_fail(response)
            if line:
                self.speak(line, expect_response=True)
            else:
                msg = message.reply('mycroft.mic.listen') or Message('mycroft.mic.listen',
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
                return True
            return False

        # install a temporary conversation handler
        self.make_active()
        converse.response = None
        default_converse = self.converse
        self.converse = converse
        wait_for_signal_clear("isSpeaking")
        event.wait(15)  # 10 for listener, 5 for STT, then timeout
        self.converse = default_converse
        return converse.response
