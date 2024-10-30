from typing import List

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import RedirectResponse
import os
from dataclasses import dataclass
from influxdb_client_3 import InfluxDBClient3, Point
from influxdb_client import InfluxDBClient
from loguru import logger

import labear_api.ear as ear
from labear_api.cloud_connect import upload_blob

# Cloud data
BUCKET = "data_labear"
USER_DATA = "data/raw"
GC_USERS = "users"


#API 
URL = "http://127.0.0.1:8000"
LEARN = "/learn"
MONITOR = "/monitor"
URL_LEARN = URL + LEARN
URL_MON = URL + MONITOR

# DASHBOARD
TOKEN = os.environ['INFLUX_DB']
DEV = "Dev team"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
DATA_BASE = "metrics"
DASHBOARD_LEARN = LEARN.split('/')[-1]
DASHBOARD_MONITOR = MONITOR.split('/')[-1]


@dataclass
class Metrics:
    token: str = TOKEN
    org: str = DEV
    host: str = HOST
    database: str = DATA_BASE

    def __post_init__(self) -> None:
        self.client = InfluxDBClient3(host=self.host, token=self.token, org=self.org, database=self.database)
    """
            Example:
            .. code-block:: python

                # Use default dictionary structure
                dict_structure = {
                    "measurement": "h2o_feet",
                    "tags": {"location": "coyote_creek"},
                    "fields": {"water_level": 1.0},
                    "time": 1
                }
    """
    def post_records(self, data, application):
        record = {}
        record['fields'] = {}
        with InfluxDBClient(HOST, TOKEN) as client:
            time = data['request_info'].pop('time_stamp')
            files = data['request_info']['files']
            for file in files:
                record['fields'].update(file)
            record['time'] = int(time)
            record['measurement'] = application
            record['tags'] = data['request_info']
            if application == DASHBOARD_MONITOR:
                record['fields'].update(data['prediction']['probabilities'])
             # use the client to access the necessary APIs
            # for example, write data using the write_api
            with client.write_api() as writer:
                writer.write(bucket=self.database, org=self.org, record=record, write_precision='ms')

    def post_data_point(self, data, application):
        point = Point(application)
        for key, value in data.items():
            point.field(key, value)
        self.client.write(record=point, write_precision="ms", timeout=5)
    


app = FastAPI()
metrics = Metrics()

def log_fileinfo(files: list[UploadFile]):
    logger.info("Files received:")
    for file in files:
        logger.info(f"{file.filename} ({file.size/1000:0.2f} KB)")
        
def gc_upload_files(user_id, files):
    # just do single (first) file for now
    # TODO handle multiple files
    file = files[0].file
    file_name = files[0].filename
    destination_folder = f'{GC_USERS}/{user_id}/{USER_DATA}/' 
    upload_blob(BUCKET, file, destination_folder, file_name)
    logger.info(f"File {file_name} uploaded to {destination_folder}.")


@app.post(LEARN)
async def submit(
    user_id: str = Form(...),
    class_id: str = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):

    log_fileinfo(files)

    response = {
        "request_info": {
            "user_id": user_id,
            "class_id": class_id,
            "time_stamp": time_stamp,
            "files": [
                {"size": file.size, "name": file.filename} for file in files
            ]
        }
    }
    gc_upload_files(user_id=user_id, files=files)
    metrics.post_records(response, DASHBOARD_LEARN)
    return response


@app.post(MONITOR)
async def monitor(
    user_id: str = Form(...),
    class_id: str = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    log_fileinfo(files)

    response = {
        "request_info": {
            "user_id": user_id,
            "class_id": class_id,
            "time_stamp": time_stamp,
            "files": [
                {"size": file.size, "name": file.filename} for file in files
            ]
        }
    }
    # just do single (first) file for now
    # TODO handle multiple files

    file = files[0].file

    probabilities, prediction, score  = ear.predict(user_id, file)
    response["prediction"] = {
        "probabilities": probabilities,
        "prediction": prediction,
        "score": score.item()
    }
    if user_id == "debug":
        gc_upload_files(user_id=user_id, files=files)

    metrics.post_records(response, DASHBOARD_MONITOR)

    return response

# Redirect root url to docs
@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")

