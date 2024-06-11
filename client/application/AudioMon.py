from functools import partial
from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivy.utils import platform
import requests

# API 
URL = 'https://albinai.fly.dev'
# URL = 'http://0.0.0.0:8000'
LEARN = '/learn'
MONITOR = '/monitor'
URL_LEARN = URL + LEARN
URL_MON = URL + MONITOR
TEST_ID = 99

has_recording = False

if platform == 'android':
    from jnius import autoclass
    from application.audio_capture import MyRecorder, Recording, MyPlayer

    Logger = autoclass('java.util.logging.Logger')
    logger = Logger.getLogger('[AlbinEars]')
    logger.info("running on android with [AlbinEars]")
    REC_FILE_EXT = '.m4a'
    REC_DEFAULT_FILE_NAME = 'rec' + REC_FILE_EXT
else:
    from loguru import logger
    from audio_capture import MyRecorder, Recording

    REC_FILE_EXT = '.wav'
    REC_DEFAULT_FILE_NAME = '../rec' + REC_FILE_EXT





def upload_file(recording, url, **kwargs):

    path = recording.get_file_path()
    logger.info(f"Attemping to open recording at {path}")

    files = []
    payload = {}

    new_name = recording.rename_rec()
    files.append(('files', open(new_name, 'rb')))

    payload = recording.get_rec_details()
    
    try:
    
        resp = requests.post(url=url, files=files, data=payload)

        response= resp.json() 
        recording.clean_up()
    except ValueError as err:
        print(f"Response from API missing: {err}")
        response =  err
    except requests.exceptions.ConnectionError as con_err:
        logger.info(f"Connection error encountered")
        response = con_err
    finally:
        recording.clean_up()
    return response

class MenuScreen(Screen):
    pass

class Rec(Screen):
    def __init__(self, **kwargs):
        super(Rec, self).__init__(**kwargs)
        self.has_recording = False
        self.monitor_state = 'Monitor not running'
    
    def on_enter(self, *args):
        self.menu_screen = self.manager.get_screen("menu")
        logger.info('Preparing to learn new sound...')

        if platform == 'android':
            logger.info('Android recorder used')
            self.recorder = MyRecorder()
            self.recorder.set_output_file(REC_DEFAULT_FILE_NAME)
            self.recorder.prepare()
            
            #self.player = MyPlayer(self.recorder.get_output_file())
        else:
            logger.info("plyer recorder used")
            self.audio = ObjectProperty()
            self.audio.file_path = REC_DEFAULT_FILE_NAME
        self.update_labels()
        return super().on_enter(*args)


    def record(self):
        logger.info('Started listening - recording starting')
        if platform == "android":
            recorder = self.recorder
            path = recorder.get_output_file()
            state = recorder.get_state()
        else:
            recorder = self.audio
            path = recorder.file_path
            state = self.audio.state
        logger.info(f"path of recording:{path}")

        #state = self.audio.state
        if state == 'ready':
            self.recorder.start()
            #TODO Implement a timer. 
            #self.event_monitor = Clock.schedule_interval(partial(self.callback_monitor), 0.5)
        if state == 'recording':
            logger.info('Recording stopping')
            self.recorder.stop()
            self.has_recording = True
            path = self.recorder.get_output_file()
            self.recording = Recording(audio_file=self.recorder, user_id=self.menu_screen.ids["text_user"].text, class_id=self.ids['text_app'].text, file_type=REC_FILE_EXT)
            self.player = MyPlayer(path)
        if state == 'reset':
            self.recorder.reset()
            self.recorder.prepare()
        self.upload_state = 'Audio Not Uploaded'
        self.update_labels() 

    def playback(self):
        state = self.recorder.get_state()
        if self.has_recording == True and state == 'reset':
            if state == 'playing':
                self.player.stop()
            else:
                self.player.play()
        self.update_labels()
    
    def upload(self):
        #self.update_labels()
        state = self.recorder.get_state()
        logger.info(f"Attempt upload...")
            
        if self.has_recording == True and state == 'reset':
            logger.info(f"Recording is ready to be uploaded")

            #self.recording = Recording(audio_file=self.recorder, user_id=self.menu_screen.ids["text_user"].text, class_id=self.ids['text_app'].text, file_type=REC_FILE_EXT)
            logger.info(f"Record details: {self.recording.get_rec_details()}")

            resp = upload_file(self.recording, URL_LEARN, app_name=self.ids['text_app'].text, test='test')
            logger.info(f"Uploaded: {self.recording.get_rec_details()}")
            logger.info(f"Response: {resp}")

            self.upload_state = 'upload_complete'
            self.has_recording = False
            self.recorder.reset()
            self.recorder.prepare()
            self.player.release()
        self.update_labels()
    
    def clean_up(self):
        logger.info(f"Cleanup recording and release audio recorder/player")

        self.recording.clean_up()
        self.recorder.release()
        self.player.release()
        self.has_recording = False


    def update_labels(self):
        record_button = self.ids['record_button']
        play_button = self.ids['play_button']
        upload_button = self.ids['upload_button']
        state_label = self.ids['state']
        upload_state = self.ids['upload_state_label']
        text_app = self.ids['text_app']

        #state = self.audio.state
        state = self.recorder.get_state()
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
        
        if state =='reset':
            record_button.text = 'START RECORD'
            play_button.text = 'PLAY AUDIO'
            record_button.disabled = False
            text_app.disabled = False
        
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
        self.menu_screen = self.manager.get_screen("menu")
        logger.info('Preparing for monitoring sound...')

        if platform == 'android':
            logger.info('Android recorder used')
            self.recorder = MyRecorder()
            self.recorder.set_output_file(REC_DEFAULT_FILE_NAME)
            self.recorder.prepare()
        self.update_labels()
        return super().on_enter(*args)

    def callback_upload(self, *largs):
        self.recorder.stop()
        self.recording = Recording(audio_file=self.recorder, user_id=self.menu_screen.ids["text_user"].text, class_id='test_mon', file_type=REC_FILE_EXT)
        resp = upload_file(self.recording, URL_MON)
        logger.info(f"Upload: {self.recording.get_rec_details()}")
        self.recorder.reset()
        self.recorder.prepare()

    def callback_monitor(self, *largs):
        self.recorder.start()
        self.event_upload = Clock.schedule_once(partial(self.callback_upload), 5)

    def monitor(self):
        #state = self.audio.state
        #self.monitoring = True
        self.upload_state = 'Audio Not Uploaded'
        if self.monitoring:
            self.stop_monitor()
        else:
            self.monitoring = True
            self.monitor_state = 'Monitoring'
            self.recorder.start()
            self.event_upload = Clock.schedule_once(partial(self.callback_upload), 5)
            self.event_monitor = Clock.schedule_interval(partial(self.callback_monitor), 20)
        self.update_labels()


    def stop_monitor(self):
        
        if self.monitoring:
            self.monitor_state = 'Not Monitoring'
        self.monitoring = False
        self.recorder.stop()
        self.event_monitor.cancel()
        self.event_upload.cancel()
        self.update_labels()

    def update_labels(self):
        monitor_button = self.ids['monitor_button']
        state_label = self.ids['state']
        upload_state = self.ids['upload_state_label']

        state = self.recorder.get_state()

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
        logger.info("Starting application!")
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.RECORD_AUDIO, Permission.WAKE_LOCK])

    def build(self):
        #screen = Builder.load_string(screen_helper)
        self.icon = "application/app_images/icon7.png"
        screen = Builder.load_file("application/AudioMon.kv") 


        return screen

if __name__ == '__main__':
    LabearApp().run()