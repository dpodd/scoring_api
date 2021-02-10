import unittest

from api import ClientIDsField, DateField, BirthDayField, CharField, EmailField, PhoneField, ArgumentsField, GenderField,\
                ValidationError
from tests import cases


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

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            clients_ids = ClientIDsField(**init_kwargs)

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

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            clients_ids = ClientIDsField(**init_kwargs)

        inst = stub()
        inst.clients_ids = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": ['01-01-2000']},
        {"case args": '32.01.2000'},
        {"case args": '02.13.2000'}
    ])
    def test_datefield_invalid(self, args):
        init_kwargs = {}
        if "required" in list(args.get('field flags', {})):
            init_kwargs.update({"required": args.get('field flags').get("required")})
        if "nullable" in list(args.get('field flags', {})):
            init_kwargs.update({"nullable": args.get('field flags').get("nullable")})

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            date = DateField(**init_kwargs)

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

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            date = DateField(**init_kwargs)

        inst = stub()
        inst.date = args.get("case args")

    @cases([
        {"case args": None, "field flags": {"required": True}},
        {"case args": None, "field flags": {"required": False, "nullable": False}},
        {"case args": ['01-01-2000']},
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

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            birthday = BirthDayField(**init_kwargs)

        inst = stub()
        with self.assertRaises(ValidationError):
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

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            birthday = BirthDayField(**init_kwargs)

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

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            some_field = CharField(**init_kwargs)

        inst = stub()
        with self.assertRaises(ValidationError):
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

        class stub: # need to create class for correctly calling __set_name__ method in descriptor
            some_field = CharField(**init_kwargs)

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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            email = EmailField(**init_kwargs)

        inst = stub()
        with self.assertRaises(ValidationError):
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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            email = EmailField(**init_kwargs)

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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            gender = GenderField(**init_kwargs)

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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            gender = GenderField(**init_kwargs)

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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            phone = PhoneField(**init_kwargs)

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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            phone = PhoneField(**init_kwargs)

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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            arguments = ArgumentsField(**init_kwargs)

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

        class stub:  # need to create class for correctly calling __set_name__ method in descriptor
            arguments = ArgumentsField(**init_kwargs)

        inst = stub()
        inst.arguments = args.get("case args")


if __name__ == '__main___':
    unittest.main()
