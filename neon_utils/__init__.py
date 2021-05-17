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
