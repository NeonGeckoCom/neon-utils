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
# Copyright 2019 Mycroft AI Inc.
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

class MycroftSkill:
    """Base class for mycroft skills providing common behaviour and parameters
    to all Skill implementations.

    For information on how to get started with creating mycroft skills see
    https://mycroft.ai/documentation/skills/introduction-developing-skills/

    Arguments:
        name (str): skill name
        bus (MycroftWebsocketClient): Optional bus connection
        use_settings (bool): Set to false to not use skill settings at all
    """

    def __init__(self, name=None, bus=None, use_settings=True):
        self.name = name or self.__class__.__name__
        self.resting_name = None
        self.skill_id = ''  # will be set from the path, so guaranteed unique
        self.settings_meta = None  # set when skill is loaded in SkillLoader

        # Get directory of skill
        #: Member variable containing the absolute path of the skill's root
        #: directory. E.g. /opt/mycroft/skills/my-skill.me/
        self.root_dir = "root_dir"

        self.gui = "GUI_object"

        self._bus = None
        self._enclosure = None
        #: Mycroft global configuration. (dict)
        self.config_core = {}

        self.settings = None
        self.settings_write_path = None

        #: Set to register a callback method that will be called every time
        #: the skills settings are updated. The referenced method should
        #: include any logic needed to handle the updated settings.
        self.settings_change_callback = None

        self.dialog_renderer = None

        #: Filesystem access to skill specific folder.
        #: See mycroft.filesystem for details.
        self.file_system = "Something"

        self.log = "Logger"
        self.reload_skill = True  #: allow reloading (default True)

        self.events = "Object"
        self.voc_match_cache = {}

        # Delegator classes
        self.event_scheduler = "Object"
        self.intent_service = "Object"


class NeonSkill:
    """Base class for mycroft skills providing common behaviour and parameters
    to all Skill implementations.

    For information on how to get started with creating mycroft skills see
    https://mycroft.ai/documentation/skills/introduction-developing-skills/

    Arguments:
        name (str): skill name
        bus (MycroftWebsocketClient): Optional bus connection
        use_settings (bool): Set to false to not use skill settings at all
    """

    def __init__(self, name=None, bus=None, use_settings=True):
        super().__init__()
        # start = time.time()
        self.user_config = None
        self.local_config = None
        self.configuration_available = {}
        self.user_info_available = {}
        self.create_signal = None
        self.check_for_signal = None
        self.name = name or self.__class__.__name__
        self.resting_name = None
        self.skill_id = ''  # will be set from the path, so guaranteed unique
        self.settings_meta = None  # set when skill is loaded in SkillLoader
        self.ngi_settings = None
        # Get directory of skill
        #: Member variable containing the absolute path of the skill's root
        #: directory. E.g. /opt/mycroft/skills/my-skill.me/
        self.root_dir = "dir"
        self.sys_tz = None

        self.gui = None
        self.gui_enabled = False

        self._bus = None
        self._enclosure = None

        self.settings = None
        self.settings_write_path = None

        #: Set to register a callback method that will be called every time
        #: the skills settings are updated. The referenced method should
        #: include any logic needed to handle the updated settings.
        self.settings_change_callback = None

        self.dialog_renderer = None

        #: Filesystem access to skill specific folder.
        #: See mycroft.filesystem for details.
        self.file_system = "Object"

        self.log = "Object"
        # self.log = LOG
        self.reload_skill = True  #: allow reloading (default True)
        self.scheduled_repeats = []
        self.skill_id = ''  # will be set from the path, so guaranteed unique
        self.events = "Object"
        self.voc_match_cache = {}
        self.cache_loc = "path"

        # Load location caches
        self.location_dict = dict()  # (lat/lng: {city, state, country})
        self.long_lat_dict = dict()  # (Location Name: {lat, lng})
        self.long_name_dict = dict()  # (short name (input string): {city, state, country})
        self.loc_cache = "path"
        self.coord_cache = "path"
        self.loc_name_cache = "path"

        self.server = False
        # self.gui_enabled = True
        self.default_intent_timeout = 60

        self.neon_core = True
        self.actions_to_confirm = dict()

        # Delegator classes
        self.event_scheduler = "Object"
        self.intent_service = "Object"

        # self.keys = get_private_keys()

        # Lang support
        self.language_config = {}
        self.lang_detector = "Object"
        self.translator = "Object"

        # if self.gui_enabled and self.settings and len(self.settings.keys()) > 0:
        #     try:
        #         self.gui.register_settings()
        #     except Exception as e:
        #         LOG.error(e)
