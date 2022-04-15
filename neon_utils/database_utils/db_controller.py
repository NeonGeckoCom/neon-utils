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

from neon_utils.database_utils.mongodb_connector import MongoDBConnector
from neon_utils.database_utils.mysql_connector import MySQLConnector

from neon_utils.database_utils.base_connector import DatabaseConnector, DatabaseTypes


class DatabaseController:

    database_class_mapping = {'mongo': MongoDBConnector,
                              'mysql': MySQLConnector}

    def __init__(self, config_data: dict):
        self._connector = None
        self.config_data = config_data

    @property
    def connector(self) -> DatabaseConnector:
        return self._connector

    def attach_connector(self, dialect: str):
        """
            Creates database connector instance base on the given class

            :param dialect: name of the dialect to for connection
        """
        if dialect not in list(self.database_class_mapping):
            raise AssertionError(f'Invalid dialect provided, supported are: {list(self.database_class_mapping)}')
        self._connector = self.database_class_mapping[dialect](config_data=self.config_data)

    def detach_connector(self, graceful_termination_func: callable = None):
        """
            Drops current database connector connection

            :param graceful_termination_func: function causing graceful termination of connector instance (optional)
        """
        if graceful_termination_func:
            graceful_termination_func(self._connector)
        else:
            self._connector = None

    def exec_query(self, query, *args, **kwargs):
        return self.connector.exec_raw_query(query=query, *args, **kwargs)

    def connect(self):
        self.connector.create_connection()

    def disconnect(self):
        self.connector.abort_connection()

    def get_type(self) -> DatabaseTypes:
        return self.connector.database_type
