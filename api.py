#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
import re
from scoring import get_score, get_interests
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


class DataNotProvided(Exception):
    """Handling 'None' assignment"""


class BaseField(ABC):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        return instance.__dict__[self._name]

    def __set__(self, instance, value):
        try:
            self.validate_field(instance, value)
        except DataNotProvided:
            instance.__dict__[self._name] = None
        except:
            logging.exception("Validation error")
            raise
        else:
            value = self.value_conversion(value)
            instance.__dict__[self._name] = value

    def validate_field(self, instance, value):
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter '%s' is mandatory" % self._name)

            if self.nullable is False:
                raise ValidationError(message="The parameter '%s' should be non-nullable" % self._name)

            raise DataNotProvided
        else:
            self.check_conditions(value)

    def check_conditions(self, value):
        """Specific conditions for each field"""

    def value_conversion(self, value):
        """Method to implement in child classes"""
        return value


class CharField(BaseField):
    def check_conditions(self, value):
        if not isinstance(value, str):
            raise ValidationError(message="The parameter %s should be a string" % self.__class__)


class ArgumentsField(BaseField):
    def check_conditions(self, value):
        if not isinstance(value, dict):
            raise ValidationError(message="The parameter %s should be a dictionary" % self.__class__)


class EmailField(CharField):
    def check_conditions(self, value):
        super().check_conditions(value)

        if '@' not in value:
            raise ValidationError(message="Invalid email given")


class PhoneField(BaseField):
    def check_conditions(self, value):
        if not isinstance(value, (int, str)):
            raise ValidationError(message="The parameter %s should be a string or integer" % self.__class__)

        phone_pattern = re.compile(r'^7\d{10}')
        if not phone_pattern.match('%s' % value):
            raise ValidationError(message="Invalid phone number given: %s" % value)

    def value_conversion(self, value):
        return str(value)


class DateField(CharField):
    def check_conditions(self, value):
        super().check_conditions(value)
        try:
            self.value_conversion(value)
        except:
            raise ValidationError(message="Invalid date; date should have a format 'DD.MM.YYYY' but %s is given"
                                  % value)

    def value_conversion(self, value):
        return datetime.date(year=int(value[6:]),
                             month=int(value[3:5]),
                             day=int(value[:2]))


class BirthDayField(DateField):
    def check_conditions(self, value):
        super().check_conditions(value)

        birthday = self.value_conversion(value)

        if datetime.date.today() - birthday > datetime.timedelta(AGE_LIMIT * 365.2425):
            raise ValidationError(message="Age limit exceeded")


class GenderField(BaseField):
    def check_conditions(self, value):
        if not isinstance(value, int):
            raise ValidationError(message="The parameter %s should be an integer" % self.__class__)

        if value not in [0, 1, 2]:
            raise ValidationError(message="Invalid gender field")

    def value_conversion(self, value):
        return str(value)


class ClientIDsField(BaseField):
    def check_conditions(self, value):
        if not isinstance(value, list):
            raise ValidationError(message="The parameter %s should be a list" % self.__class__)

        if not value:
            raise ValidationError(message="Client ID list is empty")

        for item in value:
            if not isinstance(item, int):
                raise ValidationError(message="Invalid client ID is given: %s" % value)


class ApiRequest:
    def __init__(self, **kwargs):
        self.valid_fields = [k for k, v in self.__class__.__dict__.items() if isinstance(v, BaseField)]
        self.has = []

        for k in self.valid_fields:
            if k in kwargs.keys():
                setattr(self, k, kwargs[k])
                self.has.append(k)
            else:
                setattr(self, k, None)

        self.validate()

    def validate(self):
        pass


class MethodRequest(ApiRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


class ClientsInterestsRequest(MethodRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(MethodRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        if not ((self.phone and self.email) or (self.first_name and self.last_name) or (self.gender and self.birthday)):
            raise ValidationError(message="Not enough data provided")


def check_auth(request):
    if request.is_admin:
        phrase = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        digest = hashlib.sha512(phrase.encode('utf-8')).hexdigest()
    else:
        phrase = request.account + request.login + SALT
        digest = hashlib.sha512(phrase.encode('utf-8')).hexdigest()
    logging.info('TOKEN: %s' % digest)
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code, ctx = None, None, ctx
    methods = {
        'online_score': online_score_handler,
        'clients_interests': clients_interests_handler
    }
    _request = request
    try:
        request = MethodRequest(**request.get("body"))

        if not check_auth(request):
            logging.error("Wrong authentication token")
            return None, FORBIDDEN, ctx

        try:
            response, code, ctx = methods[request.method](request, ctx, store)
        except ValidationError:
            raise
        except:
            logging.exception("Error during request: %s" % _request)
            raise
        else:
            return response, code, ctx

    except ValidationError as e:
        logging.error("Validation error: %s" % e.message)
        code = INVALID_REQUEST
        return {'msg': 'validation error'}, code, ctx
    except Exception as e:
        raise


def online_score_handler(request: MethodRequest, ctx, store):
    if request.is_admin:
        score = 42
    else:
        request = OnlineScoreRequest(**request.arguments)
        ctx['has'] = request.has
        score = get_score(store, phone=request.phone,
                          email=request.email, birthday=request.birthday,
                          gender=request.gender, first_name=request.first_name,
                          last_name=request.last_name)
    response = {"score": score}
    return response, OK, ctx


def clients_interests_handler(request: MethodRequest, ctx, store):
    request = ClientsInterestsRequest(**request.arguments)
    response = {}
    for cid in request.client_ids:
        interests = get_interests(store, cid)
        response.update({str(cid): interests})
    ctx.update({"nclients": len(response)})
    return response, OK, ctx


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

        if request or (request == {}):
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
