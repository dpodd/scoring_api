import hashlib
import datetime
import unittest
import json

import fakeredis

import api
from store import Store
from tests import cases


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.settings = Store()
        self.ids_for_cleanup = []

    def tearDown(self) -> None:
        self.delete_keys_from_storage()

    def get_response(self, request):
        try:
            response, code, ctx = api.method_handler({"body": request, "headers": self.headers}, self.context,
                                                     self.settings)
            return response, code, ctx
        except Exception:
            code = api.INTERNAL_ERROR
            return {"msg": "Internal error during test request"}, code, {}

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            msg = datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
            request["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()

    def populate_storage_with_test_data(self, cid_list):
        for cid in cid_list:
            key = "i:%s" % cid
            if cid == 1:
                self.settings.client.set(key, json.dumps(['sport', 'books']))
            elif cid == 2:
                self.settings.client.set(key, json.dumps(['music', 'travel']))
            elif cid == 3:
                self.settings.client.set(key, json.dumps(['books']))
            else:
                self.settings.client.set(key, json.dumps(['cars']))
            self.ids_for_cleanup.append(key)

    def delete_keys_from_storage(self):
        for key in self.ids_for_cleanup:
            self.settings.client.delete(key)

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        """ Test passes even if cache is down """
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"first_name": "a", "last_name": "b"},
    ])
    def test_cache_is_populated_after_score_request(self, arguments):
        """ Needs working cache to pass """
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        # checking cache
        key_parts = [
            arguments.get("first_name") or "",
            arguments.get("last_name") or "",
            str(arguments.get("phone") or ""),
        ]
        key = "uid:" + hashlib.md5("".join(key_parts).encode("utf-8")).hexdigest()
        resp = self.settings.cache_get(key)
        self.assertTrue(resp)
        self.assertTrue(float(resp.decode()) > 0)

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        """ Needs working storage to pass """
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        # prepare our storage for test
        self.populate_storage_with_test_data(arguments.get("client_ids"))
        # make and process request
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, str) for i in v)
                        for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_invalid_interests_when_storage_is_down(self, arguments):
        # emulate disfunctional storage
        server = fakeredis.FakeServer()
        server.connected = False
        self.settings.client = fakeredis.FakeStrictRedis(server=server)

        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)

        self.assertEqual(code, api.INTERNAL_ERROR)


if __name__ == '__main___':
    unittest.main()
