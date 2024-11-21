import pyaudio
import wave
import argparse
import requests
import time 
import os
import sys
import sounddevice
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = "pi.log"
LOG_SIZE = 1048576
LOG_BACKUP_COUNT = 3

def setup_size_based_logger(log_file, max_bytes, backup_count):
    """
    Sets up a logger that rolls over when the log file reaches a specified size.
    
    :param log_file: Path to the log file.
    :param max_bytes: Maximum file size in bytes before rollover.
    :param backup_count: Number of backup files to keep.
    :return: Configured logger.
    """
    logger = logging.getLogger("pi_logger")
    logger.setLevel(logging.DEBUG)

    # Configure the RotatingFileHandler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

logger = setup_size_based_logger(LOG_FILE, max_bytes=LOG_SIZE, backup_count=LOG_BACKUP_COUNT)



class RunFunctionAndExit(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logger.info("Request to show device input info...")
        # Call your function here
        list_audio_devices()
        logger.info("Program will now exit")

        sys.exit(0)  # Exit immediately


def list_audio_devices():
    print(sounddevice.query_devices())

def record_audio(output_filename, record_seconds, channels, rate, chunk):
    # Initialize pyaudio
    audio = pyaudio.PyAudio()
    # Open stream
    stream = audio.open(format=pyaudio.paInt16, channels=1,
                        rate=48000, input=True,
                        output=False,
                        frames_per_buffer=512,
                        input_device_index=1)

    logger.info(f"Recording for {record_seconds} seconds...")

    frames = []  # Store audio frames

    # Record for the specified number of seconds
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    logger.info("Recording finished.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    waveFile = wave.open(output_filename, 'wb')
    waveFile.setnchannels(channels)
    waveFile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    waveFile.setframerate(rate)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    logger.info(f"Recording saved as {output_filename}")

def upload_file(file_path, server_url, data):
    """Upload the .wav file to the server"""
    files = []
    with open(file_path, 'rb') as file:
        #files = {'file': file}
        files.append(('files', file))
        try:
            response = requests.post(server_url, files=files, data=data)
            if response.status_code == 200:
                logger.info(f"File {file_path} uploaded successfully.")
            else:
                logger.warning(f"Failed to upload {file_path}. Status Code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error occurred while uploading file: {str(e)}")

def main():
    # Initialize argument parser
    
    parser = argparse.ArgumentParser(description="Audio Recorder with Periodic Uploads")
    
    # Add arguments for customization
    parser.add_argument('-ld', "--listdevices", action=RunFunctionAndExit, nargs=0, 
                        help="List audio devices and exit immediately.")
    parser.add_argument("-o", "--output", type=str, default="output",
                        help="Output WAV file name (default: output)")
    parser.add_argument("-d", "--duration", type=int, default=5,
                        help="Duration of recording in seconds (default: 5 seconds)")
    parser.add_argument("-c", "--channels", type=int, default=1,
                        help="Number of audio channels (default: 1 for mono)")
    parser.add_argument("-r", "--rate", type=int, default=44100,
                        help="Sample rate (default: 44100 Hz)")
    parser.add_argument("-k", "--chunk", type=int, default=1024,
                        help="Chunk size (default: 1024)")
    parser.add_argument("-s", "--server", type=str, default= "https://albinai.fly.dev",
                        help="Server URL for file upload")
    parser.add_argument("-u", "--user", type=str, required=True,
                        help="User for the file to be associated with")
    parser.add_argument("-i", "--interval", type=int, default=10,
                        help="Interval between recordings in seconds (default: 10 seconds)")
    parser.add_argument("-l", "--learn", type=int, default=10,
                        help="Interval between recordings in seconds (default: 10 seconds)")
    parser.add_argument("-m", "--mode", type=str, choices=["learn", "monitor"], required=True,
                        help="Mode of operation: 'learn' or 'monitor'")
 
    

    # Parse arguments
    args = parser.parse_args()

    while True:
        # Generate a new output filename based on timestamp
        timestamp = round(time.time() * 1000)
        #output_filename = f"{timestamp}_{args.output}"  
        output_filename = f"{args.user}_{args.output}_{timestamp}.wav"

        # Record the audio
        record_audio(output_filename, args.duration, args.channels, args.rate, args.chunk)

        # Upload the file to the server
        server_redir_mode = f"{args.server}/{args.mode}"
        rec_data = {"user_id": args.user, "class_id": args.output, "time_stamp": timestamp}
        upload_file(output_filename, server_redir_mode, rec_data)

        # Optionally delete the file after upload
        if os.path.exists(output_filename):
            os.remove(output_filename)
            logger.info(f"Deleted {output_filename} after upload.")

        # Wait for the specified interval before the next recording
        time.sleep(args.interval)



if __name__ == "__main__":
    main()
