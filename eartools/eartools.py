import torchaudio
import os
from os import rename
import pandas as pd
from dataclasses import dataclass, field
from time import time
from influxdb_client_3 import InfluxDBClient3, Point
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS

#DASHBOARD
TOKEN = "lxB5VtvRuEDCh2Q3ATSK6msJKaGpQ5kHuJomgGMFtpt8iM0gYDm--VO9ZlwOj47oxV11rttLN4KIE7JTrb2ELQ=="
DEV = "Dev team"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
DATA_BASE = "metrics"
POST_LEARN = '/learn'
POST_MONITOR = '/monitor'

#SERVER LOCATIONS
RAW_FILES = '../data/raw_appliances/'
MON_FILES = '../data/mon_appliances/'

#API 
URL = "http://127.0.0.1:8000"
LEARN = '/learn'
MONITOR = '/monitor'
URL_LEARN = URL + LEARN
URL_MON = URL + MONITOR


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

def generate_timestamp() -> int: 
      return round(time() * 1000)

@dataclass
class Recording:
      audio_file: str
      user_id: str
      class_id: int
      timestamp: int = field(init=False, default_factory=generate_timestamp)
      file_label: str = field(init=False)

      def __post_init__(self) -> None:
            self.file_label = f"{self.user_id}_{self.class_id}_{self.timestamp}.wav"
      
      def rename_rec(self, new_name=None):
            if new_name:
                 self.file_label = new_name
            rename(str(self.audio_file), str(self.file_label))
            return self.file_label
      
      def get_rec_details(self):
          return {"user_id": self.user_id, "class_id": self.class_id, "time_stamp": self.timestamp}
      
      def split_rec(self, split_length=3):
          sig, sr = torchaudio.load(self.audio_file)
          _, sig_len = sig.shape
          length = sig_len / sr # length seconds
          if os.path.isfile(self.metadata) == True:
              df_temp = pd.read_csv(self.metadata)
              d = df_temp.loc[(df_temp['classID'] == self.classID)]
              fsid = int(d['fsID'].max()) + split_length
          else:
              fsid = 9000000
  
          for i in range(0, round(length), split_length):
              fsid = fsid + i
              split_fn = str(fsid) + '-' + str(self.classID) + '-0-0.wav'
              csv_entry = {
                  'slice_file_name' : [str(split_fn)],
              '   fsID' : [fsid],
                  'start': [float(i)],
                  'end' : [float((i) + split_length)],
                  'salience' : [0],
                  'fold' : [self.directory],
                  'classID' : [self.classID],
                  'class' : [self.class_name]
              }
              df = pd.DataFrame(csv_entry)
              if os.path.isfile(self.metadata) == True: 
                  df.to_csv(self.metadata, mode='a', index=False, header=False)
              else:
                  df.to_csv(self.metadata, mode='a', index=False, header=True)
  

              split_start = i * sr
              split_end = split_start + split_length * sr
              sig = sig[:, split_start : split_end]
              torchaudio.save(self.directory + '/' + split_fn, sig, sr)

