# modules/llm_interface.py
import os
import json
import requests
from datetime import datetime
import re

from config import LLM_MODEL_PATH, LLM_CONTEXT_SIZE, LLM_TEMPERATURE, LLM_MAX_TOKENS, LAB_BOOK_PROMPT, IMAGE_ANALYSIS_PROMPT

class LLMInterface:
    def __init__(self, model_path=None):
        """Initialize the LLM interface with support for Ollama"""
        self.model_path = model_path or LLM_MODEL_PATH
        self.use_ollama = False
        self.ollama_model = None
        self.llm = None  # Initialize to None for all cases
        
        # Check if we're using Ollama
        if self.model_path and "ollama:" in self.model_path:
            self.ollama_model = self.model_path.split("ollama:")[1]
            self.use_ollama = True
            print(f"Using Ollama with model: {self.ollama_model}")
            
            # Test Ollama availability
            try:
                response = requests.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    available_models = []
                    for model in models:
                        name = model["name"]
                        # Remove tags like ":latest" for comparison
                        base_name = name.split(":")[0] if ":" in name else name
                        available_models.append(name)
                        
                        # Check if our requested model matches (ignoring tags)
                        if (self.ollama_model == name or 
                            self.ollama_model == base_name):
                            self.ollama_model = name  # Use the full name including tag
                            print(f"Ollama model '{name}' is available")
                            return
                        
                    print(f"Warning: Model '{self.ollama_model}' not found in Ollama")
                    print(f"Available models: {', '.join(available_models)}")
                    print("Continuing in demo mode")
                    self.use_ollama = False
            except Exception as e:
                print(f"Error connecting to Ollama: {e}")
                print("Make sure Ollama is running (run 'ollama serve' in another terminal)")
                print("Continuing in demo mode")
                self.use_ollama = False
            
            return
            
        # Traditional llama-cpp-python approach as fallback
        if not self.model_path:
            print("Warning: No LLM model path specified. Please set LLM_MODEL_PATH in config.py")
            print("Running in demo mode - responses will be placeholders")
            return
            
        # Check if model file exists for local GGUF models
        if not os.path.exists(self.model_path):
            print(f"Warning: LLM model not found at {self.model_path}")
            print("Running in demo mode - responses will be placeholders")
            return
        
        print(f"Loading LLM model from {self.model_path}...")
        try:
            from llama_cpp import Llama
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=LLM_CONTEXT_SIZE,
                n_threads=os.cpu_count(),
                verbose=False
            )
            print("LLM model loaded successfully")
        except Exception as e:
            print(f"Error loading LLM model: {e}")
            print("Running in demo mode - responses will be placeholders")
    
    def generate_lab_book(self, transcript, custom_template=None):
        """Generate a structured lab book from transcript using the LLM"""
        # Prepare the prompt
        prompt_template = custom_template or LAB_BOOK_PROMPT
        prompt = prompt_template.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            transcript=transcript
        )
        
        # Use Ollama if configured
        if self.use_ollama and self.ollama_model:
            try:
                print(f"Generating lab book content with Ollama ({self.ollama_model})...")
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": LLM_TEMPERATURE,
                            "num_predict": LLM_MAX_TOKENS
                        }
                    }
                )
                
                if response.status_code == 200:
                    generated_text = response.json().get("response", "")
                    return generated_text.strip()
                else:
                    print(f"Error from Ollama API: {response.text}")
                    print("Falling back to demo mode")
                    return self._generate_demo_lab_book(transcript)
                    
            except Exception as e:
                print(f"Error generating with Ollama: {e}")
                print("Falling back to demo mode")
                return self._generate_demo_lab_book(transcript)
        
        # Use llama-cpp-python if available
        if self.llm:
            try:
                print("Generating lab book content...")
                response = self.llm(
                    prompt,
                    max_tokens=LLM_MAX_TOKENS,
                    temperature=LLM_TEMPERATURE,
                    echo=False
                )
                
                # Extract generated text
                generated_text = response["choices"][0]["text"]
                return generated_text.strip()
            
            except Exception as e:
                print(f"Error generating lab book: {e}")
                print("Falling back to demo mode")
                return self._generate_demo_lab_book(transcript)
        
        # If we get here, use demo mode
        print("Using demo mode for lab book generation")
        return self._generate_demo_lab_book(transcript)
    
    def analyze_image(self, image_path, transcript_context=None):
        """Analyze an image (graph, plot, etc.) and generate a description"""
        # Check if image exists
        if not os.path.exists(image_path):
            return "Error: Image file not found"
            
        # This would normally use a multimodal LLM
        # For now, we'll just return a placeholder response
        if self.use_ollama:
            # Ollama doesn't support multimodal yet in this interface
            return f"[Analysis of {os.path.basename(image_path)} - multimodal analysis would be generated here]"
            
        if self.llm:
            return f"[Analysis of {os.path.basename(image_path)} would be generated with the local LLM]"
            
        # Default placeholder
        return f"[Placeholder image analysis for {os.path.basename(image_path)}]"
    
    def _generate_demo_lab_book(self, transcript):
        """Generate a simple demo lab book when no LLM is available"""
        # Extract potential participants (look for names in the transcript)
        participants = set()
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        for match in re.finditer(name_pattern, transcript):
            participants.add(match.group(0))
        
        participants_str = ", ".join(participants) if participants else "Unknown Participants"
        
        # Create a simple structured lab book
        return f"""# Lab Experiment Session

**Date:** {datetime.now().strftime("%Y-%m-%d")}

**Participants:** {participants_str}

## Objectives
[This section would be extracted from the transcript by the LLM]

## Materials and Methods
[This section would be extracted from the transcript by the LLM]

## Procedure
[This section would be extracted from the transcript by the LLM]

## Observations
[This section would be extracted from the transcript by the LLM]

## Results
[This section would be extracted from the transcript by the LLM]

## Analysis
[This section would be extracted from the transcript by the LLM]

## Conclusions
[This section would be extracted from the transcript by the LLM]

## Next Steps
[This section would be extracted from the transcript by the LLM]

---
Note: This is a demo lab book. For full functionality, please ensure Ollama is running with your preferred model.
"""


# Simple command-line test
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LLM interface")
    parser.add_argument("--model", help="Path to the LLM model or 'ollama:model_name'")
    parser.add_argument("--transcript", help="Path to transcript file")
    args = parser.parse_args()
    
    llm = LLMInterface(args.model)
    
    if args.transcript and os.path.exists(args.transcript):
        with open(args.transcript, 'r') as f:
            transcript_text = f.read()
        
        lab_book = llm.generate_lab_book(transcript_text)
        print("\n--- Generated Lab Book ---\n")
        print(lab_book)
    else:
        print("No transcript provided or file not found")