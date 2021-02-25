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

import unittest
import os
from neon_utils.location_utils import *

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class LocationUtilTests(unittest.TestCase):
    def test_get_coordinates_complete(self):
        coords = get_coordinates({"city": "Kirkland", "state": "Washington", "country": "United States"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)

    def test_get_coordinates_no_city(self):
        coords = get_coordinates({"state": "Washington", "country": "United States"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)

    def test_get_coordinates_no_state(self):
        coords = get_coordinates({"city": "Seattle", "country": "United States"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)

    def test_get_coordinates_no_ccountry(self):
        coords = get_coordinates({"state": "Washington", "city": "Renton"})
        self.assertIsInstance(coords[0], float)
        self.assertIsInstance(coords[1], float)

    def test_get_location_from_coords(self):
        lat = 47.6038321
        lng = -122.3300624
        location = get_location(lat, lng)
        self.assertEqual(len(location), 4)
        self.assertEqual(location, ("Seattle", "King County", "Washington", "United States"))

    def test_get_timezone_from_coords(self):
        lat = 47.6038321
        lng = -122.3300624
        timezone, offset = get_timezone(lat, lng)
        self.assertIsInstance(timezone, str)
        self.assertEqual(timezone, "America/Los_Angeles")
        self.assertIsInstance(offset, float)
        self.assertIn(offset, (-7.0, -8.0))


if __name__ == '__main__':
    unittest.main()
