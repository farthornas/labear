from dataclasses import dataclass, field
from jnius import autoclass
from kivy.utils import platform
import numpy as np
import os
from os import rename
import PyWave
from PyWave import WAVE_FORMAT_PCM, WAVE_FORMAT_IEEE_FLOAT
from time import time


if platform == 'android':
    Logger = autoclass('java.util.logging.Logger')
    logger = Logger.getLogger('[AlbinEars]')
    logger.info("running on android with [AlbinEars]")
else:
    from loguru import logger

class MyPlayer:
    def __init__(self):
        self.MediaPlayer = autoclass("android.media.MediaPlayer")
        self.mPlayer = self.MediaPlayer()
        #self.mPlayer.setDataSource(input_file)
        #self.mPlayer.prepare()
        self.state = ""
    
    def prepare(self):
        self.mPlayer.prepare()
        self.state = 'prepared'
    
    def play(self):
        self.mPlayer.start()
        self.state = "playing"
    
    def stop(self):
        self.mPlayer.stop()
        self.state = "stopped"
    
    def reset(self):
        self.mPlayer.reset()
        self.state = 'idle'
    
    def release(self):
        self.mPlayer.release()
        self.state = 'released'
    
    def get_state(self):
        return self.state
    
    def set_input_source(self, source):
        self.mPlayer.setDataSource(source)

class MyRecorder:
    def __init__(self):
        '''Recorder object To access Android Hardware'''
        self.MediaRecorder = autoclass('android.media.MediaRecorder')
        self.AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
        self.OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
        self.AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
    
        # create out recorder
        self.reset()
    
    def reset(self):
        logger.info(f"Resetting recorder ... ")
        self.mRecorder = self.MediaRecorder()
        self.mRecorder.setAudioSource(self.AudioSource.MIC)
        self.mRecorder.setOutputFormat(self.OutputFormat.MPEG_4)
        self.mRecorder.setAudioEncoder(self.AudioEncoder.AAC)
        self.mRecorder.setAudioEncodingBitRate(16*44100)
        self.mRecorder.setAudioSamplingRate(44100)
        self.output_file = ""
        self.mRecorder.setOutputFile(self.output_file)
        self.state = ""
        logger.warning(f"Recorder output and state is unset!")

    def prepare(self):
        logger.info(f"Preparing recorder ... ")
        self.mRecorder.prepare()
        self.state = "ready"
        return self.state
    
    def start(self):
        self.mRecorder.start()
        self.state = "recording"
        return self.state
    
    def stop(self):
        self.mRecorder.stop()
        self.state = "reset"
        return self.state

    
    def recording(self):
        self.state = "recording"
        return self.state
    
    def set_state(state):
        self.state = state
    
    
    def set_output_file(self, file_name):
        self.output_file = file_name
        self.mRecorder.setOutputFile(self.output_file)
    
    def get_output_file(self):
        return self.output_file
    
    def get_state(self):
        return self.state
    
    def get_metrics(self):
        return self.mRecorder.getMetrics()
    
    def release(self):
        return self.mRecorder.release()

def generate_timestamp() -> int: 
      return round(time() * 1000)


@dataclass
class Recording:
    audio_file: object
    user_id: str
    class_id: str
    timestamp: int = field(init=False, default_factory=generate_timestamp)
    file_label: str = field(init=False)
    file_path: str = field(init=False)
    file_type: str

    def __post_init__(self) -> None:
        self.file_label = f"{self.user_id}_{self.class_id}_{self.timestamp}"
        self.file_path = self.audio_file.get_output_file()

    def rename_rec(self, new_name=None):
        if new_name:
             self.file_label = new_name
        old_name = self.file_path
        new_name = f'{self.file_label}{self.file_type}'
        logger.info(f"Renaming file:{old_name} --> {new_name}")
        rename(old_name, str(new_name))
        self.file_path = new_name
        return new_name
    
    def get_rec_details(self):
        return {"user_id": self.user_id, "class_id": self.class_id, "time_stamp": self.timestamp}

    def get_file_path(self):
        return self.file_path
    
    def get_file_label(self):
        return self.file_label
    
    def clean_up(self):
        logger.info(f"Attemping to remove recording at {self.file_path}")
        try:
            os.remove(str(self.file_path))
        except FileNotFoundError as e:
            logger.info(f"Recording not found at: {self.file_path}")

    def split(self, length, path):
        logger.info(f"Splitting recoridng in {length} second slices")
        logger.info(f"Path to write output to: {path}")
        files = []
        logger.info(f"File to open: {self.file_path}")
        with PyWave.open(self.file_path) as f:
            logger.info(f"File opened...")
            samples = f.samples
            sr = f.frequency
            bytes_smpl = f.bytes_per_sample
            bits_smpl = f.bits_per_sample
            chnls = f.channels
            data = f.read()
            
            no_sections = int(np.ceil((samples / sr) / length))

            for i in range(no_sections):
                temp = data[i*sr*chnls*bytes_smpl*length:i*sr*chnls*bytes_smpl*length + sr*length*chnls*bytes_smpl]
                filename = f'{path}/rec_{i}.wav'

                with PyWave.open(filename,
                    mode = "w", 
                    channels = chnls, 
                    frequency = sr, 
                    bits_per_sample = bits_smpl, 
                    format = WAVE_FORMAT_IEEE_FLOAT) as nf:

                    nf.write(temp)
                    files.append(('files', open(filename, 'rb')))
        return files



