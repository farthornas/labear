from kivymd.app import MDApp
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
import requests
from eartools.eartools import Recording
from kivy.clock import Clock

has_recording = False

URL = 'http://127.0.0.1:8000/submit'
class MenuScreen(Screen):
    pass


class LearnNew(Screen):
    def __init__(self, **kwargs):
        super(LearnNew, self).__init__(**kwargs)
    has_recording = False
    upload_state = 'Audio Not Uploaded'
    
    audio = ObjectProperty()
    def on_enter(self, *args):
        self.update_labels()
        return super().on_enter(*args)

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
            file_Sd = self.audio.file_path.split("file://")[1]
            recording = Recording(audio_file=file_Sd, user_id='test_id', class_id=11)
            file_labeled = recording.rename_rec()
            files = [('files', open(file_labeled, 'rb'))]
            payload = recording.get_rec_details()
            resp = requests.post(url=URL, files=files, data=payload)
            print(resp.json())
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
    has_recording = False
    monitoring = False

    upload_state = 'Audio Not Uploaded'
    monitor_state = 'Not monitoring'
    
    audio = ObjectProperty()
    def on_enter(self, *args):
        self.update_labels()
        return super().on_enter(*args)

    def start_monitoring(self):
        state = self.audio.state
        self.monitoring = not self.monitoring
        self.upload_state = 'Audio Not Uploaded'
        self.monitor_state = 'Monitoring'
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
sm.add_widget(LearnNew(name='learn'))
sm.add_widget(Monitor(name='monitor'))


class DemoApp(MDApp):

    def build(self):
        #screen = Builder.load_string(screen_helper)
        screen = Builder.load_file("AudioMon.kv") 
        return screen


DemoApp().run()