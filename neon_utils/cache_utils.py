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
import time
from collections import OrderedDict


class LRUCache:
    # TODO user specific cache with a compound key
    def __init__(self, capacity: int = 128):
        self.cache = OrderedDict()
        self._capacity = capacity
        self._hits = 0
        self._missed = 0
        self._init_time = time.time()

    def __len__(self):
        return len(self.cache)

    @property
    def hits(self):
        return self._hits

    @property
    def missed(self):
        return self._missed

    def get(self, key):
        """
        Return the value of the key from cache.
        Increment self._missed in key not in cache, increment self._hits in key in cache
        Args:
            key: a key to look up in cache
        Returns: value associated with the key or None

        """
        if key not in self.cache:
            self._missed += 1
            return None
        else:
            self._hits += 1
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key, value) -> None:
        """
        Put a key-value pair into cache
        Args:
            key: a key to put into cache
            value: a value to put into cache
        Returns:
        """
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self._capacity:
            self.cache.popitem(last=False)

    def clear(self):
        """
        Clear the cache dict
        """
        self.cache = OrderedDict()

    def clear_full(self):
        """
        Clear the cache dict, reset hits, missed and initialization time
        Returns:

        """
        self.clear()
        self._hits = self._missed = 0
        self._init_time = time.time()

    def jsonify(self):
        """
        Dump cache dict into json
        Returns: json-string
        """
        return json.dumps(self.cache)

    def jsonify_metrics(self):
        """
        Dump cache metrics into json
        Returns:

        """
        data = dict()
        data["cache"] = self.cache
        data["hits"] = self.hits
        data["missed"] = self.missed
        data["size"] = self._capacity
        return json.dumps(data)
