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

import base64
import inspect

from typing import Optional
from mycroft_bus_client import Message


class EncodingError(ValueError):
    """Exception to indicate an invalid Encoding"""


def request_from_mobile(message: Message) -> bool:
    """
    Check if a request is from a mobile device
    Args:
        message: Message object associated with request

    Returns:
        True if message is from a mobile app, else False
    """
    return message.context.get("mobile", False)


def get_message_user(message: Message) -> Optional[str]:
    """
    Get the user associated with a message
    Args:
        message: Message object associated with request

    Returns:
        Username associated with message
    """
    if not message:
        raise ValueError
    if not hasattr(message, "context"):
        raise AttributeError(type(message))
    return message.context.get("username")


def encode_bytes_to_b64_string(data: bytes, charset: str = "utf-8") -> str:
    """
    Encode a bytes object into a string that can be passed on the messagebus
    :param data: bytes data to be encoded
    :param charset: character set to decode b64 bytes (https://docs.python.org/3/library/codecs.html#standard-encodings)
    :return: base64 encoded string
    """
    if not data or not isinstance(data, bytes):
        raise ValueError(f"Invalid data provided to be encoded. type={type(data)}")

    encoded = base64.b64encode(data)

    try:
        bytestr = encoded.decode(charset)
    except LookupError:
        raise EncodingError(f"Invalid charset provided: {charset}")

    return bytestr


def decode_b64_string_to_bytes(data: str, charset: str = "utf-8") -> bytes:
    """
    Decodes a base64-encoded string to bytes
    :param data: string encoded data to decode
    :param charset: character set of b64 string (https://docs.python.org/3/library/codecs.html#standard-encodings)
    :return: decoded bytes object
    """
    if not data or not isinstance(data, str):
        raise ValueError(f"Invalid data provided to be encoded. type={type(data)}")

    try:
        byte_data = data.encode(charset)
    except LookupError:
        raise EncodingError(f"Invalid charset provided: {charset}")

    encoded = base64.b64decode(byte_data)

    if not encoded:
        raise EncodingError(f"Invalid charset provided for data. charset={charset}")

    return encoded


def dig_for_message(max_records: int = 10) -> Optional[Message]:
    """
    Dig Through the stack for message. Looks at the current stack for a passed argument of type 'Message'
    :param max_records: Maximum number of stack records to look through
    :return: Message if found in args, else None
    """
    stack = inspect.stack()[1:]  # First frame will be this function call
    stack = stack if len(stack) <= max_records else stack[:max_records]
    for record in stack:
        args = inspect.getargvalues(record.frame)
        if args.args:
            for arg in args.args:
                if isinstance(args.locals[arg], Message):
                    return args.locals[arg]
    return None
