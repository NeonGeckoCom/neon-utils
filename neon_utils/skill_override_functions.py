# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2020 Neongecko.com Inc. | All Rights Reserved
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
# US Patents 2008-2020: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

from mycroft_bus_client import Message


def neon_must_respond(message: Message):
    return True


def neon_in_request(message: Message):
    return True


def request_from_mobile(message: Message):
    return True


def preference_brands(message: Message):
    return {'ignored_brands': {},
            'favorite_brands': {},
            'specially_requested': {}}


def preference_user(message: Message):
    return {}


def preference_location(message: Message):
    return {}


def preference_unit(message: Message):
    return {}


def preference_speech(message: Message):
    return {}


def build_user_dict(message: Message = None):
    merged_dict = {**preference_speech(message), **preference_user(message),
                   **preference_brands(message), **preference_location(message),
                   **preference_unit(message)}
    for key, value in merged_dict.items():
        if value == "":
            merged_dict[key] = -1
    return merged_dict


