from dataclasses import dataclass, field
from functools import partial
from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
import os
from os import rename
import pandas as pd
import requests
from time import time

#API 
URL = "http://0.0.0.0:8000"
LEARN = '/learn'
MONITOR = '/monitor'
URL_LEARN = URL + LEARN
URL_MON = URL + MONITOR

has_recording = False

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



class MenuScreen(Screen):
    pass


def upload_file(recording, url):
    file_labeled = recording.rename_rec()
    files = [('files', open(file_labeled, 'rb'))]
    payload = recording.get_rec_details()
    resp = requests.post(url=url, files=files, data=payload)
    return resp.json()



class Rec(Screen):
    def __init__(self, **kwargs):
        super(Rec, self).__init__(**kwargs)
        self.has_recording = False
        self.monitor_state = 'Monitor not running'
    
    audio = ObjectProperty()
    def on_enter(self, *args):
        self.update_labels()
        return super().on_enter(*args)

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
            file_Sd = self.audio.file_path.split("file://")[1]
            recording = Recording(audio_file=file_Sd, user_id='test_id', class_id=11)
            resp = upload_file(recording, URL_LEARN)
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

        state = self.audio.state
        play_button.disabled  = not self.has_recording
        upload_button.disabled  = not self.has_recording

        state_label.text = "AudioPlayer State: " + state

        if state == 'ready':
            record_button.text = 'START RECORD'
            play_button.text = 'PLAY AUDIO'
            record_button.disabled = False
        
        if state == 'recording':
            record_button.text = 'STOP RECORD'
            upload_button.disabled = True
            play_button.disabled = True
            upload_state.text = 'Audio Not Uploaded'           

        if state == 'playing':
            play_button.text = 'STOP AUDIO'
            record_button.disabled = True
            upload_button.disabled = True
        
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

    #upload_state = 'Audio Not Uploaded'
        self.monitor_state = 'Not monitoring'
    
    #audio = ObjectProperty()
    #def on_enter(self, *args):
    #    self.update_labels()
    #    return super().on_enter(*args)

    def callback_upload(self, *largs):
        #if self.has_recording == True and state == 'ready':
        self.audio.stop()
        file_Sd = self.audio.file_path.split("file://")[1]
        recording = Recording(audio_file=file_Sd, user_id='test_id', class_id=11)
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
        self.icon = "app_images/icon4.png"
        
        screen = Builder.load_file("AudioMon.kv") 

        return screen


LabearApp().run()