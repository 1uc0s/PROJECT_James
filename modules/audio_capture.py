# modules/audio_capture.py
import os
import wave  # Built-in wave module, not an external package
import pyaudio
import time
from datetime import datetime
import threading
import numpy as np
import sys

from config import AUDIO_DIR, CHANNELS, RATE, CHUNK, SILENCE_THRESHOLD, SILENCE_DURATION

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.start_time = None
        self.filename = None
        self.thread = None
        
        # Create audio directory if it doesn't exist
        os.makedirs(AUDIO_DIR, exist_ok=True)
    
    def start_recording(self):
        """Start recording audio in a separate thread"""
        if self.recording:
            print("Recording is already in progress")
            return
        
        self.recording = True
        self.start_time = datetime.now()
        self.filename = os.path.join(AUDIO_DIR, f"lab_session_{self.start_time.strftime('%Y%m%d_%H%M%S')}.wav")
        self.frames = []
        
        self.thread = threading.Thread(target=self._record)
        self.thread.start()
        
        print(f"Recording started... Press Ctrl+C to stop.")
    
    def stop_recording(self):
        """Stop the recording and save the audio file"""
        if not self.recording:
            print("No recording in progress")
            return
        
        self.recording = False
        if self.thread:
            self.thread.join()
        
        if self.frames:
            self._save_audio()
            print(f"Recording saved to {self.filename}")
            return self.filename
        else:
            print("No audio recorded")
            return None
    
    def _record(self):
        """Record audio until stopped or silence detected"""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        silence_counter = 0
        
        try:
            while self.recording:
                data = stream.read(CHUNK)
                self.frames.append(data)
                
                # Optional: Detect extended silence to auto-stop
                audio_data = np.frombuffer(data, dtype=np.int16)
                if np.abs(audio_data).mean() < SILENCE_THRESHOLD:
                    silence_counter += 1
                else:
                    silence_counter = 0
                
                # Stop after SILENCE_DURATION seconds of silence
                if silence_counter > (RATE / CHUNK) * SILENCE_DURATION:
                    print("Extended silence detected, stopping recording...")
                    self.recording = False
                    break
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            stream.stop_stream()
            stream.close()
    
    def _save_audio(self):
        """Save recorded audio to a WAV file"""
        if not self.frames:
            return
        
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
    
    def __del__(self):
        """Clean up resources"""
        self.audio.terminate()


# Simple command-line test
if __name__ == "__main__":
    recorder = AudioRecorder()
    
    try:
        recorder.start_recording()
        # Record for 30 seconds or until Ctrl+C
        time.sleep(30)
    except KeyboardInterrupt:
        print("\nStopping recording...")
    finally:
        audio_file = recorder.stop_recording()
        if audio_file:
            print(f"Recording saved to: {audio_file}")