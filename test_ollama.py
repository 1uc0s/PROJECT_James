#!/usr/bin/env python
# test_ollama.py
import requests
import json
import sys

def test_ollama_connection():
    """Test connection to Ollama API"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully connected to Ollama")
            
            if "models" in data:
                print("\nAvailable models:")
                for model in data["models"]:
                    print(f"  - {model['name']}")
            return True
        else:
            print(f"❌ Failed to connect to Ollama: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print("\nMake sure Ollama is running with 'ollama serve' in another terminal")
        return False

def test_model_generation(model_name):
    """Test generation with a specific model"""
    prompt = "Explain what a lab book is in one paragraph:"
    
    try:
        print(f"\nTesting generation with model '{model_name}'...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Generation successful")
            print("\nGenerated text:")
            print(f"\"{result.get('response', '').strip()}\"")
            return True
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return False

if __name__ == "__main__":
    if test_ollama_connection():
        if len(sys.argv) > 1:
            model_name = sys.argv[1]
        else:
            model_name = "llama3.2"  # Default model to test
        
        test_model_generation(model_name)