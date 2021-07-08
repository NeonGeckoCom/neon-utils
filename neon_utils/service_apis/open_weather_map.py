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
from typing import Union

import requests_cache as requests

from neon_utils.logger import LOG
from requests.adapters import HTTPAdapter
from . import AUTH_CONFIG, NeonAPI, request_neon_api

SESSION = requests.CachedSession(backend='memory', cache_name="open_weather_map", allowable_codes=(200, 400),
                                 expire_after=3*60)
SESSION.mount('http://', HTTPAdapter(max_retries=8))
SESSION.mount('https://', HTTPAdapter(max_retries=8))


def get_forecast(lat: Union[str, float], lng: Union[str, float], units: str = "metric", **kwargs) -> dict:
    """
    Queries Open Weather Map for weather data at the specified location
    :param lat: latitude
    :param lng: longitude
    :param units: Temperature and Speed units "metric", "imperial", or "standard"
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
      'language' - optional language param (default english)
    :return: dict weather data
    """
    api_key = kwargs.get("api_key", AUTH_CONFIG.get("owm", {}).get("api_key"))

    if api_key:
        query_params = {"lat": lat, "lon": lng, "units": units, "appid": api_key}
        resp = query_owm_api(f"http://api.openweathermap.org/data/2.5/onecall?{urllib.parse.urlencode(query_params)}")
    else:
        query_params = {"lat": lat, "lon": lng, "units": units}
        resp = request_neon_api(NeonAPI.OPEN_WEATHER_MAP, query_params)

    data = json.loads(resp["content"])
    if data.get('cod'):
        data['cod'] = str(data['cod'])  # 400 is str, 401 is int; cast all to str for safe refs
        LOG.error(f"Error return: {data}")
        # TODO: Handle failures
    return data


def query_owm_api(url: str) -> dict:
    """
    Query the Open Weather Map API and return the result
    :param url: Open Weather Map API URL to query
    :return: dict status_code, content, encoding
    """
    result = SESSION.get(url)
    return {"status_code": result.status_code,
            "content": result.content,
            "encoding": result.encoding,
            "cached": result.from_cache}
