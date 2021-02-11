import unittest

from store import Store


class StoreConnectedTestCase(unittest.TestCase):
    """ Tests should pass when our key-value storage is active """
    def setUp(self):
        self.store = Store()

    def test_store_connected(self):
        self.assertEqual(self.store.ping(), True)


if __name__ == '__main___':
    unittest.main()
