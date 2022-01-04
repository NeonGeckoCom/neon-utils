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

from neon_utils.skill_override_functions import *
from neon_utils.variables_override import *
from neon_utils.logger import LOG

from ovos_utils.gui import is_gui_installed

SKILL = None
TYPE = None


def skill_needs_patching(skill):
    """
    Determines if the passed skill is running under a non-Neon core and needs to be patched for compatibility
    :param skill: MycroftSkill object to test
    :return: True if skill needs to be patched
    """
    LOG.warning(f"This method is depreciated. Please update your skill to extend NeonSkill instead.")
    return not hasattr(skill, "neon_core")


def stub_missing_parameters(skill):
    global SKILL
    global TYPE

    LOG.warning(f"This method is depreciated. Please update your skill to extend NeonSkill instead.")

    SKILL = skill
    TYPE = type(skill)
    LOG.debug(SKILL)
    LOG.debug(TYPE)

    skill.actions_to_confirm = dict()
    skill.default_intent_timeout = None
    skill.server = False
    skill.gui_enabled = is_gui_installed()  # This isn't a check for running, just available DM

    skill.neon_in_request = neon_in_request
    skill.neon_must_respond = neon_must_respond
    skill.request_from_mobile = request_from_mobile
    skill.speak_dialog = speak_dialog
    skill.speak = speak
    skill.create_signal = create_signal
    skill.check_for_signal = check_for_signal
    skill.clear_signals = clear_signals

    skill.preference_brands = preference_brands
    skill.preference_user = preference_user
    skill.preference_location = preference_location
    skill.preference_unit = preference_unit
    skill.preference_speech = preference_speech
    skill.preference_skill = preference_skill
    skill.build_user_dict = build_user_dict
    skill.request_check_timeout = request_check_timeout
    skill.get_utterance_user = get_utterance_user
    skill.update_skill_settings = update_skill_settings

    skill.neon_core = False
    skill.configuration_available = configuration_available

    try:
        # TODO: This should really be global to match Neon.. Maybe /opt/mycroft? DM
        skill.cache_loc = os.path.join(skill.__location__, "cache")
    except Exception as e:
        LOG.error(e)
        skill.cache_loc = os.path.join("tmp", "mycroft", "cache")

    skill.get_cached_data = get_cached_data
    skill.update_cached_data = update_cached_data
    skill.build_message = build_message

    skill.speak = speak
    skill.wait_while_speaking = wait_while_speaking
    skill.is_speaking = is_speaking
    skill.to_system_time = to_system_time

    skill.check_yes_no_response = check_yes_no_response
