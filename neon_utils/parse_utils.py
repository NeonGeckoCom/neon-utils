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

def clean_quotes(raw_utt):
    """
    Method for stripping quotes from fully quoted strings in different languages
    :param raw_utt: Input string to be cleaned
    :return: string with all paired quote characters removed
    """
    chars_to_remove = ['“', '"', '«', u'\u201d', u'\u00bb', u'\u201e', '「', '」', u'u\xa0', u'\u00a0']
    raw_utt = raw_utt.strip()
    # LOG.debug(f"clean_utterance({raw_utt})")
    utt = raw_utt
    trailing_punctuation = False
    if utt.endswith("."):
        trailing_punctuation = True
        utt = utt.rstrip(".")
    quotes_cleaned = False
    try:
        # Checks if utterance starts AND ends with some form of quotations and removes them accordingly
        while (utt.startswith('“') or utt.startswith(u'\u201d') or utt.startswith('"') or utt.startswith('«')
               or utt.startswith(u'\u00bb') or utt.startswith(u'\u201e') or utt.startswith('「') or
               utt.startswith(u'u\xa0') or utt.startswith(u'\u00a0')) and \
                (utt.endswith('“') or utt.endswith(u'\u201d') or utt.endswith('"') or utt.endswith(u'\u00bb') or
                 utt.endswith(u'\u201e') or utt.endswith('」') or utt.endswith(u'u\xa0') or
                 utt.endswith(u'\u00a0') or utt.endswith('»')):
            # LOG.debug("DM: Handling Quotations")
            quotes_cleaned = True
            removed_left, removed_right = False, False
            for c in chars_to_remove:
                if not removed_left and utt.startswith(c):
                    utt = utt[1:]
                    removed_left = True
                if not removed_right and utt.endswith(c):
                    utt = utt[:-1]
                    removed_right = True
            # utt = raw_utt.lstrip('“').lstrip(u'\u201d').lstrip('"').lstrip('«') \
            #     .lstrip(u'\u00bb').lstrip(u'\u201e').rstrip('“').rstrip(u'\u201d').rstrip('"').rstrip('«') \
            #     .rstrip(u'\u00bb').rstrip(u'\u201e')
        # else:
        #     utt = raw_utt
        # LOG.debug(f"DM: {utt}")
        if quotes_cleaned:
            if trailing_punctuation:
                return f"{utt}."
            return utt
        else:
            return raw_utt
    except Exception as x:
        print(x)
        return raw_utt
