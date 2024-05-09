import android
from platform import platform
from application.AudioMon import LabearApp
from jnius import autoclass
Logger = autoclass('java.util.logging.Logger')
mylogger = Logger.getLogger('MyLogger')


if __name__ == "__main__":
 # ... some code
    mylogger.info('Jonas: logger running')
    LabearApp().run()