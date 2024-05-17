import requests
import glob

file = glob.glob('test_submit.wav')[0]

#url = 'https://albinai.fly.dev/monitor'
url = 'http://127.0.0.1:8000/learn'

files = [('files', open(file, 'rb'))]
payload = {"user_id": "1234", "class_id": 'test_submit', "time_stamp": 12345, "is_accepted": False}

resp = requests.post(url=url, data=payload, files=files) 
print(resp.json())