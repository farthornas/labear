from dataclasses import dataclass, field
from functools import partial
from jnius import autoclass
from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivy.utils import platform
import os
from os import rename
from pydub import AudioSegment

import requests
from time import time
import tempfile
Logger = autoclass('java.util.logging.Logger')
mylogger = Logger.getLogger('[AlbinEars]')

# Android
REC_DEFAULT_FILE_NAME = 'rec.wav'

#API 
URL = 'https://albinai.fly.dev'
# URL = 'http://0.0.0.0:8000'
LEARN = '/learn'
MONITOR = '/monitor'
URL_LEARN = URL + LEARN
URL_MON = URL + MONITOR
TEST_ID = 99

has_recording = False

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

    def __post_init__(self) -> None:
        self.file_label = f"{self.user_id}_{self.class_id}_{self.timestamp}"
        self.file_path = self.audio_file.file_path

    def rename_rec(self, new_name=None):
        if new_name:
             self.file_label = new_name
        old_name = self.audio_file.file_path
        new_name = f'{self.file_label}.wav'
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
        os.remove(self.file_path)


def upload_file(recording, url, **kwargs):
    wavs = AudioSegment.from_file(recording.get_file_path()).dice(3)

    files = []
    
    payload = {}
    new_name = recording.rename_rec()
    payload = recording.get_rec_details()
    payload.update(kwargs)
    files.append(('files', open(new_name, 'rb')))
    resp = requests.post(url=url, files=files, data=payload)
    with tempfile.TemporaryDirectory() as tempdirname:
        for k, wav in enumerate(wavs):
            file_name = f'{recording.get_file_label()}_{k}.wav'
            file = f'{tempdirname}/{file_name}'
            wav.export(file, format='wav')
            files.append(('files', open(file, 'rb')))
        resp = requests.post(url=url, files=files, data=payload)
        recording.clean_up()
    try:
        response = resp.json()
        recording.clean_up()
    except ValueError as err:
        print(f"Response from API missing: {err}")
        return err
    return response
    #return payload

class MenuScreen(Screen):
    pass

class Rec(Screen):
    def __init__(self, **kwargs):
        super(Rec, self).__init__(**kwargs)
        self.has_recording = False
        self.monitor_state = 'Monitor not running'
    
    def on_enter(self, *args):
        self.update_labels()

        self.menu_screen = self.manager.get_screen("menu")
        mylogger.info('Preparing to learn new sound...')
        return super().on_enter(*args)

    
    audio = ObjectProperty()

    def record(self):
        mylogger.info('Started listening - recording starting')
        self.audio.file_path = REC_DEFAULT_FILE_NAME
        path = self.audio.file_path
        mylogger.info(f"path of recording:{path}")
        state = self.audio.state
        if state == 'ready':
            self.audio.start()
        if state == 'recording':
            self.audio.stop()
            self.has_recording = True
        self.upload_state = 'Audio Not Uploaded'
        self.update_labels() 

    def playback(self):
        state = self.audio.state
        
        if state == 'playing':
            self.audio.stop()
        else:
            self.audio.play()
        self.update_labels()
    
    def upload(self):
        #self.update_labels()
        state = self.audio.state
        mylogger.info(f"Attempt upload...")
            
        if self.has_recording == True and state == 'ready':
            mylogger.info(f"Recording is ready to be uploaded")

            #file_Sd = self.audio.file_path.split("file://")[1]
            recording = Recording(audio_file=self.audio, user_id=self.menu_screen.ids["text_user"].text, class_id=self.ids['text_app'].text)
            mylogger.info(f"Record details: {recording.get_rec_details()}")

            resp = upload_file(recording, URL_LEARN, app_name=self.ids['text_app'].text, test='test')
            mylogger.info(f"Upload: {recording.get_rec_details()}")
            self.upload_state = 'upload_complete'
            self.has_recording = False
        self.update_labels()

    def update_labels(self):
        record_button = self.ids['record_button']
        play_button = self.ids['play_button']
        upload_button = self.ids['upload_button']
        state_label = self.ids['state']
        upload_state = self.ids['upload_state_label']
        text_app = self.ids['text_app']

        state = self.audio.state
        play_button.disabled  = not self.has_recording
        upload_button.disabled  = not self.has_recording

        state_label.text = "AudioPlayer State: " + state

        if state == 'ready':
            record_button.text = 'START RECORD'
            play_button.text = 'PLAY AUDIO'
            record_button.disabled = False
            text_app.disabled = False
        
        if state == 'recording':
            record_button.text = 'STOP RECORD'
            upload_button.disabled = True
            play_button.disabled = True
            text_app.disabled = True
            upload_state.text = 'Audio Not Uploaded'           

        if state == 'playing':
            play_button.text = 'STOP AUDIO'
            record_button.disabled = True
            upload_button.disabled = True
            text_app.disabled = True
        
        if self.upload_state == 'upload_complete':
            upload_button.disabled = True
            upload_state.text = 'Audio Uploaded'
    has_recording = False
    upload_state = 'Audio Not Uploaded'

    
