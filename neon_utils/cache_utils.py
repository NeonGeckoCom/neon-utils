import json
import time
from collections import OrderedDict


class LRUCache:
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
