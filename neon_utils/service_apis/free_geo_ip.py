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
from ipaddress import ip_address
from requests.adapters import HTTPAdapter
from . import AUTH_CONFIG, NeonAPI, request_neon_api

SESSION = requests.CachedSession(backend='memory', cache_name="free_geo_ip")
SESSION.mount('http://', HTTPAdapter(max_retries=8))
SESSION.mount('https://', HTTPAdapter(max_retries=8))


def get_location_for_address(ip_addr: str, **kwargs) -> dict:
    """
    Queries Alpha Vantage for stocks matching the specified company
    :param ip_addr: Public IP Address to geolocate
    :param kwargs:
      'api_key' - optional str api_key to use for query (None to force remote lookup)
    :return: dict location data
    """

    if ip_address(ip_addr).is_private:
        raise ValueError(f"Requested IP Address is private: {ip_addr}")

    api_key = kwargs.get("api_key", AUTH_CONFIG.get("free_geo_ip", {}).get("api_key"))
    if api_key:
        query_params = {"apikey": api_key}
        resp = query_free_geo_ip_api(f"https://api.freegeoip.app/json/{ip_addr}?{urllib.parse.urlencode(query_params)}")
    else:
        resp = request_neon_api(NeonAPI.FREE_GEO_IP, {"ip_addr": ip_addr})

    geolocation_data = json.loads(resp["content"])
    LOG.debug(geolocation_data)
    return geolocation_data


def query_free_geo_ip_api(url: str) -> dict:
    """
    Query the FreeGeoIp API and return the result
    :param url: Alpha Vantage API URL to query
    :return: dict status_code, content, encoding
    """
    expiration = 60*60*24  # Cache quotes for 1 day
    result = SESSION.get(url, expire_after=expiration)

    return {"status_code": result.status_code,
            "content": result.content,
            "encoding": result.encoding,
            "cached": result.from_cache}