class Monitor(Screen):
    def __init__(self, **kwargs):
        super(Monitor, self).__init__(**kwargs)
        self.monitoring = False
        self.monitor_state = 'Not monitoring'

    
    def on_enter(self, *args):
        self.update_labels()
        self.menu_screen = self.manager.get_screen("menu")

        return super().on_enter(*args)

    def callback_upload(self, *largs):
        self.audio.stop()
        recording = Recording(audio_file=self.audio, user_id=self.menu_screen.ids["text_user"].text, class_id='test_mon')
        resp = upload_file(recording, URL_MON)
        print(resp)

    def callback_monitor(self, *largs):
        self.audio.start()
        self.event_upload = Clock.schedule_once(partial(self.callback_upload), 5)

    def monitor(self):
        state = self.audio.state
        #self.monitoring = True
        self.upload_state = 'Audio Not Uploaded'
        if self.monitoring:
            self.stop_monitor()
        else:
            self.monitoring = True
            self.monitor_state = 'Monitoring'
            self.audio.start()
            self.event_upload = Clock.schedule_once(partial(self.callback_upload), 5)
            self.event_monitor = Clock.schedule_interval(partial(self.callback_monitor), 20)
        self.update_labels()


    def stop_monitor(self):
        
        if self.monitoring:
            self.monitor_state = 'Not Monitoring'
        self.monitoring = False
        self.audio.stop()
        self.event_monitor.cancel()
        self.event_upload.cancel()
        self.update_labels()

    def update_labels(self):
        monitor_button = self.ids['monitor_button']
        state_label = self.ids['state']
        upload_state = self.ids['upload_state_label']

        state = self.audio.state

        state_label.text = "AudioPlayer State: " + state

        if state == 'ready':
            monitor_button.text = 'MONITOR'
        
        if self.monitoring:
            monitor_button.text = 'STOP MONITOR'
            upload_state.text = 'Audio Not Uploaded'

        if not self.monitoring:
            monitor_button.text = 'MONITOR'

        
        if self.monitor_state == 'upload_complete':
            upload_state.text = 'Audio Uploaded'
    has_recording = False
    upload_state = 'Audio Not Uploaded'



# Create the screen manager
sm = ScreenManager()
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(Rec(name='learn'))
sm.add_widget(Monitor(name='monitor'))

class LabearApp(MDApp):

    def on_start(self):
        mylogger.info("Starting application!")
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.INTERNET, Permission.RECORD_AUDIO, Permission.WAKE_LOCK])

    def build(self):
        #screen = Builder.load_string(screen_helper)
        self.icon = "application/app_images/icon7.png"
        screen = Builder.load_file("application/AudioMon.kv") 


        return screen


#LabearApp().run()