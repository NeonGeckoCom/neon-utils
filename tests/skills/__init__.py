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

from neon_utils.skills import *


class TestCMS(CommonMessageSkill):
    def __init__(self):
        super(TestCMS, self).__init__(name="Test Common Message Skill")

    def CMS_match_message_phrase(self, request, context):
        pass

    def CMS_handle_send_message(self, message):
        pass

    def CMS_match_call_phrase(self, contact, context):
        pass

    def CMS_handle_place_call(self, message):
        pass


class TestCPS(CommonPlaySkill):
    def __init__(self):
        super(TestCPS, self).__init__(name="Test Common Play Skill")

    def CPS_match_query_phrase(self, phrase, message):
        pass

    def CPS_start(self, phrase, data, message=None):
        pass


class TestCQS(CommonQuerySkill):
    def __init__(self):
        super(TestCQS, self).__init__(name="Test Common Query Skill")

    def CQS_match_query_phrase(self, phrase, message):
        pass


class TestFBS(NeonFallbackSkill):
    def __init__(self):
        super(TestFBS, self).__init__(name="Test Fallback Skill")


class TestNeonSkill(NeonSkill):
    def __init__(self):
        super(TestNeonSkill, self).__init__(name="Test Neon Skill")
