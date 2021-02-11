import unittest

from tests import cases
from api import BaseField, ClientIDsField, DateField, BirthDayField, CharField, EmailField, PhoneField, ArgumentsField,\
                GenderField, ValidationError


class TestBaseField(unittest.TestCase):
    @cases([
        {"required": True, "nullable": False},
        {"required": True, "nullable": True},
        {"required": False, "nullable": False},
    ])
    def test_base_field_null_handling_error(self, init_kwargs):
        class Stub:  # need to create a class for correctly calling __set_name__ method in the descriptor
            some_field = BaseField(**init_kwargs)

        inst = Stub()
        with self.assertRaises(ValidationError):
            inst.some_field = None

    @cases([
        {"required": False, "nullable": True},
    ])
    def test_base_field_null_handling_ok(self, init_kwargs):
        class Stub:  # need to create a class for correctly calling __set_name__ method in the descriptor
            some_field = BaseField(**init_kwargs)

        inst = Stub()
        inst.some_field = None
        self.assertEqual(inst.some_field, None)


class TestChildFields(unittest.TestCase):
    @cases([
        123,
        [],
        ['123'],
        [123, '345']
    ])
    def test_client_id_invalid(self, value):
        with self.assertRaises(ValidationError):
            ClientIDsField().check_conditions(value)

    @cases([
        [1234],
        [1234, 4567]
    ])
    def test_client_id_valid(self, value):
        ClientIDsField().check_conditions(value)

    @cases([
        ['01-01-2000'],
        '32.01.2000',
        '02.13.2000'
    ])
    def test_datefield_invalid(self, value):
        with self.assertRaises(ValidationError):
            DateField().check_conditions(value)

    @cases([
        '01.01.2000',
    ])
    def test_datefield_valid(self, value):
        DateField().check_conditions(value)

    @cases([
        ['01-01-2000'],
        '32.01.2000',
        '02.13.2000',
        '01.12.1936',
    ])
    def test_birthday_field_invalid(self, value):
        with self.assertRaises(ValidationError):
            BirthDayField().check_conditions(value)

    @cases([
        '01.01.2000'
    ])
    def test_birthday_field_valid(self, value):
        BirthDayField().check_conditions(value)

    @cases([
        ['Vasily'],
        1234567
    ])
    def test_charfield_invalid(self, value):
        with self.assertRaises(ValidationError):
            CharField().check_conditions(value)

    @cases([
        '01.01.2000'
    ])
    def test_charfield_valid(self, value):
        CharField().check_conditions(value)

    @cases([
        1234567,
        'vasilygoogle.com',
    ])
    def test_emailfield_invalid(self, value):
        with self.assertRaises(ValidationError):
            EmailField().check_conditions(value)

    @cases([
        'vasily@google.com',
    ])
    def test_emailfield_valid(self, value):
        EmailField().check_conditions(value)

    @cases([
        '1',
        [],
        [22],
        4,
    ])
    def test_gender_field_invalid(self, value):
        with self.assertRaises(ValidationError):
            GenderField().check_conditions(value)

    @cases([
        0,
        1,
        2,
    ])
    def test_gender_field_valid(self, value):
        GenderField().check_conditions(value)

    @cases([
        '+79081112233',
        [],
        [79081112233],
        89081112233,
        890811122,
    ])
    def test_phone_field_invalid(self, value):
        with self.assertRaises(ValidationError):
            PhoneField().check_conditions(value)

    @cases([
        79081112233,
        '79081112233'
    ])
    def test_phone_field_valid(self, value):
        PhoneField().check_conditions(value)

    @cases([
        [],
        '"first_name": "Vasily", "last_name": "Vasin"',
    ])
    def test_arguments_field_invalid(self, value):
        with self.assertRaises(ValidationError):
            ArgumentsField().check_conditions(value)

    @cases([
        {},
        {"first_name": "Vasily", "last_name": "Vasin"},
    ])
    def test_arguments_field_valid(self, value):
        ArgumentsField().check_conditions(value)


if __name__ == '__main___':
    unittest.main()
