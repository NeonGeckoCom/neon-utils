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


import os
import unittest

from neon_utils import LOG
from neon_utils.database_utils.config import KlatDBConfig
from neon_utils.ssh_utils import create_tunnel


class TestDBController(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # '~/.local/share/neon/credentials.json'
        db_config_file_path = os.environ.get('DATABASE_CONFIG', 'config.json')
        ssh_config_file_path = os.environ.get('SSH_CONFIG', 'config.json')

        cls.configuration = KlatDBConfig(from_files=[db_config_file_path, ssh_config_file_path])

    def test_simple_interaction_mysql(self):
        ssh_configs = self.configuration.config_data.get('SSH_CONFIG', None)
        override_configs = dict()
        if ssh_configs:
            tunnel_connection = create_tunnel(server_address=ssh_configs['ADDRESS'],
                                              username=ssh_configs['USER'],
                                              password=ssh_configs['PASSWORD'],
                                              remote_bind_address=('127.0.0.1', 3306))
            override_configs = {'host': '127.0.0.1',
                                'port': tunnel_connection.local_bind_address[1]}
        self.db_controller = self.configuration.get_db_controller(name='klatchat_2222',
                                                                  override_args=override_configs)

        simple_query = """SELECT name, created, last_updated_cid,value from shoutbox_cache;"""
        result = self.db_controller.exec_query(query=simple_query)
        self.assertIsNotNone(result)

    def test_simple_interaction_mongo(self):
        self.db_controller = self.configuration.get_db_controller(name='pyklatchat_3333')
        self.assertIsNotNone(self.db_controller)
        test_data = {"name": "John", "address": "Highway 37"}
        self.db_controller.exec_query(query={'command': 'insert_one',
                                             'document': 'test',
                                             'data': test_data})
        inserted_data = self.db_controller.exec_query(query={'command': 'find_one',
                                                             'document': 'test',
                                                             'data': test_data})
        LOG.debug(f'Received inserted data: {inserted_data}')
        self.assertIsNotNone(inserted_data)
        self.assertIsInstance(inserted_data, dict)
        self.db_controller.exec_query(query={'command': 'delete_many',
                                             'document': 'test',
                                             'data': test_data})
