from dataclasses import dataclass, field
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import ObjectProperty
from os import rename
import requests
from time import time

Builder.load_file("AudioRec.kv") 

URL = 'http://127.0.0.1:8000/submit'
class AudioInterface(MDBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_labels()
    audio = ObjectProperty()

    has_recording = False
    upload_state = 'Audio Not Uploaded'


    def start_recording(self):
        state = self.audio.state
        if state == 'ready':
            self.audio.start()
        if state == 'recording':
            self.audio.stop()
            self.has_recording = True
        self.upload_state = 'Audio Not Uploaded'
        self.update_labels() 
    
    def start_playing(self):
        
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
            recording = Recording(user_id='test_id', class_id=11)
            file_Sd = self.audio.file_path.split("file://")[1]
            file_labeled = recording.rename_rec(file_Sd)
            files = [('files', open(file_labeled, 'rb'))]
            payload = recording.get_details()
            resp = requests.post(url=URL, files=files, data=payload)
            print(resp.json())
            self.upload_state = 'upload_complete'
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

def generate_timestamp() -> int:
      return round(time() * 1000)

@dataclass
class Recording:
      user_id: str
      class_id: int
      timestamp: int = field(init=False, default_factory=generate_timestamp)
      file_label: str = field(init=False)

      def __post_init__(self) -> None:
            self.file_label = f"{self.user_id}_{self.class_id}_{self.timestamp}.wav"
      
      def rename_rec(self, rec):
            rename(rec, self.file_label)
            return self.file_label
      
      def get_details(self):
          return {"user_id": self.user_id, "class_id": self.class_id, "time_stamp": self.timestamp}


class AudioApp(MDApp):

    def build(self):
        return AudioInterface()
        
if __name__ == '__main__':
    AudioApp().run() 
