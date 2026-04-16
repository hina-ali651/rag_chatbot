import urllib.request
import urllib.error
import json

data = json.dumps({
    'session_id': '9c04f255-9d4c-40ec-92cc-78df0452688e',
    'user_email': 'test@test.com',
    'messages': [{'role': 'user', 'content': 'hello'}]
}).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/chat',
    data=data,
    headers={'Content-Type': 'application/json'}
)

try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(e.read().decode())
