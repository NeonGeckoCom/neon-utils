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
import lingua_nostra.lang


def numeric_confirmation_validator(confirmation_num: str, lang: str = "en"):
    """
    Returns a validator method that returns true if the passed confirmation_num is in the passed string.
     The confirmation_num must be the only number in the utterance (something 123 != 1 something 123).
    :param confirmation_num: number to locate in utterance
    :param lang: language to use for extracting number from strings
    :return: True if the confirmation is in the spoken utterance.
    """
    if not isinstance(confirmation_num, str):
        raise TypeError(f"Expected str, got {type(confirmation_num)}")
    if not confirmation_num.isnumeric():
        raise ValueError(f"{confirmation_num} is not numeric")

    from lingua_nostra.parse import extract_numbers
    lingua_nostra.lang.set_active_lang(lang)

    def wrapped_validator(utt):
        spoken_num = "".join([str(round(n)) for n in extract_numbers(utt)])
        return confirmation_num == spoken_num
    return wrapped_validator
