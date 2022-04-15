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

from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


class DatabaseTypes(Enum):
    RELATIONAL = 1
    NOSQL = 2


class DatabaseConnector(ABC):
    """Base class for database"""

    def __init__(self, config_data: dict):
        self.config_data = config_data
        self._cnx = None

    @property
    @abstractmethod
    def database_type(self) -> DatabaseTypes:
        pass

    @property
    def connection(self):
        return self._cnx

    @abstractmethod
    def create_connection(self):
        """Creates new database connection"""
        pass

    @abstractmethod
    def abort_connection(self):
        """Aborts existing connection"""
        pass

    @abstractmethod
    def exec_raw_query(self, query: str, *args) -> Optional[object]:
        """
            Executes raw query returns result if needed
            :param query: query to execute
            :param args: query args (if needed)
        """
        pass
