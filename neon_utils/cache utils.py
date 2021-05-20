import json
import time
from collections import OrderedDict

TIME_OFFSET = 24*60*60  # seconds in 24 hours


class LRUCache:
    # TODO unit tests!
    # TODO make is a separate module
    # use threading.Event or MycroftSkill.schedule_event to write to disk
    def __init__(self, capacity: int = 128):
        self.cache = OrderedDict()
        self.capacity = capacity
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

    def get(self, key: str) -> str:
        if key not in self.cache:
            self._missed += 1
            return ''
        else:
            self._hits += 1
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: str) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def jsonify(self):
        return json.dumps(self.cache)

    def jsonify_metrics(self):
        data = dict()
        data["cache"] = self.cache
        data["hits"] = self.hits
        data["missed"] = self.missed
        data["size"] = self.capacity
        return json.dumps(data)
