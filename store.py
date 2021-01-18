import redis
import logging
import time

MAX_ATTEMPTS = 5


class Store:
    def __init__(self):
        self.client = redis.Redis()

    def set(self, key, value):
        n = 0
        while n <= MAX_ATTEMPTS:
            try:
                self.client.set(key, value)
            except Exception as e:
                logging.info("Cannot connect to Redis at %s attempt: %s ..." % (n, e))
                n += 1
                time.sleep(1)
        raise redis.exceptions.ConnectionError

    def get(self, key: str):
        n = 0
        while n <= MAX_ATTEMPTS:
            try:
                resp = self.client.get(key)
            except Exception as e:
                logging.info("Cannot connect to Redis at %s attempt: %s ..." % (n, e))
                n += 1
                time.sleep(1)
            else:
                if resp:
                    return resp.decode("utf-8")
                return None
        raise redis.exceptions.ConnectionError

    def cache_set(self, key: str, value, seconds_to_expire):
        """ Implemented as an example; it goes to the same key-value storage """
        self.client.setex(key, seconds_to_expire, value)

    def cache_get(self, key: str):
        """ Implemented as an example; it goes to the same key-value storage """
        return self.get(key)