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

from mysql.connector import (connection)

from typing import Optional
from neon_utils import LOG
from neon_utils.database_utils.base_connector import DatabaseConnector, DatabaseTypes


class MySQLConnector(DatabaseConnector):
    """Base connector for all MySQL-related dbs"""

    @property
    def database_type(self):
        return DatabaseTypes.RELATIONAL

    def create_connection(self):
        self._cnx = connection.MySQLConnection(**self.config_data)

    def abort_connection(self):
        self._cnx.close()

    def exec_raw_query(self, query: str, generator: bool = False, *args, **kwargs) -> Optional[list]:
        """Executes raw string query and returns its results

            :param query: valid SQL query string
            :param generator: to return cursor as generator object (defaults to False)

            :returns query result if any
        """
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, *args, **kwargs)
        result = None
        try:
            result = cursor.fetchall()
        except Exception as ex:
            LOG.error(ex)
        finally:
            cursor.close()
            return result
