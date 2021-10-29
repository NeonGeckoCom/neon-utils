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
from datetime import datetime

import pendulum
from dateutil.tz import tzlocal, gettz

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from neon_utils.logger import LOG


def get_coordinates(gps_loc: dict) -> (float, float):
    """
    Gets the latitude and longitude for the passed location
    :param gps_loc: dict of "city", "state", "country"
    :return: lat, lng float values
    """
    coordinates = Nominatim(user_agent="neon-ai")
    try:
        location = coordinates.geocode(gps_loc)
        LOG.debug(f"{location}")
        return location.latitude, location.longitude
    except Exception as x:
        LOG.error(x)
        return -1, -1


def get_location(lat, lng) -> (str, str, str, str):
    """
    Gets location name values for the passed coordinates.
    Note that some coordinates do not have a city, but may have a county.
    :param lat: latitude
    :param lng: longitude
    :return: city, county, state, country
    """
    address = Nominatim(user_agent="neon-ai")
    location = address.reverse([lat, lng], language="en-US")
    LOG.debug(f"{location}")
    LOG.debug(f"{location.raw}")
    LOG.debug(f"{location.raw.get('address')}")
    city = location.raw.get('address').get('city') or location.raw.get('address').get('town')
    county = location.raw.get('address').get('county')
    state = location.raw.get('address').get('state')
    country = location.raw.get('address').get('country')
    return city, county, state, country


def get_timezone(lat, lng) -> (str, float):
    """
    Gets timezone information for the passed coordinates.
    Note that some coordinates do not have a city, but may have a county.
    :param lat: latitude
    :param lng: longitude
    :return: timezone name, offset from GMT
    """
    timezone = TimezoneFinder().timezone_at(lng=float(lng), lat=float(lat))
    offset = pendulum.from_timestamp(0, timezone).offset_hours
    return timezone, offset


def to_system_time(dt: datetime) -> datetime:
    """
    Converts a timezone aware or timezone naiive datetime object to a datetime object in the system tz
    :param dt: datetime object to convert
    :return: timezone aware datetime object that can be scheduled
    """
    tz = tzlocal()
    if dt.tzinfo:
        return dt.astimezone(tz)
    else:
        return dt.replace(tzinfo=tz).astimezone(tz)
