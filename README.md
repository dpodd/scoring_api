## Scoring API
### Homework #3 for 'OTUS Python Professional' Course

A simple server that validates requests and sends responses with some data. More details are available in `description.md` (in Russian). 

The script was tested with Python 3.8.

To fire up the server with a default port 8089 use:
```
$ python api.py
```
It is possible to add optional parameters: a port number and the name of a log file.
```
$ python api.py [-p | --port 9000] [-l | --log log.txt]
```
Run tests:
```
$ python test.py
```
Now your can send requests for validation:
```
$ CURL -X POST -H "Content-Type: application/json" -d '{"account": "13", "token": "96e967ba7bad01b1b44c3bb6e4d4136cec50a19040807ac77064e755b631cb3febb9c06286df6d64f86238daed6f68ed7abdeff655b71ef827e0f895ae74661f","login": "oleg23", "method": "online_score", "arguments": {"phone": 79082223354, "email": "alas@alas" }}' localhost:8089/method

```
If you have run into Forbidden 403 response, just copy a valid token from the Python console (after a word "TOKEN:") and paste it into your curl's request at the place of the old token.