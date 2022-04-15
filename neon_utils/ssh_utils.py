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
# Authors: Guy Daniels, Daniel McKnight, Elon Gasper, Richard Leeds, Kirill Hrymailo
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

from sshtunnel import SSHTunnelForwarder


def create_tunnel(server_address: str, username: str, password: str = None,
                  private_key: str = None,
                  private_key_password: str = None,
                  remote_bind_address: tuple = ('127.0.0.1', 8080)) -> SSHTunnelForwarder:
    """
        Creates tunneled SSH connection to dedicated address

        :param server_address: ssh server address
        :param username: server username
        :param password: server password (mutually exclusive with :param private_key)
        :param private_key: private key to server (mutually exclusive with :param password)
        :param private_key_password: private key password to server (optional)
        :param remote_bind_address: remote address to bind to
    """
    server = SSHTunnelForwarder(
        server_address,
        ssh_username=username,
        ssh_password=password,
        ssh_pkey=private_key,
        ssh_private_key_password=private_key_password,
        remote_bind_address=remote_bind_address
    )
    server.start()
    return server
