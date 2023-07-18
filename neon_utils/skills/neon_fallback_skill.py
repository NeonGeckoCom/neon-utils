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

from neon_utils.skills.neon_skill import NeonSkill
from ovos_workshop.skills.ovos import OVOSSkill
from ovos_utils.intents import IntentLayers
from ovos_workshop.decorators.layers import IntentLayers
from ovos_workshop.skills.fallback import FallbackSkillV1 as FallbackSkill


class NeonFallbackSkill(FallbackSkill, NeonSkill, OVOSSkill):
    """
    Class that extends the NeonSkill and FallbackSkill classes to provide
    NeonSkill functionality to any Fallback skill subclassing this class.
    """
    def __init__(self, *args, **kwargs):
        # Manual init of OVOSSkill
        self.private_settings = None
        self._threads = []
        self._original_converse = self.converse
        self.intent_layers = IntentLayers()
        self.audio_service = None

        # Manual init of FallbackSkill
        #  list of fallback handlers registered by this instance
        self.instance_fallback_handlers = []
        NeonSkill.__init__(self, *args, **kwargs)

    @property
    def fallback_config(self):
        # "skill_id": priority (int)  overrides
        return self.config_core["skills"].get("fallbacks", {})