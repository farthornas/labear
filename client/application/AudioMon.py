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
import time

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
    file_uploaded = False
    files = []
    payload = {}

    new_name = recording.rename_rec()
    files.append(('files', open(new_name, 'rb')))

    payload = recording.get_rec_details()
    
    try:
    
        resp = requests.post(url=url, files=files, data=payload)

        response, file_uploaded = resp.json(), True
        recording.clean_up()
    except ValueError as err:
        print(f"Response from API missing: {err}")
        response, file_uploaded =  err, False
    except requests.exceptions.ConnectionError as con_err:
        logger.info(f"Connection error encountered")
        response, file_uploaded = con_err, False
    return response, file_uploaded

def rec_counter(start_time):
    time_passed = time.time() - start_time
    return f"{time_passed:.2f}"

class MenuScreen(Screen):
    pass

class Rec(Screen):
    def __init__(self, **kwargs):
        super(Rec, self).__init__(**kwargs)
        self.has_recording = False
        self.monitor_state = 'Monitor not running'
        self.count = 0
    
    def on_enter(self, *args):
        self.has_recording = False

        self.menu_screen = self.manager.get_screen("menu")
        logger.info('Preparing to learn new sound...')

        if platform == 'android':
            logger.info('Android recorder used')
            self.recorder = MyRecorder()
            
            self.player = MyPlayer()            
            logger.info('Resetting player')

            self.player.reset()
        else:
            logger.info("plyer recorder used")
            self.audio = ObjectProperty()
            self.audio.file_path = REC_DEFAULT_FILE_NAME
        self.update_labels()
        return super().on_enter(*args)
    
    def callback_screen_counter(self, *largs):
        time_recorded = rec_counter(self.rec_start)
        if self.count >= 12:
            self.record_button.text = f"* {str(time_recorded)}"
            self.count = 0
        elif self.count == 0:
            self.record_button.text = f"* {str(time_recorded)}"
        else:
            self.record_button.text = f"  {str(time_recorded)}"
        self.count += 1


    def record(self):
        logger.info('Recorder button engaged')
        if platform == "android":
            recorder = self.recorder
            #path = recorder.get_output_file()
            state = recorder.get_state()
        else:
            recorder = self.audio
            path = recorder.file_path
            state = self.audio.state

        if state == 'recording':
            logger.info('Stop button pressed')
            logger.info('Recording stopping')
            
            self.recorder.stop()
            self.event_timer.cancel()
            self.has_recording = True
            self.recording = Recording(audio_file=self.recorder, user_id=self.menu_screen.ids["text_user"].text, class_id=self.ids['text_app'].text, file_type=REC_FILE_EXT)
        elif state == 'reset': # Recorder has stopped and user presses button to reset
            logger.info(f'Reset button pressed')
            self.clean_up()
        else:
            logger.info(f'Recorder state unset')
            logger.info(f'Recorder setting up')

            self.recorder.reset()
            self.recorder.set_output_file(REC_DEFAULT_FILE_NAME)
            self.recorder.prepare()
            self.recorder.start()
            self.rec_start = time.time()
            self.record_button = self.ids['record_button']
            self.event_timer = Clock.schedule_interval(partial(self.callback_screen_counter), 0.1)


        self.upload_state = 'Audio Not Uploaded'
        self.update_labels() 

    def playback(self):
        logger.info('Sound Playback pressed')
        state_rec = self.recorder.get_state()
        state_player = self.player.get_state()
        logger.info(f'Player state is {state_player}')


        if self.has_recording == True and state_rec == 'reset':
            if state_player == 'playing':
                logger.info('Stop playing recording')
                self.player.stop()
            else:
                logger.info('Play recording')
                logger.info(f'Player state is: {state_player}')
                logger.info('Resetting player')
                self.player.reset()
                self.player.set_input_source(str(self.recorder.get_output_file()))
                self.player.prepare()
                self.player.play()
        self.update_labels()
    
    def upload(self):
        state = self.recorder.get_state()
        logger.info(f"Attempt upload...")
            
        if self.has_recording == True and state == 'reset':
            logger.info(f"Recording is ready to be uploaded")

            logger.info(f"Record details: {self.recording.get_rec_details()}")
            response, file_uploaded = upload_file(self.recording, URL_LEARN, app_name=self.ids['text_app'].text, test='test')

            if file_uploaded:
                logger.info(f"Uploaded: {self.recording.get_rec_details()}")
                self.upload_state = 'upload_complete'
                self.clean_up()
            else:
                logger.info(f"Recording not uploaded!")
                self.upload_state = 'upload_fail'

            logger.info(f"Response: {response}")
        self.update_labels()
    
    def clean_up(self):
        logger.info(f"Cleanup recording")
        logger.info(f'Resetting recorder and preparing for new recording')
        
        self.recorder.reset()
        self.recording.clean_up()
        self.recorder.set_output_file(REC_DEFAULT_FILE_NAME)
        self.recorder.prepare()
        self.has_recording = False
        self.count = 0
        
    def update_labels(self):
        record_button = self.ids['record_button']
        play_button = self.ids['play_button']
        upload_button = self.ids['upload_button']
        state_label = self.ids['state']
        upload_state = self.ids['upload_state_label']
        text_app = self.ids['text_app']

        rec_state = self.recorder.get_state()
        play_state = self.player.get_state()

        play_button.disabled  = not self.has_recording
        upload_button.disabled  = not self.has_recording

        state_label.text = "Recorder State: " + rec_state

        if rec_state == 'ready':
            record_button.text = 'RECORD'
            play_button.text = 'PLAY AUDIO'
            record_button.disabled = False
            upload_button.disabled = True
            text_app.disabled = False
        
        elif rec_state == 'recording':
            record_button.text = 'RECORD'
            upload_button.disabled = True
            play_button.disabled = True
            text_app.disabled = True
            upload_state.text = 'Audio Not Uploaded'
        
        elif rec_state =='reset':
            record_button.text = 'RESET'
            play_button.text = 'PLAY AUDIO'
            record_button.disabled = False
            text_app.disabled = False
        else:
            record_button.disabled = False

        if play_state == 'playing':
            play_button.text = 'STOP AUDIO'
            record_button.disabled = True
            upload_button.disabled = True
            text_app.disabled = True

        if play_state == 'stopped':
            play_button.text = 'PLAY AUDIO'
            record_button.disabled = False
        
        if self.upload_state == 'upload_complete':
            upload_button.disabled = True
            upload_state.text = 'Audio Uploaded'
        elif self.upload_state == 'upload_fail':
            upload_button.disabled = False
            upload_state.text = 'Audio Upload Fail, pls retry!'
    has_recording = False
    upload_state = 'Audio Not Uploaded'

    
class Monitor(Screen):
    def __init__(self, **kwargs):
        super(Monitor, self).__init__(**kwargs)
        self.monitoring = False
        self.monitor_state = 'Not monitoring'
        self.upload_tries = 0

    
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
        response, file_uploaded = upload_file(self.recording, URL_MON)
        if not file_uploaded and self.upload_tries < 1:
            logger.info(f"Recording not uploaded, retrying once")
            self.event_upload = Clock.schedule_once(partial(self.callback_upload), 3)
            self.upload_tries += 1
            self.upload_state = 'upload_fail'
            
        else:
            #logger.info(f"Uploaded: {self.recording.get_rec_details()}")
            self.upload_state = 'upload_complete'
            self.has_recording = False
            self.recorder.reset()
            self.recorder.prepare()
            self.player.release()
            logger.info(f"Response: {response}")
        self.update_labels()


        logger.info(f"Upload: {self.recording.get_rec_details()}")

    def callback_monitor(self, *largs):
        self.recorder.start()
        self.event_upload = Clock.schedule_once(partial(self.callback_upload), 5)

    def monitor(self):
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