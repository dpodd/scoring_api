import redis
import logging
import time

MAX_ATTEMPTS = 5


class Store:
    def __init__(self):
        self.client = redis.Redis()

    def ping(self):
        return self.client.ping()

    def set(self, key, value):
        n = 0
        while n <= MAX_ATTEMPTS:
            try:
                self.client.set(key, value)
            except Exception as e:
                logging.info("Cannot connect to Redis: %s ..." % e)
                n += 1
                time.sleep(1)
        raise redis.exceptions.ConnectionError

    def get(self, key: str):
        n = 0
        while n <= MAX_ATTEMPS:
            try:
                resp = self.client.get(key)
            except Exception as e:
                logging.info("Cannot connect to Redis: %s ..." % e)
                n += 1
                time.sleep(1)
            else:
                if resp:
                    return resp.decode("utf-8")
        raise redis.exceptions.ConnectionError

    def cache_set(self, key: str, value, seconds_to_expire):
        self.client.setex(key, seconds_to_expire, value)

    def cache_get(self, key: str):
        return self.get(key)