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

import os
import base64

from ovos_utils.signal import ensure_directory_exists

from neon_utils import LOG


def encode_file_to_base64_string(path: str) -> str:
    """
    Encodes a file to a base64 string (useful for passing file data over a messagebus)
    :param path: Path to file to be encoded
    :return: encoded string
    """
    if not isinstance(path, str):
        raise TypeError
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        LOG.error(f"File Not Found: {path}")
        raise FileNotFoundError
    with open(path, "rb") as file_in:
        encoded = base64.b64encode(file_in.read()).decode("utf-8")
    return encoded


def decode_base64_string_to_file(encoded_string: str, output_path: str) -> str:
    """
    Writes out a base64 string to a file object at the specified path
    :param encoded_string: Base64 encoded string
    :param output_path: Path to file to write (throws exception if file exists)
    :return: Path to output file
    """
    if not isinstance(output_path, str):
        raise TypeError
    output_path = os.path.expanduser(output_path)
    if os.path.isfile(output_path):
        LOG.error(f"File already exists: {output_path}")
        raise FileExistsError
    ensure_directory_exists(os.path.dirname(output_path))
    with open(output_path, "wb+") as file_out:
        byte_data = base64.b64decode(encoded_string.encode("utf-8"))
        file_out.write(byte_data)
    return output_path
