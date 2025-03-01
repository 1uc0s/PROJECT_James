#!/usr/bin/env python
"""
Debug script to test API connectivity and audio processing
"""
import os
import sys
import requests
import json
from datetime import datetime

# Import config to access the correct file structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, LAB_CYCLES_DIR, TEMP_DIR, get_cycle_paths

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

def test_huggingface_api():
    """Test connection to HuggingFace API"""
    print("\n--- Testing HuggingFace API Connection ---")
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        print("Error: HF_TOKEN environment variable not set.")
        print("Set it with: export HF_TOKEN='your-token-here'")
        return False
    
    # Make a simple request to verify the token
    headers = {
        "Authorization": f"Bearer {hf_token}"
    }
    
    try:
        response = requests.get(
            "https://huggingface.co/api/models",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully connected to HuggingFace API")
            models = response.json()
            print(f"Found {len(models)} public models.")
            print("Your HuggingFace token is valid and working.")
            return True
        else:
            print(f"❌ Failed to connect to HuggingFace API: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error connecting to HuggingFace API: {e}")
        return False

def test_audio_processing():
    """Test the audio processing capabilities"""
    print("\n--- Testing Audio Processing ---")
    
    # Find all potential audio directories in the updated structure
    audio_dirs = []
    
    # Check temp audio dir
    temp_audio_dir = os.path.join(TEMP_DIR, "audio")
    if os.path.exists(temp_audio_dir):
        audio_dirs.append(temp_audio_dir)
        
    # Check lab cycle audio dirs
    if os.path.exists(LAB_CYCLES_DIR):
        for cycle_dir in os.listdir(LAB_CYCLES_DIR):
            cycle_path = os.path.join(LAB_CYCLES_DIR, cycle_dir)
            if os.path.isdir(cycle_path):
                cycle_audio_dir = os.path.join(cycle_path, "audio")
                if os.path.exists(cycle_audio_dir):
                    audio_dirs.append(cycle_audio_dir)
    
    # Check each audio directory for WAV files
    for audio_dir in audio_dirs:
        wav_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
        
        if wav_files:
            # Test with the first WAV file found
            test_file = os.path.join(audio_dir, wav_files[0])
            print(f"Testing with file: {test_file} (from {audio_dir})")
            
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
            
            # Found a test file - no need to check other directories
            return True
    
    print("No WAV files found in any audio directory")
    return False

def test_file_structure():
    """Test the file structure of the project"""
    print("\n--- Testing File Structure ---")
    
    # Check main directories
    print("Checking main directories:")
    directories = {
        "DATA_DIR": DATA_DIR,
        "LAB_CYCLES_DIR": LAB_CYCLES_DIR,
        "TEMP_DIR": TEMP_DIR
    }
    
    for name, directory in directories.items():
        if os.path.exists(directory):
            print(f"✅ {name}: {directory} exists")
        else:
            print(f"❌ {name}: {directory} does not exist")
    
    # Check lab cycles
    print("\nChecking lab cycles:")
    if os.path.exists(LAB_CYCLES_DIR):
        cycles = [d for d in os.listdir(LAB_CYCLES_DIR) if os.path.isdir(os.path.join(LAB_CYCLES_DIR, d))]
        if cycles:
            print(f"Found {len(cycles)} lab cycles: {', '.join(cycles)}")
            
            # Check structure of first cycle
            first_cycle = cycles[0]
            paths = get_cycle_paths(first_cycle)
            
            print(f"\nChecking structure of cycle '{first_cycle}':")
            for name, path in paths.items():
                if os.path.exists(path):
                    items = os.listdir(path)
                    print(f"✅ {name}: {path} exists with {len(items)} items")
                else:
                    print(f"❌ {name}: {path} does not exist")
        else:
            print("No lab cycles found")
    else:
        print(f"Lab cycles directory doesn't exist: {LAB_CYCLES_DIR}")
    
    return True

def test_environment_variables():
    """Test environment variables needed for the application"""
    print("\n--- Testing Environment Variables ---")
    
    env_vars = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "HF_TOKEN": os.environ.get("HF_TOKEN")
    }
    
    for name, value in env_vars.items():
        if value:
            masked_value = value[:4] + "*" * (len(value) - 4)
            print(f"✅ {name} is set: {masked_value}")
        else:
            print(f"❌ {name} is not set")
    
    return True

if __name__ == "__main__":
    print("=== API and Audio Processing Debug Tool ===")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test environment variables first
    test_environment_variables()
    
    # Test file structure
    test_file_structure()
    
    # Test APIs
    test_openai_api()
    test_anthropic_api()
    test_huggingface_api()
    
    # Test audio processing
    test_audio_processing()
    
    print("\nDebug tests completed")