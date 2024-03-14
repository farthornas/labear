import sys
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

TEST = '/Users/jonas/test/'

#SERVER LOCATIONS
RAW_FILES = '../../data/raw_appliances/'
MON_FILES = '../../data/mon_appliances/'

class MonitorEventHandler(LoggingEventHandler):
    """Logs all the events captured."""

    def __init__(self, logger=None):
        super().__init__()
    
    def on_created(self, event):
        super().on_created(event)

        print("File appeared")

    def on_deleted(self, event):
        super().on_deleted(event)

        print("File deleted")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    event_handler_mon = MonitorEventHandler()
    event_handler_learn = MonitorEventHandler()
    observer = Observer()
    #test_print(event_handler)
    observer.schedule(event_handler_mon, MON_FILES, recursive=True)
    observer.schedule(event_handler_learn, RAW_FILES, recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()