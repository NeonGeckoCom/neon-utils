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
        self.file_system = FileSystemAccess(os.path.join('skills', self.name))
        if is_neon_core():
            skill_id = os.path.basename(os.path.dirname(os.path.abspath(sys.modules[self.__module__].__file__)))
            LOG.info("Patching skill file system path")
            self.file_system.path = os.path.join(os.path.expanduser(get_neon_local_config()["dirVars"].get("confDir")
                                                                    or "~/.config/neon"), "skills", skill_id)
            if not os.path.isdir(self.file_system.path):
                os.makedirs(self.file_system.path)
        fs_path = deepcopy(self.file_system.path)
        super(PatchedMycroftSkill, self).__init__(name, bus, use_settings)
        self.file_system.path = fs_path
        self.config_core = get_mycroft_compatible_config()

    def _init_settings(self):
        self.settings_write_path = self.file_system.path
        skill_settings = get_local_settings(self.settings_write_path, self.name)
        self.settings = dict_update_keys(skill_settings, self._read_default_settings())
        if self.settings != skill_settings:
            with open(self.settings_write_path, "w+") as f:
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
