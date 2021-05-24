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

import os
import sys
import random
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.cache_utils import *


class CacheUtilTests(unittest.TestCase):

    def setUp(self) -> None:
        self.lru_cache = LRUCache()

    def test_put(self):
        max_size = self.lru_cache._capacity

        self.lru_cache.put("1", 1)
        self.assertEqual(len(self.lru_cache), 1)

        for i in range(2, max_size+2):
            self.lru_cache.put(str(i), i)
        self.assertEqual(len(self.lru_cache), max_size)
        self.assertNotIn("1", self.lru_cache.cache)

        random_i = random.randint(0, max_size)
        self.lru_cache.put(str(random_i), random_i)
        self.assertEqual(random_i, self.lru_cache.cache.popitem()[1])

    def test_get(self):
        hits = self.lru_cache.hits
        missed = self.lru_cache.missed
        key = random.randint(0, self.lru_cache._capacity)
        str_key = "a"

        for i in range(self.lru_cache._capacity):
            self.lru_cache.put(str(i), i)
        result = self.lru_cache.get(str(key))
        self.assertTrue(result)
        self.assertEqual(result, key)
        self.assertEqual(self.lru_cache.hits, hits + 1)
        self.assertEqual(self.lru_cache.cache.popitem()[1], key)

        result = self.lru_cache.get(str_key)
        self.assertFalse(result)
        self.assertEqual(self.lru_cache.missed, missed + 1)

    def test_clear(self):
        for i in range(self.lru_cache._capacity):
            self.lru_cache.put(str(i), i)

        self.lru_cache.clear()
        self.assertEqual(len(self.lru_cache), 0)

    def test_clear_full(self):
        for i in range(self.lru_cache._capacity):
            self.lru_cache.put(str(i), i)
        self.lru_cache._missed = self.lru_cache._hits = 10
        init_time = self.lru_cache._init_time

        self.lru_cache.clear_full()

        self.assertEqual(len(self.lru_cache), 0)
        self.assertEqual(self.lru_cache.hits, 0)
        self.assertEqual(self.lru_cache.missed, 0)
        self.assertNotEqual(init_time, self.lru_cache._init_time)

    def test_jsonify(self):
        for i in range(self.lru_cache._capacity):
            self.lru_cache.put(str(i), i)

        with self.assertRaises(TypeError):
            json.dumps(self.lru_cache)

        j = self.lru_cache.jsonify()
        self.assertIsInstance(j, str)

    def jsonify_metrics(self):
        j = self.lru_cache.jsonify_metrics()
        self.assertIsInstance(j, str)


if __name__ == '__main__':
    unittest.main()
