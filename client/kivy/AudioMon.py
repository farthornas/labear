from dataclasses import dataclass, field
from functools import partial
from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
import os
from os import rename
import pandas as pd
import requests
from time import time
import audiosegment
import tempfile

#API 
#URL = 'https://albinai.fly.dev'
URL = 'http://0.0.0.0:8000'
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
        self.file_path = self.audio_file.file_path.split("file://")[1]

    def rename_rec(self, new_name=None):
        if new_name:
             self.file_label = new_name
        print(self.audio_file.file_path)
        rename(str(self.file_path), str(f'{self.file_path}/{self.file_label}.wav'))
        return self.file_label
    
    def get_rec_details(self):
        return {"user_id": self.user_id, "class_id": self.class_id, "time_stamp": self.timestamp}

    def get_file_path(self):
        return self.file_path
    
    def get_file_label(self):
        return self.file_label
    
    def clean_up(self):
        os.remove(self.file_path)


def upload_file(recording, url, **kwargs):
    wavs = audiosegment.from_file(recording.get_file_path()).dice(3)
    files = []
    payload = {}
    payload = recording.get_rec_details()
    payload.update(kwargs)
    with tempfile.TemporaryDirectory() as tempdirname:
        for k, wav in enumerate(wavs):
            file_name = f'{recording.get_file_label()}_{k}.wav'
            file = f'{tempdirname}/{file_name}'
            wav.export(file, format='wav')
            files.append(('files', open(file, 'rb')))
        resp = requests.post(url=url, files=files, data=payload)
        recording.clean_up()
    return resp.json()


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
        return super().on_enter(*args)

    
    audio = ObjectProperty()

    def record(self):
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
            
        if self.has_recording == True and state == 'ready':
            #file_Sd = self.audio.file_path.split("file://")[1]
            recording = Recording(audio_file=self.audio, user_id=self.menu_screen.ids["text_user"].text, class_id=self.ids['text_app'].text)
            resp = upload_file(recording, URL_LEARN, app_name=self.ids['text_app'].text, test='test')
            print(resp)
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
    #has_recording = False
        self.monitoring = False
        self.monitor_state = 'Not monitoring'

    
    def on_enter(self, *args):
        self.update_labels()
        self.menu_screen = self.manager.get_screen("menu")

        return super().on_enter(*args)

    #upload_state = 'Audio Not Uploaded'
    
    #audio = ObjectProperty()
    #def on_enter(self, *args):
    #    self.update_labels()
    #    return super().on_enter(*args)

    def callback_upload(self, *largs):
        #if self.has_recording == True and state == 'ready':
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

    def build(self):
        #screen = Builder.load_string(screen_helper)
        self.icon = "app_images/icon7.png"
        self.icon_size = 0.2
        
        screen = Builder.load_file("AudioMon.kv") 

        return screen


LabearApp().run()