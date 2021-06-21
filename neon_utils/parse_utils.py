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

import nltk
import re
import os

from neon_utils.logger import LOG


def clean_quotes(raw_utt: str) -> str:
    """
    Method for stripping quotes from fully quoted strings in different languages
    :param raw_utt: Input string to be cleaned
    :return: string with all paired quote characters removed
    """
    if not raw_utt:
        raise ValueError("Expected a string and got None")
    if not isinstance(raw_utt, str):
        raise TypeError(f"{raw_utt} is not a string!")
    chars_to_remove = ['“', '"', '«', u'\u201d', u'\u00bb', u'\u201e', '「', '」', u'u\xa0', u'\u00a0']
    raw_utt = raw_utt.strip()
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
            quotes_cleaned = True
            removed_left, removed_right = False, False
            for c in chars_to_remove:
                if not removed_left and utt.startswith(c):
                    utt = utt[1:]
                    removed_left = True
                if not removed_right and utt.endswith(c):
                    utt = utt[:-1]
                    removed_right = True
        if quotes_cleaned:
            if trailing_punctuation:
                return f"{utt}."
            return utt
        else:
            return raw_utt
    except Exception as x:
        LOG.error(x)
        return raw_utt


def clean_filename(raw_name: str, to_lowercase: bool = False) -> str:
    """
    Cleans a filename of any invalid characters
    :param raw_name: input file basename to clean
    :param to_lowercase: cast string to lowercase
    :return: cleaned file basename
    """
    if not raw_name:
        raise ValueError
    invalid_chars = ('/', '\\', '*', '~', ':', '"', '<', '>', '|', '?')
    name = raw_name
    for char in invalid_chars:
        name = name.replace(char, "_")
    if to_lowercase:
        name = name.lower()
    return name


def clean_transcription(raw_string: str) -> str:
    """
    Cleans up input transcriptions to replace any special characters with text
    :param raw_string: Input string to be cleaned
    :return: Cleaned string of alphas
    """
    if not raw_string:
        raise ValueError
    parsed = raw_string.lower().replace('%', ' percent').replace('.', ' ').replace('?', '').replace('-', ' ').strip()
    # TODO: Cleanup to alpha string (replace all chars)
    return parsed


def get_phonemes(phrase: str) -> str:
    """
    Gets phonemes for the requested phrase
    :param phrase: String phrase for which to get phonemes
    :return: ARPAbet phonetic representation (https://en.wikipedia.org/wiki/ARPABET)
    """
    download_path = os.path.expanduser("~/.local/share/neon")
    if not os.path.isdir(download_path):
        os.makedirs(download_path)
    nltk.download('cmudict', download_dir=download_path)
    nltk.data.path.append(download_path)

    output = ''
    for word in phrase.split():
        phoenemes = nltk.corpus.cmudict.dict()[word.lower()][0]
        for phoeneme in phoenemes:
            output += str(re.sub('[0-9]', '', phoeneme) + ' ')
        output += '. '
    return output.rstrip()


def format_speak_tags(sentence: str, include_tags: bool = True) -> str:
    """
    Cleans up SSML tags for speech synthesis and ensures the phrase is wrapped in 'speak' tags and any excluded text is
    removed.
    Args:
        sentence: Input sentence to be spoken
        include_tags: Flag to include <speak> tags in returned string
    Returns:
        Cleaned sentence to pass to TTS
    """
    # Wrap sentence in speak tag if no tags present
    if "<speak>" not in sentence and "</speak>" not in sentence:
        to_speak = f"<speak>{sentence}</speak>"
    # Assume speak starts at the beginning of the sentence if a closing speak tag is found
    elif "<speak>" not in sentence:
        to_speak = f"<speak>{sentence}"
    # Assume speak ends at the end of the sentence if an opening speak tag is found
    elif "</speak>" not in sentence:
        to_speak = f"{sentence}</speak>"
    else:
        to_speak = sentence

    # Trim text outside of speak tags
    if not to_speak.startswith("<speak>"):
        to_speak = f"<speak>{to_speak.split('<speak>', 1)[1]}"

    if not to_speak.endswith("</speak>"):
        to_speak = f"{to_speak.split('</speak>', 1)[0]}</speak>"

    if to_speak == "<speak></speak>":
        return ""

    if include_tags:
        return to_speak
    else:
        return to_speak.lstrip("<speak>").rstrip("</speak>")


def normalize_string_to_speak(to_speak: str) -> str:
    """
    Normalizes spoken strings for TTS engines to handle
    :param to_speak: String to speak
    :return: string with any invalid characters removed and punctuation added
    """
    if not to_speak:
        raise ValueError("Expected a string and got None")
    if not isinstance(to_speak, str):
        raise TypeError(f"{to_speak} is not a string!")

    valid_punctuation = ['.', '?', '!']
    if any(to_speak.endswith(x) for x in valid_punctuation):
        return to_speak
    return f"{to_speak}."
