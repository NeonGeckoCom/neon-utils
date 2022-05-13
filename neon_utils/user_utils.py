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

from os.path import isfile, join
from mycroft_bus_client import Message, MessageBusClient

from neon_utils.message_utils import resolve_message, get_message_user
from neon_utils.configuration_utils import get_neon_user_config, \
    dict_make_equal_keys, get_config_dir, get_user_config_from_mycroft_conf, dict_merge
from neon_utils.logger import LOG

_DEFAULT_USER_CONFIG = None


def get_default_user_config() -> dict:
    """
    Get the default user configuration from global yml and Mycroft config
    :returns: default user config from existing ngi_user_info or mycroft.conf
    """
    global _DEFAULT_USER_CONFIG
    if not _DEFAULT_USER_CONFIG:
        if isfile(join(get_config_dir(), "ngi_user_info.yml")):
            _DEFAULT_USER_CONFIG = get_neon_user_config().content
        else:
            _DEFAULT_USER_CONFIG = get_user_config_from_mycroft_conf()
    return _DEFAULT_USER_CONFIG


@resolve_message
def get_user_prefs(message: Message = None) -> dict:
    """
    Get a dict of user preferences from the given message
    :param message: Message associated with user request
    :returns: dict configuration following the structure of ngi_user_info
    """
    default_user_config = get_default_user_config()
    if not message:
        return default_user_config

    username = get_message_user(message)
    if not username:
        return default_user_config

    # nick_profiles is here for legacy support, spec calls for 'user_profiles'
    profile_key = "user_profiles" if "user_profiles" in message.context else \
        "nick_profiles" if "nick_profiles" in message.context else None

    if not profile_key:
        LOG.debug("No profile data in message, returning default")
        return default_user_config
    if not isinstance(message.context[profile_key], list):
        LOG.warning(f"Invalid data found in {profile_key}: "
                    f"{message.context[profile_key]}")
        return default_user_config

    for profile in message.context.get(profile_key):
        if profile["user"]["username"] == username:
            return dict(dict_make_equal_keys(profile, default_user_config))
    LOG.warning(f"No preferences found for {username} in {message.context}")
    return default_user_config


@resolve_message
def update_user_profile(new_preferences: dict, message: Message = None,
                        bus: MessageBusClient = None):
    """
    Update a
    """
    if not message:
        raise ValueError("No message associated with profile update.")

    # Update current message object and get updated profile
    username = get_message_user(message)
    user_profile = None
    if username and 'nick_profiles' in message.context:
        LOG.warning("nick_profiles found and will be updated")
        old_preferences = message.context["nick_profiles"][username]
        user_profile = dict_merge(old_preferences, new_preferences)
        message.context["nick_profiles"][username] = user_profile
    elif username and 'user_profiles' in message.context:
        LOG.debug("updating user_profiles")
        for i, profile in enumerate(message.context['user_profiles']):
            if profile['user']['username'] == username:
                user_profile = dict_merge(profile, new_preferences)
                message.context['user_profiles'][i] = user_profile
                break

    if not user_profile:
        raise RuntimeError(f"No profile found for user: {username}.")

    # Notify connector modules of update
    bus = bus or MessageBusClient()
    update_message = message.forward("neon.profile_update", dict(user_profile))
    bus.emit(update_message)