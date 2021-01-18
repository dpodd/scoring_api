#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from typing import Type
import re
from scoring import get_interests, get_score
from http.server import HTTPServer, BaseHTTPRequestHandler
from store import Store

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}
AGE_LIMIT = 70


class ValidationError(Exception):
    """Raises when validation check fails"""
    def __init__(self, message=None):
        self.message = message


class BaseField(ABC):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable
        self._value = None

    def __get__(self, instance, owner):
        return self._value


class CharField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")
            
            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")

            self._value = value
        else:
            if not isinstance(value, str):
                raise ValidationError(message="The parameter should be a string")

            self._value = value


class ArgumentsField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")
            
            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")        

            self._value = value
        else:
            if not isinstance(value, dict):
                raise ValidationError(message="The parameter should be a dictionary")
        
            self._value = value


class EmailField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")

            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")

            self._value = value
        else:
            if not isinstance(value, str):
                raise ValidationError(message="The parameter should be a string")

            if '@' not in value:
                raise ValidationError(message="Invalid email given")

            self._value = value


class PhoneField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")

            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")

            self._value = value
        else:
            if not isinstance(value, (int, str)):
                raise ValidationError(message="The parameter should be a string or integer")

            phone_pattern = re.compile(r'^7\d{10}')
            if not phone_pattern.match('%s' % value):
                raise ValidationError(message="Invalid phone number")

            self._value = str(value)


class DateField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")

            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")

            self._value = value
        else:
            if not isinstance(value, str):
                raise ValidationError(message="The parameter should be a string")

            date_pattern = re.compile(r'(\d{2})\.(\d{2})\.(\d{4})')
            match = date_pattern.match(value)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                try:
                    date = datetime.date(year=year, month=month, day=day)
                except:
                    raise ValidationError(message="Invalid date; date should have a format 'DD.MM.YYYY', but given '%s'" % value)
            else:
                raise ValidationError(message="Invalid date; date should have a format DD.MM.YYYY")

            self._value = date


class BirthDayField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")

            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")

            self._value = value
        else:
            if not isinstance(value, str):
                raise ValidationError(message="The parameter should be a string")

            birthday_pattern = re.compile(r'(\d{2})\.(\d{2})\.(\d{4})')
            match = birthday_pattern.match(value)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                try:
                    birthday = datetime.date(year=year, month=month, day=day)
                except:
                    raise ValidationError(message="Invalid date; date should have a format 'DD.MM.YYYY', but given '%s'" % value)
            else:
                raise ValidationError(message="Invalid date; date should have a format 'DD.MM.YYYY', but given '%s'" % value)

            if datetime.date.today() - birthday > datetime.timedelta(AGE_LIMIT * 365.2425):
                raise ValidationError(message="Age limit exceeded")

            self._value = birthday


class GenderField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")

            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")

            self._value = value
        else:
            if not isinstance(value, int):
                raise ValidationError(message="The parameter should be an integer")

            if value not in [0, 1, 2]:
                raise ValidationError(message="Invalid gender field")

            self._value = str(value)


class ClientIDsField(BaseField):
    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")

            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")

            self._value = value
        else:
            if not isinstance(value, list):
                raise ValidationError(message="The parameter should be a list")

            if not value:
                raise ValidationError(message="Client ID list is empty")

            for item in value:
                if not isinstance(item, int):
                    raise ValidationError(message="Invalid client ID is given")

            self._value = value


class MethodRequest(object):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def validate(self, request):
        self.account = request.get('body').get('account')
        self.login = request.get('body').get('login')
        self.token = request.get('body').get('token')
        self.arguments = request.get('body').get('arguments')
        self.method = request.get('body').get('method')
        return self


class ClientsInterestsRequest(MethodRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def validate(self, request: Type[MethodRequest]):
        self.client_ids = request.arguments.get('client_ids')
        self.date = request.arguments.get('date')
        return self

    def get_interests(self, store):
        result = {}
        for cid in self.client_ids:
            interests = get_interests(store, cid)
            result.update({str(cid): interests})
        return result


class OnlineScoreRequest(MethodRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)
    VALID_ARGUMENTS = ["first_name", "last_name", "email", "phone", "birthday", "gender"]

    def validate(self, request: Type[MethodRequest]):
        self.first_name = request.arguments.get('first_name')
        self.last_name = request.arguments.get('last_name')
        self.email = request.arguments.get('email')
        self.phone = request.arguments.get('phone')
        self.birthday = request.arguments.get('birthday')
        self.gender = request.arguments.get('gender')

        if not ((self.phone and self.email) or (self.first_name and self.last_name) or (self.gender and self.birthday)):
            raise ValidationError(message="Not enough data provided")

        return self

    def get_score(self, store):
        return get_score(store, self.phone, self.email, birthday=self.birthday,
                         gender=self.gender, first_name=self.first_name, last_name=self.last_name)


def check_auth(request):
    if request.is_admin:
        phrase = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        digest = hashlib.sha512(phrase.encode('utf-8')).hexdigest()
    else:
        phrase = request.account + request.login + SALT
        digest = hashlib.sha512(phrase.encode('utf-8')).hexdigest()
        print("TOKEN: ", digest)
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code, ctx = None, None, ctx
    try:
        # 1 validate general request structure
        request = MethodRequest().validate(request)

        # 2 check auth
        if not check_auth(request):
            logging.error("Wrong authentication token")
            return None, FORBIDDEN, ctx

        # 3 validate method arguments and dispatch to a specific method
        if request.method == 'online_score':
            # adding args to the context dictionary
            ctx['has'] = [key for key in request.arguments.keys() if key in OnlineScoreRequest.VALID_ARGUMENTS]
            # process a request
            request = OnlineScoreRequest().validate(request)
            if not request.is_admin:
                score = request.get_score(store)
            else:
                score = 42
            response = {"score": score}
            return response, OK, ctx

        elif request.method == 'clients_interests':
            request = ClientsInterestsRequest().validate(request)
            response = request.get_interests(store)
            ctx.update({"nclients": len(response)})
            return response, OK, ctx
    except ValidationError as e:
        logging.error("Validation error: %s" % e.message)
        code = INVALID_REQUEST
        return {'msg': 'validation error'}, code, ctx


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = Store()

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code, context = self.router[path]({"body": request, "headers": self.headers},
                                                                context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        result_string = json.dumps(r).encode('utf-8')
        self.wfile.write(result_string)
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8089)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
