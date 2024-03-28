from typing import List

from fastapi import FastAPI, File, UploadFile, Form
import uvicorn
import os
import aiofiles
from dataclasses import dataclass
from influxdb_client_3 import InfluxDBClient3, Point
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from labear_api.cloud_upload import upload_many_blobs_from_stream_with_transfer_manager as upload_many_blobs_from_stream
#import tempfile



# Cloud data
BUCKET = "data_labear"
PROJECT = "labear"


#API 
URL = "http://127.0.0.1:8000"
LEARN = '/learn'
MONITOR = '/monitor'
URL_LEARN = URL + LEARN
URL_MON = URL + MONITOR

#DASHBOARD
TOKEN = "lxB5VtvRuEDCh2Q3ATSK6msJKaGpQ5kHuJomgGMFtpt8iM0gYDm--VO9ZlwOj47oxV11rttLN4KIE7JTrb2ELQ=="
DEV = "Dev team"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
DATA_BASE = "metrics"
POST_LEARN = '/learn'
POST_MONITOR = '/monitor'


@dataclass
class Metrics:
    token: str =  TOKEN
    org: str = DEV
    host: str = HOST
    database: str = DATA_BASE
    
    
    def __post_init__(self) -> None:
        self.client = InfluxDBClient3(host=self.host, token=self.token, org=self.org, database=self.database)
        

    def post(self, data, application):
        point = Point(application)
        for key, value in data.items():
            point.field(key, value)
        self.client.write(record=point, write_precision="s", timeout=5)


app = FastAPI()
metrics = Metrics()


async def file_handler(files, path):
    for file in files:
        out_file_path = os.path.join(path, str(file.filename))
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await file.read()
            result = await out_file.write(content)
    return result

def received_file(files):
    print("Files received")
    for file in files:
        print(f"File name:{file.filename}")
        print(f"File size:{file.size}")
   

    

@app.post(LEARN)
async def submit(
    user_id: str = Form(...),
    class_id: str = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    
    received_file(files)

    submitted = {
        "Payload": {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files_size":[file.size for file in files],
        "Filenames": [file.filename for file in files],}
    }
    metr = {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files": len(files)}
    print(f"Attempt gc upload....")
    upload_many_blobs_from_stream(bucket_name=BUCKET, files=files)
    
    metrics.post(metr, LEARN)
    return submitted

@app.post(MONITOR)
async def monitor(
    user_id: str = Form(...),
    class_id: str = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    received_file(files)
    
    submitted = {
        "Payload": {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files_size":[file.size for file in files],
        "Filenames": [file.filename for file in files],}
    }
    metr = {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files": len(files)}
    metrics.post(metr, MONITOR)
    
    return submitted

@app.get("/")
async def root():
    return {"message": "Hello World"}

def start():
    """Launched with `poetry run start` at root level"""
    uvicorn.run("labear_api.main:app", host="0.0.0.0", port=8000, reload=True)