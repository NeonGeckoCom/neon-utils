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

import urllib.parse
import requests_cache as requests

from requests.adapters import HTTPAdapter
from enum import Enum
from typing import Union
from neon_utils.net_utils import get_ip_address
from neon_utils.log_utils import LOG
from . import AUTH_CONFIG, NeonAPI, request_neon_api

SESSION = requests.CachedSession(backend='memory', cache_name="wolfram_alpha", allowable_codes=(200, 501),
                                 expire_after=15*60)
SESSION.mount('http://', HTTPAdapter(max_retries=8))
SESSION.mount('https://', HTTPAdapter(max_retries=8))


class QueryApi(Enum):
    def __repr__(self):
        return self.value
    SIMPLE = "simple"
    SHORT = "short"
    SPOKEN = "spoken"
    FULL = "full"
    RECOGNIZE = "recognize"
    CONVERSATION = "conversation"


def get_wolfram_alpha_response(query: str, api: QueryApi, units: str = "metric", **kwargs) -> Union[str, bytes]:
    """
    Queries Wolfram|Alpha for a response from the specified API with the specified parameters
    :param query: Question to submit to Wolfram|Alpha
    :param api: API to target
    :param units: "metric" or "nonmetric" units
    :param kwargs:
      'lat' - optional str latitude
      'lng' - optional str longitude
      'ip' - optional str public IP for geolocation
      'app_id' - optional str app_id to use for query (None to force remote lookup)
    :return: str text response or bytes response for 'full'
    """
    query_params = get_geolocation_params(**kwargs)
    query_params["units"] = units
    api_key = kwargs.get("app_id", AUTH_CONFIG.get("wolfram", {}).get("app_id"))
    if api_key:
        query_params["appid"] = api_key
        query_params["i"] = query
        resp = query_wolfram_alpha_api(f"{api_to_url(api)}?{urllib.parse.urlencode(query_params)}")
    else:
        query_params["query"] = query
        query_params["api"] = repr(api)
        resp = request_neon_api(NeonAPI.WOLFRAM_ALPHA, query_params)

    if resp["status_code"] != 200:
        LOG.error(f"Non-success response: {resp}")  # TODO: Handle failures
        if resp["status_code"] == 403:
            LOG.error(f"Invalid credential provided.")
    if resp.get("encoding"):
        return resp["content"].decode(resp["encoding"])
    else:
        return resp["content"]


def api_to_url(api: QueryApi) -> str:
    """
    Translates a wolfram API to a URL
    :param api: QueryApi to call
    :return: base URL
    """
    if not api:
        raise ValueError("api is null")
    if not isinstance(api, QueryApi):
        raise TypeError(f"Not a QueryApi: {api}")
    url_map = {QueryApi.SIMPLE: "http://api.wolframalpha.com/v2/simple",
               QueryApi.SHORT: "http://api.wolframalpha.com/v2/result",
               QueryApi.SPOKEN: "http://api.wolframalpha.com/v2/spoken",
               QueryApi.FULL: "http://api.wolframalpha.com/v2/query",
               QueryApi.RECOGNIZE: "http://www.wolframalpha.com/queryrecognizer/query.jsp",
               QueryApi.CONVERSATION: "http://api.wolframalpha.com/v1/conversation.jsp"}
    return url_map[api]


def query_wolfram_alpha_api(url: str) -> dict:
    """
    Query the Wolfram|Alpha API and return the result
    :param url: Wolfram|Alpha API URL to query
    :return: dict status_code, content, encoding
    """
    result = SESSION.get(url)

    return {"status_code": result.status_code,
            "content": result.content,
            "encoding": result.encoding,
            "cached": result.from_cache}


def get_geolocation_params(**kwargs) -> dict:
    """
    Returns a valid dict of data for geolocation (lat/lng or ip)
    :param kwargs:
      'lat' - optional str latitude
      'lng' - optional str longitude
      'ip' - optional str public IP for geolocation
    :return: dict with latlong or ip
    """
    if kwargs.get("lat") and kwargs.get("lng"):
        return {"latlong": f'{kwargs.get("lat")},{kwargs.get("lng")}'}
    elif kwargs.get("ip"):
        return {"ip": kwargs.get("ip")}
    else:
        return {"ip": get_ip_address()}
