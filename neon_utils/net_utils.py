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

import socket
import netifaces


def get_ip_address() -> str:
    """
    Returns the IPv4 address of the default interface (This is a public IP for server implementations)
    :return: IP Address
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def get_adapter_info(interface: str = "default") -> dict:
    """
    Returns MAC and IP info for the specified gateway
    :param interface: Name of network interface to check
    :return: Dict of mac, IPv4 and IPv6 addresses
    """
    gateways = netifaces.gateways()
    if interface not in gateways:
        raise IndexError("Requested Interface Not Found")
    if netifaces.AF_INET not in gateways[interface]:
        raise IndexError("Requested Interface not connected!")
    device = gateways[interface][netifaces.AF_INET][1]
    mac = netifaces.ifaddresses(device)[netifaces.AF_LINK][0]['addr']
    ip4 = netifaces.ifaddresses(device)[netifaces.AF_INET][0]['addr']
    ip6 = netifaces.ifaddresses(device)[netifaces.AF_INET6][0]['addr']
    return {"ipv4": ip4, "ipv6": ip6, "mac": mac}
