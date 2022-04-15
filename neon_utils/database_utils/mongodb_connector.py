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

from typing import Optional
from pymongo import MongoClient
from neon_utils import LOG

from neon_utils.database_utils.base_connector import DatabaseConnector, DatabaseTypes


class MongoDBConnector(DatabaseConnector):

    mongo_recognised_commands = ('insert_one', 'insert_many', 'delete_one', 'bulk_write',
                                 'delete_many', 'find', 'find_one', 'update')

    @property
    def database_type(self) -> DatabaseTypes:
        return DatabaseTypes.NOSQL

    def create_connection(self):
        database = self.config_data.pop('database')
        self._cnx = MongoClient(**self.config_data)[database]

    def abort_connection(self):
        self._cnx.close()

    def exec_raw_query(self, query: dict, *args, **kwargs) -> Optional[dict]:
        """
            Generic method for executing query over mongo db

            :param query: dictionary with query instruction has to contain following parameters:
                - "document": target document for query
                - "command": member of the self.mongo_recognised_commands
                - "data": query data, represented as a tuple of (List[dict] if bulk insert, dict otherwise)

            :returns result of the query execution if any
        """
        received_command = query.get('command', 'find')
        if received_command not in self.mongo_recognised_commands:
            raise NotImplementedError(f'Query command: {received_command} is not supported, '
                                      f'please use one of the following: '
                                      f'{self.mongo_recognised_commands}')
        db_command = getattr(self.connection[query.get('document')], query.get('command'))
        if not isinstance(query.get('data'), tuple):
            LOG.debug('Received wrong param type for query data, using default conversion to tuple')
            query['data'] = (query.get('data', {}),)
        query_output = db_command(*query.get('data'), *args, **kwargs)
        if received_command == 'find' and query.get('sort', None):
            query_output = query_output.sort(query['sort'])
        return query_output
