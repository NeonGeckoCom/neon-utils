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

import unittest

from datetime import datetime
from time import sleep

from dateutil.tz import gettz, tzlocal

# Wide enough that Nominatim/HANA centroid drift does not fail CI, tight
# enough that a different metro or state still fails. south, north, west, east.
_SEATTLE_METRO_BOX = (47.0, 48.3, -123.2, -121.4)
_WASHINGTON_BOX = (45.5, 49.1, -125.0, -116.5)

_SEATTLE_NAMES = {"seattle"}
_KING_COUNTY_NAMES = {"king county", "king"}
_WASHINGTON_NAMES = {"washington", "wa"}
_US_COUNTRY_EN = {"united states", "united states of america", "usa"}
_US_COUNTRY_ES = {"estados unidos de américa", "estados unidos",
                  "ee. uu.", "ee.uu.", "eeuu"}


def _normalize_name(value):
    return (value or "").strip().lower()


def _address_locality(address: dict):
    return (address.get('city') or address.get('town') or
            address.get('village') or address.get('hamlet'))


class LocationUtilTests(unittest.TestCase):
    def _assert_in_box(self, lat, lon, box):
        south, north, west, east = box
        lat = float(lat)
        lon = float(lon)
        self.assertGreaterEqual(lat, south)
        self.assertLessEqual(lat, north)
        self.assertGreaterEqual(lon, west)
        self.assertLessEqual(lon, east)

    def _assert_name_in(self, value, names):
        self.assertIn(_normalize_name(value), names)

    def test_get_coordinates_complete(self):
        from neon_utils.location_utils import get_coordinates

        # Complete location
        coords = get_coordinates({"city": "Kirkland", "state": "Washington",
                                  "country": "United States"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)
        self._assert_in_box(*coords, _SEATTLE_METRO_BOX)
        sleep(1)  # maps.co rate-limit

        # No city specified. "Washington State" disambiguates from DC.
        coords = get_coordinates({"state": "Washington State",
                                  "country": "United States"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)
        self._assert_in_box(*coords, _WASHINGTON_BOX)
        sleep(1)  # maps.co rate-limit

        # No state specified
        coords = get_coordinates({"city": "Seattle",
                                  "country": "United States"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)
        self._assert_in_box(*coords, _SEATTLE_METRO_BOX)
        sleep(1)  # maps.co rate-limit

        # No country specified
        coords = get_coordinates({"state": "Washington", "city": "Renton"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)
        self._assert_in_box(*coords, _SEATTLE_METRO_BOX)
        sleep(1)  # maps.co rate-limit

    def test_get_location_from_coords(self):
        from neon_utils.location_utils import get_location
        lat = 47.6038321
        lng = -122.3300624
        location = get_location(lat, lng)
        self.assertEqual(len(location), 4)
        city, county, state, country = location
        self._assert_name_in(city, _SEATTLE_NAMES)
        self._assert_name_in(county, _KING_COUNTY_NAMES)
        self._assert_name_in(state, _WASHINGTON_NAMES)
        self._assert_name_in(country, _US_COUNTRY_EN)

        # Test 'hamlet' location
        location = get_location(34.46433387046654, -81.99487538579375)
        self.assertIsInstance(location[0], str)

    def test_get_timezone_from_coords(self):
        from neon_utils.location_utils import get_timezone
        lat = 47.6038321
        lng = -122.3300624
        timezone, offset = get_timezone(lat, lng)
        self.assertIsInstance(timezone, str)
        self.assertEqual(timezone, "America/Los_Angeles")
        self.assertIsInstance(offset, float)
        self.assertIn(offset, (-7.0, -8.0))

        lat = 35.0000
        lon = 103.000
        timezone, offset = get_timezone(lat, lon)
        self.assertEqual(timezone, "Asia/Shanghai")
        self.assertEqual(offset, 8.0)

    def test_to_system_time(self):
        from neon_utils.location_utils import to_system_time
        tz_aware_dt = datetime.now(gettz("America/NewYork"))
        system_dt = to_system_time(tz_aware_dt)
        self.assertEqual(system_dt.tzinfo, tzlocal())
        self.assertEqual(tz_aware_dt.timestamp(), system_dt.timestamp())

        tz_aware_dt = datetime.now(gettz("America/Los_Angeles"))
        system_dt = to_system_time(tz_aware_dt)
        self.assertEqual(system_dt.tzinfo, tzlocal())
        self.assertEqual(tz_aware_dt.timestamp(), system_dt.timestamp())

        tz_naiive_dt = datetime.now()
        system_dt = to_system_time(tz_naiive_dt)
        self.assertEqual(system_dt.tzinfo, tzlocal())
        self.assertEqual(tz_naiive_dt.timestamp(), system_dt.timestamp())

    def test_get_full_location(self):
        from neon_utils.location_utils import get_full_location
        location_en = get_full_location("Seattle, Washington")
        self.assertIsInstance(location_en, dict)
        self.assertIsInstance(location_en['lat'], str)
        self.assertIsInstance(location_en['lon'], str)
        self.assertIsInstance(location_en['address'], dict)
        self._assert_in_box(location_en['lat'], location_en['lon'],
                            _SEATTLE_METRO_BOX)
        self._assert_name_in(_address_locality(location_en['address']),
                             _SEATTLE_NAMES)
        self._assert_name_in(location_en['address']['state'],
                             _WASHINGTON_NAMES)
        self._assert_name_in(location_en['address']['country'],
                             _US_COUNTRY_EN)
        self.assertEqual(location_en['address']['country_code'], "us")
        sleep(1)  # maps.co rate-limit

        location_es = get_full_location("Seattle, Washington", "es")
        self._assert_in_box(location_es['lat'], location_es['lon'],
                            _SEATTLE_METRO_BOX)
        self._assert_name_in(location_es['address']['country'],
                             _US_COUNTRY_ES)
        self.assertEqual(location_en['address']['country_code'], "us")
        sleep(1)  # maps.co rate-limit

        location_from_coords = get_full_location((location_en['lat'],
                                                  location_en['lon']))
        self._assert_in_box(location_from_coords['lat'],
                            location_from_coords['lon'],
                            _SEATTLE_METRO_BOX)
        self._assert_name_in(_address_locality(location_from_coords['address']),
                             _SEATTLE_NAMES)
        self._assert_name_in(location_from_coords['address']['state'],
                             _WASHINGTON_NAMES)
        self._assert_name_in(location_from_coords['address']['country'],
                             _US_COUNTRY_EN)
        self.assertEqual(location_from_coords['address']['country_code'], "us")

    def test_set_nominatim_domain(self):
        from neon_utils.location_utils import set_nominatim_domain, \
            _NOMINATIM_DOMAIN
        self.assertIsInstance(_NOMINATIM_DOMAIN, str)

        set_nominatim_domain("https://geocode.maps.co")
        from neon_utils.location_utils import _NOMINATIM_DOMAIN
        self.assertEqual(_NOMINATIM_DOMAIN, "geocode.maps.co")

        set_nominatim_domain("nominatim.openstreetmap.org")
        from neon_utils.location_utils import _NOMINATIM_DOMAIN
        self.assertEqual(_NOMINATIM_DOMAIN, "nominatim.openstreetmap.org")


if __name__ == '__main__':
    unittest.main()
