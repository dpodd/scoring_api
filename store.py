import redis


class Store:
    def __init__(self):
        self.client = redis.Redis()

    def ping(self):
        return self.client.ping()

    def set(self, key, value):
        self.client.set(key, value)

    def get(self, key: str):
        resp = self.client.get(key)
        if resp:
            return resp.decode("utf-8")

    def cache_set(self, key: str, value, seconds_to_expire):
        self.client.setex(key, seconds_to_expire, value)

    def cache_get(self, key: str):
        pass