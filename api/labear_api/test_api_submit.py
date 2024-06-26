import requests
import glob
from cloud_upload import upload_many_blobs_from_stream_with_transfer_manager as upload_gc
from pydub import AudioSegment
import tempfile
import torchaudio
file = glob.glob('test2.m4a')[0]

url = 'https://albinai.fly.dev/monitor'
#url = 'http://127.0.0.1:8000/learn'

files = [('files', open(file, 'rb'))]
payload = {"user_id": "1234", "class_id": 'test_submit', "time_stamp": 12345, "is_accepted": False}

def with_requests():
    resp = requests.post(url=url, data=payload, files=files) 
    print(resp.json())

def with_gc():
    print(files[0].file_name)
    upload_gc(bucket_name="data_labear", files=files)
def with_temp():
    signal, sr = None, None
    with tempfile.TemporaryFile() as tp:

        temp = AudioSegment.from_file(file, format='m4a')
        temp.export(tp, format='wav')
        signal, sr = torchaudio.load(tp, channels_first=False)
    return signal, sr


if __name__== "__main__":
    print("Attempting to upload to google cloud")
    with_requests()