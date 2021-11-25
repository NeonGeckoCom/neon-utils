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
from enum import Enum
from json import JSONDecodeError
from typing import Union

import requests_cache as requests

from neon_utils.logger import LOG
from requests.adapters import HTTPAdapter
from . import AUTH_CONFIG, NeonAPI, request_neon_api

SESSION = requests.CachedSession(backend='memory', cache_name="open_weather_map", allowable_codes=(200, 400),
                                 expire_after=3*60)
SESSION.mount('http://', HTTPAdapter(max_retries=8))
SESSION.mount('https://', HTTPAdapter(max_retries=8))

BASE_URL = "http://api.openweathermap.org/data/2.5"


class OpenWeatherMapApi(Enum):
    def __repr__(self):
        return self.value
    CURRENT = "weather"
    ONECALL = "onecall"


def get_current_weather(lat: Union[str, float], lng: Union[str, float], units: str = "metric", **kwargs) -> dict:
    """
    Queries Open Weather Map for current weather at the specified location
    :param lat: latitude
    :param lng: longitude
    :param units: Temperature and Speed units "metric", "imperial", or "standard"
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
      'language' - optional language param (default english)
    :return: dict weather data (https://openweathermap.org/current#current_JSON)
    """
    forecast = _make_api_call(lat, lng, units, OpenWeatherMapApi.CURRENT, **kwargs)
    if not forecast.get("weather"):
        LOG.warning("Outdated backend API return. Reformatting into current")
        forecast = {"main": forecast["current"],
                    "weather": forecast["current"]["weather"]}
    return forecast


def get_forecast(lat: Union[str, float], lng: Union[str, float], units: str = "metric", **kwargs) -> dict:
    """
    Queries Open Weather Map for weather data at the specified location
    :param lat: latitude
    :param lng: longitude
    :param units: Temperature and Speed units "metric", "imperial", or "standard"
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
      'language' - optional language param (default english)
    :return: dict weather data (https://openweathermap.org/api/one-call-api#hist_example)
    """
    return _make_api_call(lat, lng, units, OpenWeatherMapApi.ONECALL, **kwargs)


def _make_api_call(lat: Union[str, float], lng: Union[str, float], units: str, target_api: OpenWeatherMapApi, **kwargs) -> dict:
    """
    Common wrapper for API calls to OWM
    :param lat: latitude
    :param lng: longitude
    :param units: Temperature and Speed units "metric", "imperial", or "standard"
    :param target_api: API to query
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
      'language' - optional language param (default english)
    :return: dict weather data
    """
    api_key = kwargs.get("api_key", AUTH_CONFIG.get("owm", {}).get("api_key"))

    if api_key:
        query_params = {"lat": lat, "lon": lng, "units": units, "appid": api_key}

        resp = query_owm_api(f"{BASE_URL}/{repr(target_api)}?{urllib.parse.urlencode(query_params)}")
    else:
        query_params = {"lat": lat, "lng": lng, "units": units, "api": repr(target_api)}
        resp = request_neon_api(NeonAPI.OPEN_WEATHER_MAP, query_params)

    try:
        data = json.loads(resp["content"])
    except JSONDecodeError:
        data = {"error": "Error decoding response",
                "response": resp}
    if data.get('cod'):
        data['cod'] = str(data['cod'])
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
