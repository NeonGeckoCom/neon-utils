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
from json import JSONDecodeError

import requests_cache as requests

from neon_utils.logger import LOG
from requests.adapters import HTTPAdapter
from . import AUTH_CONFIG, NeonAPI, request_neon_api

SESSION = requests.CachedSession(backend='memory', cache_name="alpha_vantage")
SESSION.mount('http://', HTTPAdapter(max_retries=8))
SESSION.mount('https://', HTTPAdapter(max_retries=8))


def search_stock_by_name(company: str, **kwargs) -> list:
    """
    Queries Alpha Vantage for stocks matching the specified company
    :param company: Company name/stock search term
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
      'region' - optional preferred region (default `United States`)
    :return: list of dict matched stock data
    """
    api_key = kwargs.get("api_key", AUTH_CONFIG.get("alpha_vantage", {}).get("api_key"))
    region = kwargs.get("region") or "United States"

    if api_key:
        query_params = {"function": "SYMBOL_SEARCH",
                        "keywords": company,
                        "apikey": api_key}
        resp = query_alpha_vantage_api(f"https://www.alphavantage.co/query?{urllib.parse.urlencode(query_params)}")
    else:
        query_params = {**kwargs, **{"api": "symbol", "company": company}}
        resp = request_neon_api(NeonAPI.ALPHA_VANTAGE, query_params)

    if resp["status_code"] == -1:
        data = {"error": resp["content"]}
    else:
        try:
            data = json.loads(resp["content"])
        except JSONDecodeError:
            data = {"error": "Error decoding response",
                    "response": resp}
    if data.get("Information"):
        LOG.warning(data.get("Information"))
        # TODO: Handle API Errors DM
    if not data.get("bestMatches"):
        LOG.warning(f"No matches found for {company}")
        return []
    filtered_data = [stock for stock in data.get("bestMatches") if stock.get("4. region") == region]
    if not filtered_data:
        filtered_data = data.get("bestMatches")
    data = [{"symbol": stock.get("1. symbol"),
             "name": stock.get("2. name"),
             "region": stock.get("4. region"),
             "currency": stock.get("8. currency")} for stock in filtered_data]
    return data


def get_stock_quote(symbol: str, **kwargs) -> dict:
    """
    Queries Alpha Vantage for stock information for the specified company
    :param symbol: Stock ticker symbol
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
    :return: dict stock data
    """
    api_key = kwargs.get("api_key", AUTH_CONFIG.get("alpha_vantage", {}).get("api_key"))

    if api_key:
        query_params = {"function": "GLOBAL_QUOTE",
                        "symbol": symbol,
                        "apikey": api_key}
        resp = query_alpha_vantage_api(f"https://www.alphavantage.co/query?{urllib.parse.urlencode(query_params)}")
    else:
        query_params = {**kwargs, **{"api": "quote", "symbol": symbol}}
        resp = request_neon_api(NeonAPI.ALPHA_VANTAGE, query_params)

    if resp["status_code"] == -1:
        data = {"error": resp["content"]}
    else:
        try:
            data = json.loads(resp["content"])
        except JSONDecodeError:
            data = {"error": "Error decoding response",
                    "response": resp}
    if data.get("Information"):
        LOG.warning(data.get("Information"))
        # TODO: Handle API Errors DM

    if not data.get("Global Quote"):
        LOG.warning(f"No data found for {symbol}")
        data["error"] = data.get("error") or "No data found"
        LOG.error(data)
        return data
    return {"symbol": data.get("Global Quote")["01. symbol"],
            "price": data.get("Global Quote")["05. price"],
            "close": data.get("Global Quote")["08. previous close"]}


def query_alpha_vantage_api(url: str) -> dict:
    """
    Query the Alpha Vantage API and return the result
    :param url: Alpha Vantage API URL to query
    :return: dict status_code, content, encoding
    """
    if "global_quote" in url.lower():
        expiration = 5*60  # Cache quotes for 5 minutes
    elif "symbol_search" in url.lower():
        expiration = None
    else:
        LOG.warning(f"Unknown URL request; caching for 15 minutes: {url}")
        expiration = 15*60
    result = SESSION.get(url, expire_after=expiration)

    return {"status_code": result.status_code,
            "content": result.content,
            "encoding": result.encoding,
            "cached": result.from_cache}
