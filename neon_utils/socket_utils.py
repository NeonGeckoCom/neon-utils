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
import json
import base64

# Limited maximum tcp packet size to 10 MB;
# Implied by the fact that TCP client aborts the connection once has its packet delivered to server
# thus preventing from sequential traversing
MAX_PACKET_SIZE = 10485760


def get_packet_data(socket, sequentially=False, batch_size=2048) -> bytes:
    """
        Gets all packet data by reading TCP socket stream sequentially
        :@param socket: TCP socket
        :@param sequentially: marker indicating whether received packet data should be read once or sequentially
        :@param batch_size: size of packet added through one sequence

        :@return bytes string representing the received data
    """
    if sequentially:
        fragments = []
        while True:
            chunk = socket.recv(batch_size)
            if not chunk:
                break
            fragments.append(chunk)
        data = b''.join(fragments)
    else:
        data = bytes(socket.recv(MAX_PACKET_SIZE))
    return data


def b64_to_dict(data: bytes, charset: str = "utf-8") -> dict:
    """
        Decodes base64-encoded message to python dictionary
        @param data: string bytes to decode
        @param charset: character set encoding to use (https://docs.python.org/3/library/codecs.html#standard-encodings)

        @return decoded dictionary
    """
    return eval(json.loads(base64.b64decode(data).decode(charset)))


def dict_to_b64(data: dict, charset: str = "utf-8") -> bytes:
    """
        Encodes python dictionary into base64 message
        @param data: python dictionary to encode
        @param charset: character set encoding to use (https://docs.python.org/3/library/codecs.html#standard-encodings)

        @return base64 encoded string
    """
    return base64.b64encode(json.dumps(str(data)).encode(charset))
