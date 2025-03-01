# modules/audio_capture.py
import os
import wave
import pyaudio
import time
import numpy as np
import threading
import tempfile
from datetime import datetime
import sounddevice as sd

from config import AUDIO_DIR, CHANNELS, RATE, CHUNK, SILENCE_THRESHOLD, SILENCE_DURATION

class AudioRecorder:
    def __init__(self, noise_filtering=True, voice_activity_detection=True):
        """Initialize audio recorder with optional noise filtering"""
        self.recording = False
        self.paused = False
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.start_time = None
        self.pause_time = None
        self.filename = None
        self.thread = None
        self.last_recording = None
        
        # Noise filtering and VAD settings
        self.noise_filtering = noise_filtering
        self.voice_activity_detection = voice_activity_detection
        self.noise_profile = None
        self.vad_threshold = 300  # Adjustable threshold for voice activity detection
        self.min_voice_frames = int(0.1 * RATE / CHUNK)  # 100ms of voice to start recording
        self.voice_frames_count = 0
        self.silence_frames_count = 0
        
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
        
        # If noise filtering is enabled, perform noise profiling
        if self.noise_filtering:
            self._calibrate_noise()
        
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
    
    def _calibrate_noise(self):
        """Record ambient noise for a short period to build a noise profile"""
        print("Calibrating noise profile (stay silent for 2 seconds)...")
        
        # Record 2 seconds of ambient noise
        duration = 2  # seconds
        noise_data = sd.rec(int(duration * RATE), samplerate=RATE, channels=CHANNELS, dtype='int16')
        sd.wait()
        
        # Calculate noise profile (simple mean and standard deviation)
        if noise_data.size > 0:
            self.noise_profile = {
                'mean': np.mean(noise_data),
                'std': np.std(noise_data),
                'threshold': np.std(noise_data) * 2.5  # Adjustable factor
            }
            print(f"Noise profile calibrated: mean={self.noise_profile['mean']:.2f}, threshold={self.noise_profile['threshold']:.2f}")
        else:
            print("Failed to calibrate noise profile")
            self.noise_profile = None
    
    def _filter_noise(self, audio_data):
        """Apply simple noise filtering using the noise profile"""
        if self.noise_profile is None:
            return audio_data
            
        # Convert to numpy array if it's not already
        data_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Simple noise gate: anything below threshold becomes silent
        threshold = self.noise_profile['threshold']
        mask = np.abs(data_array) <= threshold
        filtered_data = data_array.copy()
        filtered_data[mask] = 0
        
        return filtered_data.tobytes()
    
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
        voice_activity = False
        
        try:
            while self.recording:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                data = stream.read(CHUNK)
                
                # Apply noise filtering if enabled
                if self.noise_filtering:
                    data = self._filter_noise(data)
                
                # Voice Activity Detection if enabled
                if self.voice_activity_detection:
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.abs(audio_data).mean()
                    
                    if volume > self.vad_threshold:
                        self.voice_frames_count += 1
                        self.silence_frames_count = 0
                        
                        # Transition to voice activity if enough voice frames
                        if not voice_activity and self.voice_frames_count >= self.min_voice_frames:
                            voice_activity = True
                            print("Voice detected, recording...")
                    else:
                        self.silence_frames_count += 1
                        self.voice_frames_count = 0
                        
                        # If we've had silence for long enough, potentially stop voice activity
                        silence_duration = self.silence_frames_count * CHUNK / RATE
                        if voice_activity and silence_duration > SILENCE_DURATION:
                            voice_activity = False
                            print("Voice ended, waiting for next speech...")
                    
                    # Only save frames if we're in voice activity mode or not using VAD
                    if voice_activity or not self.voice_activity_detection:
                        self.frames.append(data)
                else:
                    # Without VAD, just save all frames
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
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Test audio recorder")
    parser.add_argument("--noise-filter", action="store_true", help="Enable noise filtering")
    parser.add_argument("--vad", action="store_true", help="Enable voice activity detection")
    args = parser.parse_args()
    
    recorder = AudioRecorder(noise_filtering=args.noise_filter, voice_activity_detection=args.vad)
    
    try:
        print("Recording with Ctrl+C to stop...")
        recorder.start_recording()
        time.sleep(5)
        print("Recording paused for demonstration")
        recorder.pause_recording()
        time.sleep(2)
        print("Recording resumed")
        recorder.resume_recording()
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping recording...")
    finally:
        audio_file = recorder.stop_recording()
        if audio_file:
            print(f"Recording saved to: {audio_file}")