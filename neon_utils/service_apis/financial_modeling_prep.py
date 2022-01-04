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

import json
import urllib.parse
import requests_cache as requests

from neon_utils.logger import LOG
from requests.adapters import HTTPAdapter
from . import AUTH_CONFIG, NeonAPI, request_neon_api

SESSION = requests.CachedSession(backend='memory', cache_name="financial_modeling_prep")
SESSION.mount('http://', HTTPAdapter(max_retries=8))
SESSION.mount('https://', HTTPAdapter(max_retries=8))


def search_stock_by_name(company: str, **kwargs) -> list:
    """
    Queries FMP for stocks matching the specified company
    :param company: Company name/stock search term
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
      'exchange' - optional preferred exchange (default None)
    :return: list of dict matched stock data (`name`, `symbol`)
    """
    api_key = kwargs.get("api_key", AUTH_CONFIG.get("financial_modeling_prep", {}).get("api_key"))

    if api_key:
        query_params = {"query": company,
                        "limit": 10,
                        "apikey": api_key}
        if kwargs.get("exchange"):
            query_params["exchange"] = kwargs.get("exchange")
        resp = query_fmp_api(f"https://financialmodelingprep.com/api/v3/search?{urllib.parse.urlencode(query_params)}")
    else:
        query_params = {**kwargs, **{"api": "symbol"}}
        resp = request_neon_api(NeonAPI.FINANCIAL_MODELING_PREP, query_params)

    data = json.loads(resp["content"])
    return data


def get_stock_quote(symbol: str, **kwargs) -> dict:
    """
    Queries FMP for stock information for the specified company
    :param symbol: Stock ticker symbol
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
    :return: dict stock data
    """
    api_key = kwargs.get("api_key", AUTH_CONFIG.get("financial_modeling_prep", {}).get("api_key"))

    if api_key:
        query_params = {"apikey": api_key}
        resp = query_fmp_api(f"https://financialmodelingprep.com/api/v3/company/profile/{symbol}?"
                             f"{urllib.parse.urlencode(query_params)}")
    else:
        query_params = {**kwargs, **{"api": "quote"}}
        resp = request_neon_api(NeonAPI.FINANCIAL_MODELING_PREP, query_params)

    data = json.loads(resp["content"])
    if data.get("Information"):
        LOG.warning(data.get("Information"))
        # TODO: Handle API Errors DM

    return data.get("profile")


def query_fmp_api(url: str) -> dict:
    """
    Query the FMP API and return the result
    :param url: Alpha Vantage API URL to query
    :return: dict status_code, content, encoding
    """
    if "/company/profile" in url.lower():
        expiration = 5*60  # Cache quotes for 5 minutes
    elif "/search" in url.lower():
        expiration = None
    else:
        LOG.warning(f"Unknown URL request; caching for 15 minutes: {url}")
        expiration = 15*60
    result = SESSION.get(url, expire_after=expiration)

    return {"status_code": result.status_code,
            "content": result.content,
            "encoding": result.encoding,
            "cached": result.from_cache}
