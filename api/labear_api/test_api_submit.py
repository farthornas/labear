import requests

file = 'test_submit.wav'

url = 'http://0.0.0.0:8000/monitor'
#files = [('files', open('test_files/a.txt', 'rb')), ('files', open('test_files/b.txt', 'rb'))]
files = [('files', open(file, 'rb'))]

#payload ={"foo": "bar"}
payload = {"user_id": "1234", "class_id": 11, "time_stamp": 12345, "is_accepted": False}
resp = requests.post(url=url, data=payload, files=files) 
print(resp.json())