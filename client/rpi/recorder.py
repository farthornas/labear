import pyaudio
import wave
import argparse
import requests
import time 
import os

def record_audio(output_filename, record_seconds, channels, rate, chunk):
    # Initialize pyaudio
    audio = pyaudio.PyAudio()

    # Open stream
    stream = audio.open(format=pyaudio.paInt16, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk)

    print(f"Recording for {record_seconds} seconds...")

    frames = []  # Store audio frames

    # Record for the specified number of seconds
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

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

    print(f"Recording saved as {output_filename}")

def upload_file(file_path, server_url, data):
    """Upload the .wav file to the server"""
    files = []
    with open(file_path, 'rb') as file:
        #files = {'file': file}
        files.append(('files', file))
        try:
            response = requests.post(server_url, files=files, data=data)
            if response.status_code == 200:
                print(f"File {file_path} uploaded successfully.")
            else:
                print(f"Failed to upload {file_path}. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error occurred while uploading file: {str(e)}")

def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Audio Recorder with Periodic Uploads")
    
    # Add arguments for customization
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
            print(f"Deleted {output_filename} after upload.")

        # Wait for the specified interval before the next recording
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
