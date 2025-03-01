# modules/simple_audio.py
import os
import wave
import pyaudio
import time
import threading
from datetime import datetime

from config import AUDIO_DIR, CHANNELS, RATE, CHUNK

class SimpleAudioRecorder:
    """Simple audio recorder without noise filtering or VAD"""
    def __init__(self):
        self.recording = False
        self.paused = False
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.start_time = None
        self.pause_time = None
        self.filename = None
        self.thread = None
        self.last_recording = None
        
        # Create audio directory if it doesn't exist
        os.makedirs(AUDIO_DIR, exist_ok=True)
    
    def start_recording(self):
        """Start recording audio in a separate thread"""
        if self.recording:
            print("Recording is already in progress")
            return
        
        self.recording = True
        self.paused = False
        self.start_time = datetime.now()
        self.filename = os.path.join(AUDIO_DIR, f"lab_session_{self.start_time.strftime('%Y%m%d_%H%M%S')}.wav")
        self.frames = []
        
        self.thread = threading.Thread(target=self._record)
        self.thread.daemon = True
        self.thread.start()
        
        print(f"Recording started... Use keyboard shortcuts to control recording.")
        return self.filename
    
    def pause_recording(self):
        """Pause the recording"""
        if not self.recording or self.paused:
            return
        
        self.paused = True
        self.pause_time = datetime.now()
        print(f"Recording paused at {self.pause_time.strftime('%H:%M:%S')}")
    
    def resume_recording(self):
        """Resume a paused recording"""
        if not self.recording or not self.paused:
            return
        
        self.paused = False
        pause_duration = (datetime.now() - self.pause_time).total_seconds()
        print(f"Recording resumed after {pause_duration:.1f}s pause")
    
    def stop_recording(self):
        """Stop the recording and save the audio file"""
        if not self.recording:
            print("No recording in progress")
            return None
        
        self.recording = False
        self.paused = False
        
        if self.thread:
            self.thread.join()
        
        if self.frames:
            self._save_audio()
            print(f"Recording saved to {self.filename}")
            self.last_recording = self.filename
            return self.filename
        else:
            print("No audio recorded")
            return None
    
    def save_current_segment(self):
        """Save the current segment without stopping recording"""
        if not self.recording or not self.frames:
            return None
            
        # Create a temporary pause
        was_paused = self.paused
        if not was_paused:
            self.pause_recording()
        
        # Make a copy of current frames
        current_frames = self.frames.copy()
        
        # Create a temporary file
        temp_filename = os.path.join(AUDIO_DIR, f"temp_segment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        
        # Save the current frames
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(current_frames))
        wf.close()
        
        # Resume if it wasn't paused
        if not was_paused:
            self.resume_recording()
        
        return temp_filename
    
    def get_last_recording(self):
        """Get the path to the last recorded file"""
        return self.last_recording
    
    def _record(self):
        """Record audio until stopped"""
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            while self.recording:
                if self.paused:
                    time.sleep(0.1)
                    continue
                    
                try:
                    data = stream.read(CHUNK)
                    self.frames.append(data)
                except Exception as e:
                    print(f"Error reading from stream: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
    
    def _save_audio(self):
        """Save recorded audio to a WAV file"""
        if not self.frames:
            return
        
        try:
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
        except Exception as e:
            print(f"Error saving audio: {e}")
    
    def __del__(self):
        """Clean up resources"""
        try:
            self.audio.terminate()
        except:
            pass