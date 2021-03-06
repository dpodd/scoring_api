import unittest

import fakeredis
import redis

from store import Store


class StoreConnectedTestCase(unittest.TestCase):
    """ Tests should pass when our key-value storage (and cache) are running  and available """
    def setUp(self):
        self.store = Store()
        self.keys_for_cleanup = []

    def tearDown(self):
        self.clean_storage()

    def clean_storage(self):
        for key in self.keys_for_cleanup:
            self.store.delete(key)

    def test_store_connected(self):
        self.assertEqual(self.store.ping(), True)

    def test_store_set_value(self):
        t = ("test_key", "test_value")
        self.keys_for_cleanup.append(t[0])
        self.assertEqual(self.store.set(*t), True)

    def test_store_get_value(self):
        t = ("test_key", "test_value")
        self.keys_for_cleanup.append(t[0])
        self.assertEqual(self.store.set(*t), True)
        self.assertEqual(self.store.get(t[0]).decode(), t[1])

    def test_store_set_cache(self):
        t = ("test_key", "test_value")
        self.keys_for_cleanup.append(t[0])
        self.assertEqual(self.store.cache_set(*t, 60*10), True)

    def test_store_get_cache(self):
        t = ("test_key", "test_value")
        self.keys_for_cleanup.append(t[0])
        self.assertEqual(self.store.cache_set(*t, 60*10), True)
        self.assertEqual(self.store.cache_get(t[0]).decode(), t[1])


class StoreDisconnectedTestCase(unittest.TestCase):
    """ Tests should pass when our key-value storage (and cache) are not available """
    def setUp(self):
        self.store = Store()
        # emulate dysfunctional storage:
        server = fakeredis.FakeServer()
        server.connected = False
        self.store.client = fakeredis.FakeStrictRedis(server=server)

    def test_our_mock_redis(self):
        self.assertRaises(redis.exceptions.ConnectionError, self.store.ping)

    def test_store_set_value(self):
        t = ("test_key", "test_value")
        self.assertRaises(redis.exceptions.ConnectionError, self.store.set, *t)

    def test_store_get_value(self):
        t = ("test_key", "test_value")
        self.assertRaises(redis.exceptions.ConnectionError, self.store.get, t[0])

    def test_store_set_cache_value(self):
        t = ("test_key", "test_value")
        self.assertRaises(redis.exceptions.ConnectionError, self.store.cache_set, *t, 60)

    def test_store_get_cache_value(self):
        """ Cache returns None when storage is disconnected"""
        t = ("test_key", "test_value")
        self.assertEqual(self.store.cache_get(t[0]), None)


if __name__ == '__main___':
    unittest.main()
