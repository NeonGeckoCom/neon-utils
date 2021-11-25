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
