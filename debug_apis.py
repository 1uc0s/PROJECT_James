#!/usr/bin/env python
"""
Debug script to test API connectivity and audio processing
"""
import os
import sys
import requests
import json

def test_openai_api():
    """Test connection to OpenAI API"""
    print("\n--- Testing OpenAI API Connection ---")
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    # Make a simple request to the models endpoint (lightweight call)
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers
        )
        
        if response.status_code == 200:
            models = response.json()["data"]
            print(f"✅ Successfully connected to OpenAI API")
            print(f"Found {len(models)} models. First few models:")
            for model in models[:5]:
                print(f"  - {model['id']}")
            return True
        else:
            print(f"❌ Failed to connect to OpenAI API: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error connecting to OpenAI API: {e}")
        return False

def test_anthropic_api():
    """Test connection to Anthropic API"""
    print("\n--- Testing Anthropic API Connection ---")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return False
    
    # Make a simple request to verify the API key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 10,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": "Say hello"}
        ]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully connected to Anthropic API")
            result = response.json()
            print(f"Response: {result['content'][0]['text']}")
            return True
        else:
            print(f"❌ Failed to connect to Anthropic API: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error connecting to Anthropic API: {e}")
        return False

def test_audio_processing():
    """Test the audio processing capabilities"""
    print("\n--- Testing Audio Processing ---")
    
    # Find a WAV file to test with
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    audio_dir = os.path.join(data_dir, "audio")
    
    if not os.path.exists(audio_dir):
        print(f"Audio directory not found: {audio_dir}")
        return False
    
    # Find WAV files
    wav_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    
    if not wav_files:
        print("No WAV files found in audio directory")
        return False
    
    # Test the first WAV file found
    test_file = os.path.join(audio_dir, wav_files[0])
    print(f"Testing with file: {test_file}")
    
    # Test audio duration function
    print("Testing audio duration:")
    try:
        from utils.helpers import get_audio_duration
        duration = get_audio_duration(test_file)
        print(f"✅ Duration: {duration:.2f} seconds")
    except Exception as e:
        print(f"❌ Error getting audio duration: {e}")
    
    # Try to get basic audio info using wave module
    print("\nBasic audio info:")
    try:
        import wave
        with wave.open(test_file, 'rb') as wf:
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            rate = wf.getframerate()
            frames = wf.getnframes()
            print(f"✅ Channels: {channels}")
            print(f"✅ Sample width: {width} bytes")
            print(f"✅ Sample rate: {rate} Hz")
            print(f"✅ Frames: {frames}")
            print(f"✅ Duration: {frames / rate:.2f} seconds")
    except Exception as e:
        print(f"❌ Error reading WAV file: {e}")
        
        # Try with soundfile if available
        try:
            import soundfile as sf
            info = sf.info(test_file)
            print(f"✅ Using soundfile:")
            print(f"✅ Channels: {info.channels}")
            print(f"✅ Sample rate: {info.samplerate} Hz")
            print(f"✅ Duration: {info.duration:.2f} seconds")
        except ImportError:
            print("❌ soundfile library not available for fallback")
        except Exception as e2:
            print(f"❌ Error with soundfile: {e2}")
    
    return True

if __name__ == "__main__":
    print("=== API and Audio Processing Debug Tool ===")
    
    test_openai_api()
    test_anthropic_api()
    test_audio_processing()
    
    print("\nDebug tests completed")