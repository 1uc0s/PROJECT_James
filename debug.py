#!/usr/bin/env python
"""
Debug script to isolate components causing segmentation fault
"""
import os
import sys
import time
import argparse

def test_audio_basic():
    """Test basic audio recording without noise filtering or VAD"""
    print("\n--- Testing Basic Audio Recording ---")
    try:
        import pyaudio
        import wave
        
        print("PyAudio imported successfully")
        
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        print("PyAudio initialized")
        
        # Get device info
        device_count = audio.get_device_count()
        print(f"Found {device_count} audio devices")
        
        # Get default input device info
        default_input = audio.get_default_input_device_info()
        print(f"Default input device: {default_input['name']}")
        
        # Try to open a stream
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )
        
        print("Audio stream opened successfully")
        
        # Read a small chunk
        data = stream.read(1024)
        print(f"Read {len(data)} bytes from audio stream")
        
        # Clean up
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("Audio test completed successfully")
        return True
    except Exception as e:
        print(f"Error in audio test: {e}")
        return False

def test_sounddevice():
    """Test sounddevice module"""
    print("\n--- Testing sounddevice Module ---")
    try:
        import sounddevice as sd
        import numpy as np
        
        print("sounddevice imported successfully")
        
        # Get device info
        devices = sd.query_devices()
        print(f"Found {len(devices)} audio devices via sounddevice")
        
        # Try to record a small sample
        duration = 1  # seconds
        fs = 44100  # Sample rate
        print("Recording 1 second of audio...")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished
        
        print(f"Recorded array shape: {recording.shape}")
        print("sounddevice test completed successfully")
        return True
    except Exception as e:
        print(f"Error in sounddevice test: {e}")
        return False

def test_noise_filtering():
    """Test noise filtering components"""
    print("\n--- Testing Noise Filtering ---")
    try:
        import numpy as np
        import sounddevice as sd
        
        # Record sample background noise
        print("Recording 1 second of background noise...")
        duration = 1  # seconds
        fs = 44100  # Sample rate
        noise_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        
        # Calculate noise profile
        noise_mean = np.mean(noise_data)
        noise_std = np.std(noise_data)
        threshold = noise_std * 2.5
        
        print(f"Noise profile: mean={noise_mean:.2f}, threshold={threshold:.2f}")
        
        # Test filter application
        data_array = np.random.normal(noise_mean, noise_std, 44100).astype(np.int16)
        mask = np.abs(data_array) <= threshold
        filtered_data = data_array.copy()
        filtered_data[mask] = 0
        
        print(f"Applied filter: zeroed {np.sum(mask)} of {len(mask)} samples")
        print("Noise filtering test completed successfully")
        return True
    except Exception as e:
        print(f"Error in noise filtering test: {e}")
        return False

def test_keyboard():
    """Test keyboard module"""
    print("\n--- Testing Keyboard Module ---")
    try:
        import keyboard
        
        print("keyboard module imported successfully")
        
        # Register a test hotkey for 3 seconds
        print("Testing keyboard hotkey registration...")
        keyboard.add_hotkey('ctrl+t', lambda: print("Test hotkey triggered"))
        
        print("Press Ctrl+T within 3 seconds to test...")
        time.sleep(3)
        
        # Unregister the hotkey
        keyboard.unhook_all()
        
        print("Keyboard test completed successfully")
        return True
    except Exception as e:
        print(f"Error in keyboard test: {e}")
        return False

def test_whisper():
    """Test Whisper import"""
    print("\n--- Testing Whisper Import ---")
    try:
        import whisper
        
        print("whisper imported successfully")
        print("Note: Not loading model to save time")
        
        return True
    except Exception as e:
        print(f"Error importing whisper: {e}")
        return False

def test_ollama():
    """Test Ollama connection"""
    print("\n--- Testing Ollama Connection ---")
    try:
        import requests
        
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            data = response.json()
            print("Successfully connected to Ollama")
            
            if "models" in data:
                models = data.get("models", [])
                print(f"Found {len(models)} models")
                for model in models:
                    print(f"  - {model['name']}")
        else:
            print(f"Failed to connect to Ollama: {response.status_code}")
            print(response.text)
            
        return True
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Debug Lab Book Generator components")
    parser.add_argument("--all", action="store_true", help="Test all components")
    parser.add_argument("--audio", action="store_true", help="Test basic audio")
    parser.add_argument("--sounddevice", action="store_true", help="Test sounddevice")
    parser.add_argument("--noise", action="store_true", help="Test noise filtering")
    parser.add_argument("--keyboard", action="store_true", help="Test keyboard module")
    parser.add_argument("--whisper", action="store_true", help="Test whisper import")
    parser.add_argument("--ollama", action="store_true", help="Test Ollama connection")
    
    args = parser.parse_args()
    
    # If no specific tests are selected, test everything
    if not (args.audio or args.sounddevice or args.noise or args.keyboard or 
            args.whisper or args.ollama):
        args.all = True
    
    if args.all or args.audio:
        test_audio_basic()
    
    if args.all or args.sounddevice:
        test_sounddevice()
    
    if args.all or args.noise:
        test_noise_filtering()
    
    if args.all or args.keyboard:
        test_keyboard()
    
    if args.all or args.whisper:
        test_whisper()
    
    if args.all or args.ollama:
        test_ollama()
        
    print("\nDebug tests completed")

if __name__ == "__main__":
    main()