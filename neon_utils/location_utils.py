# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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
from time import time

import pytz

from datetime import datetime
from typing import Optional, Union

from dateutil.tz import tzlocal
from timezonefinder import TimezoneFinder
from re import sub
from ovos_utils.log import LOG

from neon_utils.hana_utils import request_backend

# geocode.maps.co nominatim.openstreetmap.org
_NOMINATIM_DOMAIN = "nominatim.openstreetmap.org"


def set_nominatim_domain(domain: str):
    """
    Configure the Nominatim domain to use for location requests
    :param domain: Nominatim domain to use for location lookups
    """
    global _NOMINATIM_DOMAIN
    if domain.startswith("http"):
        domain = domain.split('/')[2]
    _NOMINATIM_DOMAIN = domain


def get_full_location(address: Union[str, tuple],
                      lang: Optional[str] = None) -> Optional[dict]:
    """
    Get full location details for the specified address in the specified lang
    :param address: string address or tuple (latitude, longitude)
    :param lang: optional language to format results (else system default)
    :returns: dict containing at minimum `place_id`, `lat`, `lon`, `address`
        None if service is not available
    """
    try:
        if isinstance(address, str):
            response = request_backend("proxy/geolocation/geocode",
                                       {"address": address})
            coords = (response.get('lat'), response.get('lon'))
        else:
            coords = address

        dict_location = request_backend("proxy/geolocation/reverse",
                                        {"lat": coords[0], "lon": coords[1]})
        dict_location['address']['country'] = sub(f'[0-9]', '',
                                                  dict_location['address'].
                                                  get('country'))
        if lang:
            try:
                # TODO: make this optional with a deprecation notice
                from geopy.geocoders import Nominatim
                resp = Nominatim(user_agent="neon-ai", domain=_NOMINATIM_DOMAIN,
                                 timeout=10).reverse(coords, language=lang)
                return resp.raw
            except ImportError:
                LOG.error("geopy not installed")
            except Exception as e:
                LOG.exception(e)
        return dict_location
    except Exception as e:
        LOG.exception(e)
    return None


def get_coordinates(gps_loc: dict) -> (float, float):
    """
    Gets the latitude and longitude for the passed location
    :param gps_loc: dict of "city", "state", "country"
    :return: lat, lng float values
    """
    try:
        request_str = ', '.join((x for x in [gps_loc.get('city'),
                                             gps_loc.get('state'),
                                             gps_loc.get('country')] if x))
        location = request_backend("proxy/geolocation/geocode",
                                   {"address": request_str})
        LOG.debug(f"{location}")
        return float(location.get('lat')), float(location.get('lon'))
    except Exception as x:
        LOG.exception(x)
    return -1, -1


def get_location(lat, lng) -> (str, str, str, str):
    """
    Gets location name values for the passed coordinates.
    Note that some coordinates do not have a city, but may have a county.
    :param lat: latitude
    :param lng: longitude
    :return: city, county, state, country
    """
    try:
        location = request_backend("proxy/geolocation/reverse",
                                   {"lat": lat, "lon": lng})

        dict_location = location.get('address')
    except Exception as x:
        LOG.exception(x)
        return None
    LOG.debug(f"{location}")
    city = dict_location.get('city') or \
        dict_location.get('town') or \
        dict_location.get('village') or \
        dict_location.get('hamlet')
    county = dict_location.get('county')
    state = dict_location.get('state')
    country = dict_location.get('country')
    return city, county, state, country


def get_timezone(lat, lng) -> (str, float):
    """
    Gets timezone information for the passed coordinates.
    Note that some coordinates do not have a city, but may have a county.
    :param lat: latitude
    :param lng: longitude
    :return: timezone name, offset in hours from UTC
    """
    timezone = TimezoneFinder().timezone_at(lng=float(lng), lat=float(lat))
    offset = pytz.timezone(timezone).utcoffset(
        datetime.now()).total_seconds() / 3600
    return timezone, offset


def to_system_time(dt: datetime) -> datetime:
    """
    Converts a timezone aware or timezone naiive datetime object to a datetime
    object in the system tz
    :param dt: datetime object to convert
    :return: timezone aware datetime object that can be scheduled
    """
    tz = tzlocal()
    if dt.tzinfo:
        return dt.astimezone(tz)
    else:
        return dt.replace(tzinfo=tz).astimezone(tz)
