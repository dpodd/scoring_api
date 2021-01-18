import hashlib
import datetime
import functools
import unittest
from unittest.mock import patch
import api
from api import ClientIDsField, DateField, BirthDayField, CharField, EmailField, PhoneField, ArgumentsField, GenderField,\
                ValidationError
from icecream import ic

def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                # try:
                f(*new_args)
                # except:
                #     print(f"FAILED TEST with arguments: {new_args[1]} \n\tin {new_args[0]}")
                #     print('~'*10)
        return wrapper
    return decorator


def mock_get_interests(store, cid):
    if cid == 1:
        return ['sport', 'books']
    elif cid == 2:
        return ['music', 'travel']
    elif cid == 3:
        return ["books"]
    else:
        return ['cars']

class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.settings = {}

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            msg = datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
            request["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()

    def test_empty_request(self):
        _, code, ctx = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, request):
        _, code, ctx = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

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
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)
        ic(response, code, ctx)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ])
    @patch('api.get_interests')
    def test_invalid_interests_request(self, arguments, mock):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        # mock request to Redis server
        mock.side_effect = mock_get_interests
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    @patch('api.get_interests')
    def test_ok_interests_request(self, arguments, mock):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        # mock request to Redis server
        mock.side_effect = mock_get_interests
        response, code, ctx = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, str) for i in v)
                        for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


class stub():
    pass


class TestFieldsSuite(unittest.TestCase):
    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": [], "field flags": {"required": True}},
        {"case args": 123, "field flags": {"required": True}},
        {"case args": ['123'], "field flags": {"required": True}},
        {"case args": [123, '345'], "field flags": {"required": True}}
    ])
    def test_clients_ids_fields_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.clients_ids = ClientIDsField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.clients_ids = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": [1234]},
        {"case args": [1234, 4567]}
    ])
    def test_clients_ids_fields_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.clients_ids = ClientIDsField(**init_kwargs)
        inst = stub()
        inst.clients_ids = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": ['01-01-2000']},
        {"case args": '01-01-2000'},
        {"case args": '32.01.2000'},
        {"case args": '02.13.2000'}
    ])
    def test_datefield_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.date = DateField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.date = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": '01.01.2000'},
    ])
    def test_datefield_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.date = DateField(**init_kwargs)
        inst = stub()
        inst.date = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": ['01-01-2000']},
        {"case args": '01-01-2000'},
        {"case args": '32.01.2000'},
        {"case args": '02.13.2000'},
        {"case args": '01.12.1936'}
    ])
    def test_birthday_field_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.birthday = BirthDayField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.birthday = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": '01.01.2000'},
    ])
    def test_birthday_field_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.birthday = BirthDayField(**init_kwargs)
        inst = stub()
        inst.birthday = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": ['Vasily']},
        {"case args": 1234567},
    ])
    def test_charfield_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.some_field = CharField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.some_field = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": '01.01.2000'},
    ])
    def test_charfield_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.some_field = CharField(**init_kwargs)
        inst = stub()
        inst.some_field = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": 1234567},
        {"case args": 'vasilygoogle.com'},
    ])
    def test_emailfield_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.email = EmailField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.email = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": 'vasily@google.com'},
    ])
    def test_emailfield_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.email = EmailField(**init_kwargs)
        inst = stub()
        inst.email = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": '1', "field flags": {"required": False}},
        {"case args": [], "field flags": {"required": False}},
        {"case args": [22], "field flags": {"required": False}},
        {"case args": 4, "field flags": {"required": False}}
    ])
    def test_gender_field_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.gender = GenderField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.gender = args.get("case args")


    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": 1}
    ])
    def test_gender_field_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.gender = GenderField(**init_kwargs)
        inst = stub()
        inst.gender = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": '+79081112233', "field flags": {"required": False}},
        {"case args": [], "field flags": {"required": False}},
        {"case args": [79081112233], "field flags": {"required": False}},
        {"case args": 89081112233, "field flags": {"required": False}},
        {"case args": 890811122, "field flags": {"required": False}}
    ])
    def test_phone_field_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.phone = PhoneField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.phone = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": 79081112233},
        {"case args": '79081112233'}
    ])
    def test_phone_field_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.phone = PhoneField(**init_kwargs)
        inst = stub()
        inst.phone = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": [], "field flags": {"required": False}},
        {"case args": '"first_name": "Vasily", "last_name": "Vasin"', "field flags": {"required": False}},
    ])
    def test_arguments_field_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.arguments = ArgumentsField(**init_kwargs)
        inst = stub()
        with self.assertRaises(ValidationError) as ctx:
            inst.arguments = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": False, "nullable": True}},
        {"case args": {}},
        {"case args": {"first_name": "Vasily", "last_name": "Vasin"}}
    ])
    def test_arguments_field_valid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        stub.arguments = ArgumentsField(**init_kwargs)
        inst = stub()
        inst.arguments = args.get("case args")


if __name__ == "__main__":
    unittest.main()
