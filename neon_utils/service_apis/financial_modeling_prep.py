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
