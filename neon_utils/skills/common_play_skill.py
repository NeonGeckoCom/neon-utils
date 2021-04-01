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
#
# This software is an enhanced derivation of the Mycroft Project which is licensed under the
# Apache software Foundation software license 2.0 https://www.apache.org/licenses/LICENSE-2.0
# Changes Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
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

import re
from enum import IntEnum
from abc import ABC, abstractmethod
from mycroft_bus_client import Message
from neon_utils.skills.neon_skill import NeonSkill

from mycroft.skills.common_play_skill import CPSMatchLevel, CommonPlaySkill as CPS


class CPSTrackStatus(IntEnum):
    DISAMBIGUATION = 1  # not queued for playback, show in gui
    PLAYING = 20  # Skill is handling playback internally
    PLAYING_AUDIOSERVICE = 21  # Skill forwarded playback to audio service
    PLAYING_GUI = 22  # Skill forwarded playback to gui
    PLAYING_ENCLOSURE = 23  # Skill forwarded playback to enclosure
    QUEUED = 30  # Waiting playback to be handled inside skill
    QUEUED_AUDIOSERVICE = 31  # Waiting playback in audio service
    QUEUED_GUI = 32  # Waiting playback in gui
    QUEUED_ENCLOSURE = 33  # Waiting for playback in enclosure
    PAUSED = 40  # media paused but ready to resume
    STALLED = 60  # playback has stalled, reason may be unknown
    BUFFERING = 61  # media is buffering from an external source
    END_OF_MEDIA = 90  # playback finished, is the default state when CPS loads


class CommonPlaySkill(NeonSkill, CPS, ABC):
    """ To integrate with the common play infrastructure of Mycroft
    skills should use this base class and override the two methods
    `CPS_match_query_phrase` (for checking if the skill can play the
    utterance) and `CPS_start` for launching the media.

    The class makes the skill available to queries from the
    mycroft-playback-control skill and no special vocab for starting playback
    is needed.
    """
    def __init__(self, name=None, bus=None):
        super().__init__(name, bus)
        self.audioservice = None
        self.play_service_string = None

        # "MusicServiceSkill" -> "Music Service"
        spoken = name or self.__class__.__name__
        self.spoken_name = re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>",
                                  spoken.replace("Skill", ""))
        # NOTE: Derived skills will likely want to override self.spoken_name
        # with a translatable name in their initialize() method.

    def __handle_play_query(self, message):
        """Query skill if it can start playback from given phrase."""
        search_phrase = message.data["phrase"]

        # First, notify the requestor that we are attempting to handle
        # (this extends a timeout while this skill looks for a match)
        self.bus.emit(message.response({"phrase": search_phrase,
                                        "skill_id": self.skill_id,
                                        "searching": True}))

        # Now invoke the CPS handler to let the skill perform its search
        result = self.CPS_match_query_phrase(search_phrase, message)

        if result:
            match = result[0]
            level = result[1]
            callback = result[2] if len(result) > 2 else None
            confidence = self.__calc_confidence(match, search_phrase, level)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "callback_data": callback,
                                            "service_name": self.spoken_name,
                                            "conf": confidence}))
        else:
            # Signal we are done (can't handle it)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "searching": False}))

    def __handle_play_start(self, message):
        """Bus handler for starting playback using the skill."""
        if message.data["skill_id"] != self.skill_id:
            # Not for this skill!
            return
        phrase = message.data["phrase"]
        data = message.data.get("callback_data")

        # Stop any currently playing audio
        if self.audioservice.is_playing:
            self.audioservice.stop()
        # self.bus.emit(message.forward("mycroft.stop"))
        # TODO: maybe do this with some param to not clear gui in CP skills DM

        # Save for CPS_play() later, e.g. if phrase includes modifiers like
        # "... on the chromecast"
        self.play_service_string = phrase

        # Invoke derived class to provide playback data
        self.CPS_start(phrase, data, message)

    ######################################################################
    # Abstract methods
    # All of the following must be implemented by a skill that wants to
    # act as a CommonPlay Skill
    @abstractmethod
    def CPS_match_query_phrase(self, phrase, message):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            message (Message): Message associated with request
        Returns:
            (match, CPSMatchLevel[, callback_data]) or None: Tuple containing
                 a string with the appropriate matching phrase, the PlayMatch
                 type, and optionally data to return in the callback if the
                 match is selected.
        """
        # Derived classes must implement this, e.g.
        #
        # if phrase in ["Zoosh"]:
        #     return ("Zoosh", CPSMatchLevel.Generic, {"hint": "music"})
        # or:
        # zoosh_song = find_zoosh(phrase)
        # if zoosh_song and "Zoosh" in phrase:
        #     # "play Happy Birthday in Zoosh"
        #     return ("Zoosh", CPSMatchLevel.MULTI_KEY, {"song": zoosh_song})
        # elif zoosh_song:
        #     # "play Happy Birthday"
        #     return ("Zoosh", CPSMatchLevel.TITLE, {"song": zoosh_song})
        # elif "Zoosh" in phrase
        #     # "play Zoosh"
        #     return ("Zoosh", CPSMatchLevel.GENERIC, {"cmd": "random"})
        return None

    @abstractmethod
    def CPS_start(self, phrase, data, message=None):
        """Begin playing whatever is specified in 'phrase'

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            data (dict): Callback data specified in match_query_phrase()
            message (Message): Message associated with request
        """
        # Derived classes must implement this, e.g.
        # self.CPS_play("http://zoosh.com/stream_music")
        pass
