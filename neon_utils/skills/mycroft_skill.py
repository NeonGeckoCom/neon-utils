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

import sys
import json
import os.path

from copy import deepcopy
from ruamel.yaml import YAML

from neon_utils.logger import LOG
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

    def _init_settings(self):
        self.settings_write_path = self.file_system.path
        skill_settings = get_local_settings(self.settings_write_path, self.name)
        settings_from_disk = deepcopy(skill_settings)
        self.settings = dict_update_keys(skill_settings, self._read_default_settings())
        if self.settings != settings_from_disk:
            with open(os.path.join(self.settings_write_path, 'settings.json'), "w+") as f:
                json.dump(self.settings, f, indent=4)
        self._initial_settings = deepcopy(self.settings)

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
