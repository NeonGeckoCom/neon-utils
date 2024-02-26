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

import requests
import json

from os import makedirs
from os.path import join, isfile, isdir, dirname
from time import time
from ovos_utils.log import LOG
from ovos_utils.xdg_utils import xdg_cache_home

_DEFAULT_BACKEND_URL = "https://hana.neonaiservices.com"
_client_config = {}
_headers = {}


def _get_client_config_path(url: str = _DEFAULT_BACKEND_URL):
    url_key = hash(url)
    return join(xdg_cache_home(), "neon", f"hana_token_{url_key}.json")


class ServerException(Exception):
    """Exception class representing a backend server communication error"""


def _init_client(backend_address: str):
    """
    Initialize request headers for making backend requests. If a local cache is
    available it will be used, otherwise an auth request will be made to the
    specified backend server
    @param backend_address: Hana server URL to connect to
    """
    global _client_config
    global _headers

    if not _client_config:
        client_config_path = _get_client_config_path(backend_address)
        if isfile(client_config_path):
            with open(client_config_path) as f:
                _client_config = json.load(f)
        else:
            _get_token(backend_address)

    if not _headers:
        _headers = {"Authorization": f"Bearer {_client_config['access_token']}"}


def _get_token(backend_address: str, username: str = "guest",
               password: str = "password"):
    """
    Get new auth tokens from the specified server. This will cache the returned
    token, overwriting any previous data at the cache path.
    @param backend_address: Hana server URL to connect to
    @param username: Username to authorize
    @param password: Password for specified username
    """
    global _client_config
    # TODO: username/password from configuration
    resp = requests.post(f"{backend_address}/auth/login",
                         json={"username": username,
                               "password": password})
    if not resp.ok:
        raise ServerException(f"Error logging into {backend_address}. "
                              f"{resp.status_code}: {resp.text}")
    _client_config = resp.json()
    client_config_path = _get_client_config_path(backend_address)
    if not isdir(dirname(client_config_path)):
        makedirs(dirname(client_config_path))
    with open(client_config_path, "w+") as f:
        json.dump(_client_config, f, indent=2)


def _refresh_token(backend_address: str):
    """
    Get new tokens from the specified server using an existing refresh token
    (if it exists). This will update the cached tokens and associated metadata.
    @param backend_address: Hana server URL to connect to
    """
    global _client_config
    _init_client(backend_address)
    update = requests.post(f"{backend_address}/auth/refresh", json={
        "access_token": _client_config.get("access_token"),
        "refresh_token": _client_config.get("refresh_token"),
        "client_id": _client_config.get("client_id")})
    if not update.ok:
        raise ServerException(f"Error updating token from {backend_address}. "
                              f"{update.status_code}: {update.text}")
    _client_config = update.json()
    client_config_path = _get_client_config_path(backend_address)
    with open(client_config_path, "w+") as f:
        json.dump(_client_config, f, indent=2)


def request_backend(endpoint: str, request_data: dict,
                    server_url: str = _DEFAULT_BACKEND_URL) -> dict:
    """
    Make a request to a Hana backend server and return the json response
    @param endpoint: server endpoint to query
    @param request_data: dict data to send in request body
    @param server_url: Base URL of Hana server to query
    @returns: dict response
    """
    _init_client(server_url)
    if time() >= _client_config.get("expiration", 0):
        try:
            _refresh_token(server_url)
        except ServerException as e:
            LOG.error(e)
            _get_token(server_url)
    resp = requests.post(f"{server_url}/{endpoint.lstrip('/')}",
                         json=request_data, headers=_headers)
    if resp.ok:
        return resp.json()
    else:
        raise ServerException(f"Error response {resp.status_code}: {resp.text}")
