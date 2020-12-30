#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler    
except:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

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

class ValidationError(Exception):
    """Raises when validation check fails"""
    def __init__(self, message=None):
        self.message = message

class CharField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable
    
    def __get__(self, instance, owner):
        return self._value
    
    def __set__(self, instance, value):        
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")
            
            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")        
            else:
                self._value = ''            
        else:
            self._value = str(value)


class ArgumentsField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable
    
    def __get__(self, instance, owner):
        return self._value
    
    def __set__(self, instance, value):  
        print('arguments __set__:', instance, value)      
        if value is None:
            if self.required is True:
                raise ValidationError(message="The parameter is mandatory")
            
            if self.nullable is False:
                raise ValidationError(message="The parameter should be non-nullable")        
            else:
                self._value = {}           
        
        if not isinstance(value, dict):
            raise ValidationError(message="The parameter should be a dictionary")
        
        self._value = value


class EmailField(CharField):
    pass


class PhoneField(object):
    def __init__(self, required=None, nullable=None):
        self.required = required
        self.nullable = nullable


class DateField(object):
    def __init__(self, required=None, nullable=None):
        self.required = required
        self.nullable = nullable


class BirthDayField(object):
    def __init__(self, required=None, nullable=None):
        self.required = required
        self.nullable = nullable


class GenderField(object):
    def __init__(self, required=None, nullable=None):
        self.required = required
        self.nullable = nullable


class ClientIDsField(object):
    def __init__(self, required=None):
        self.required = required

    def __get__(self, instance, owner):
        pass


class ClientsInterestsRequest(object):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(object):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest(object):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    @classmethod
    def validate(cls, request):
        code = OK
        try:
            cls.account = request.get('body').get('account')
            cls.login = request.get('body').get('login')
            cls.token = request.get('body').get('token')
            cls.arguments = request.get('body').get('arguments')
            cls.method = request.get('body').get('method')
            print('-'*20)
            print(cls.account, cls.login, cls.token, type(cls.arguments), cls.method)
        except ValidationError as e:
            code = INVALID_REQUEST
            # add logging
        return code
        



def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    # 1 valid general request structure
    try:
        code = MethodRequest.validate(request)
        print("code: ", code)
    except:
        pass
    # 2 check auth
    # 3 valid specific request
    response = "placeholder"
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

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
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
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
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
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
