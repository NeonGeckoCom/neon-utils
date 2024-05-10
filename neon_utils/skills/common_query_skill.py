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
#
# Copyright 2018 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import abstractmethod
from os.path import dirname

from ovos_workshop.decorators.layers import IntentLayers
from ovos_workshop.skills.common_query_skill import CQSMatchLevel, CQSVisualMatchLevel
from ovos_workshop.skills.common_query_skill import CommonQuerySkill as _CQS
from ovos_workshop.decorators.compat import backwards_compat
from ovos_utils.file_utils import resolve_resource_file
from ovos_utils.log import log_deprecation, LOG
from neon_utils.skills.neon_skill import NeonSkill


def is_CQSVisualMatchLevel(match_level):
    log_deprecation("This method is deprecated", "2.0.0")
    return isinstance(match_level, type(CQSVisualMatchLevel.EXACT))


VISUAL_DEVICES = ['mycroft_mark_2']


def handles_visuals(platform):
    log_deprecation("This method is deprecated", "2.0.0")
    return platform in VISUAL_DEVICES


class CommonQuerySkill(NeonSkill, _CQS):
    """Question answering skills should be based on this class.

    The skill author needs to implement `CQS_match_query_phrase` returning an
    answer and can optionally implement `CQS_action` to perform additional
    actions if the skill's answer is selected.

    This class works in conjunction with skill-query which collects
    answers from several skills presenting the best one available.
    """
    def __init__(self, *args, **kwargs):
        log_deprecation("This base class is deprecated. Implement "
                        "`ovos_workshop.skills.common_query_skill."
                        "CommonQuerySkill`", "2.0.0")
        # these should probably be configurable
        self.level_confidence = {
            CQSMatchLevel.EXACT: 0.9,
            CQSMatchLevel.CATEGORY: 0.6,
            CQSMatchLevel.GENERAL: 0.5
        }

        # Manual init of OVOSSkill
        self.private_settings = None
        self._threads = []
        self._original_converse = self.converse
        self.intent_layers = IntentLayers()
        self.audio_service = None

        NeonSkill.__init__(self, *args, **kwargs)

        noise_words_filepath = f"text/{self.lang}/noise_words.list"
        default_res = f"{dirname(dirname(__file__))}/res/text/{self.lang}" \
                      f"/noise_words.list"
        noise_words_filename = \
            resolve_resource_file(noise_words_filepath,
                                  config=self.config_core) or \
            resolve_resource_file(default_res, config=self.config_core)

        self._translated_noise_words = {}
        if noise_words_filename:
            with open(noise_words_filename) as f:
                translated_noise_words = f.read().strip()
            self._translated_noise_words[self.lang] = \
                translated_noise_words.split()

    def __calc_confidence(self, match, phrase, level):
        # Assume the more of the words that get consumed, the better the match
        consumed_pct = len(match.split()) / len(phrase.split())
        if consumed_pct > 1.0:
            consumed_pct = 1.0

        # Add bonus if match has visuals and the device supports them.
        # platform = self.config_core.get('enclosure', {}).get('platform')
        # if is_CQSVisualMatchLevel(level) and handles_visuals(platform):
        #     bonus = 0.1
        # else:
        #     bonus = 0
        bonus = 0

        if int(level) == int(CQSMatchLevel.EXACT):
            return 0.9 + (consumed_pct / 10) + bonus
        elif int(level) == int(CQSMatchLevel.CATEGORY):
            return 0.6 + (consumed_pct / 10) + bonus
        elif int(level) == int(CQSMatchLevel.GENERAL):
            return 0.5 + (consumed_pct / 10) + bonus
        else:
            return 0.0  # should never happen

    def __handle_query_classic(self, message):
        """Message handler for question:action.

        Extracts phrase and data from message forward this to the skills
        CQS_action method.
        """
        if message.data["skill_id"] != self.skill_id:
            # Not for this skill!
            return
        LOG.debug(f"handling for ovos-core 0.0.7")
        phrase = message.data["phrase"]
        data = message.data.get("callback_data")
        # Invoke derived class to provide playback data
        self.CQS_action(phrase, data)
        self.bus.emit(message.forward("mycroft.skill.handler.complete",
                                      {"handler": "common_query"}))

    @backwards_compat(classic_core=__handle_query_classic,
                      pre_008=__handle_query_classic)
    def __handle_query_action(self, message):
        """
        If this skill's response was spoken to the user, this method is called.
        Phrase and callback data from `CQS_match_query_phrase` will be passed
        to the `CQS_action` method.
        @param message: `question:action` message
        """
        if message.data["skill_id"] != self.skill_id:
            # Not for this skill!
            return
        LOG.debug(f"handling for ovos-core 0.0.8")
        phrase = message.data["phrase"]
        data = message.data.get("callback_data") or {}
        if data.get("answer"):
            self.speak(data["answer"])
        else:
            LOG.error(f"no answer provided in: {message.data.keys()}")
        # Invoke derived class to provide playback data
        self.CQS_action(phrase, data)
        self.bus.emit(message.forward("mycroft.skill.handler.complete",
                                      {"handler": "common_query"}))

    def __handle_question_query(self, message):
        # Override ovos-workshop implementation that doesn't pass `message`
        search_phrase = message.data["phrase"]

        # First, notify the requestor that we are attempting to handle
        # (this extends a timeout while this skill looks for a match)
        self.bus.emit(message.response({"phrase": search_phrase,
                                        "skill_id": self.skill_id,
                                        "searching": True}))

        # Now invoke the CQS handler to let the skill perform its search
        result = self.CQS_match_query_phrase(search_phrase, message)

        if result:
            match = result[0]
            level = result[1]
            answer = result[2]
            callback = result[3] if len(result) > 3 else None
            callback["answer"] = answer
            confidence = self.__calc_confidence(match, search_phrase, level)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "answer": answer,
                                            "callback_data": callback,
                                            "conf": confidence}))
        else:
            # Signal we are done (can't handle it)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "searching": False}))

    @abstractmethod
    def CQS_match_query_phrase(self, phrase, message):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Needs to be implemented by the skill.

        Arguments:
            phrase (str): User phrase, "What is an aardwark"

        Returns:
            (match, CQSMatchLevel[, callback_data]) or None: Tuple containing
                 a string with the appropriate matching phrase, the PlayMatch
                 type, and optionally data to return in the callback if the
                 match is selected.
        """
        # Derived classes must implement this, e.g.
        return None

    def CQS_action(self, phrase, data):
        """Take additional action IF the skill is selected.

        The speech is handled by the common query but if the chosen skill
        wants to display media, set a context or prepare for sending
        information info over e-mail this can be implemented here.

        Args:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            data (dict): Callback data specified in match_query_phrase()
        """
        # Derived classes may implement this if they use additional media
        # or wish to set context after being called.
        pass
