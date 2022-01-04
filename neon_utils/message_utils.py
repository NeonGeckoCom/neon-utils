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
