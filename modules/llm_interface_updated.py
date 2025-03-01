# modules/llm_interface_updated.py
import os
import json
import requests
from datetime import datetime
import re

from config import (
    LLM_MODEL_PATH, LLM_CONTEXT_SIZE, LLM_TEMPERATURE, LLM_MAX_TOKENS, 
    LAB_BOOK_PROMPT, IMAGE_ANALYSIS_PROMPT, EXTERNAL_API_KEYS,
    POST_PROCESSING_PROMPT
)

class LLMInterface:
    def __init__(self, model_path=None):
        """Initialize the LLM interface with support for Ollama and external APIs"""
        # Get model path from parameter or config
        self.model_path = model_path or LLM_MODEL_PATH
        self.use_ollama = False
        self.ollama_model = None
        self.llm = None  # Initialize to None for all cases
        
        print(f"Initializing LLM interface with model path: {self.model_path}")
        
        # Check if we're using Ollama
        if self.model_path and isinstance(self.model_path, str) and "ollama:" in self.model_path:
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
        try:
            if not os.path.exists(self.model_path):
                # Try absolute path
                abs_path = os.path.abspath(self.model_path)
                if os.path.exists(abs_path):
                    self.model_path = abs_path
                    print(f"Found model at absolute path: {abs_path}")
                else:
                    # Try relative to the current file
                    rel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", self.model_path)
                    if os.path.exists(rel_path):
                        self.model_path = rel_path
                        print(f"Found model at relative path: {rel_path}")
                    else:
                        print(f"Warning: LLM model not found at any of these locations:")
                        print(f"  - Original path: {self.model_path}")
                        print(f"  - Absolute path: {abs_path}")
                        print(f"  - Relative path: {rel_path}")
                        print("Running in demo mode - responses will be placeholders")
                        return
        except Exception as e:
            print(f"Error checking model path: {e}")
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
            print(f"Details: {str(e)}")
            print("Running in demo mode - responses will be placeholders")
    
    def generate_lab_book(self, transcript, custom_template=None, rag_context=None, 
                         external_comments=None, include_external=True):
        """Generate a structured lab book from transcript using the LLM"""
        # Prepare the prompt
        prompt_template = custom_template or LAB_BOOK_PROMPT
        
        # Add RAG context if available
        context_sections = []
        if rag_context:
            context_sections.append(rag_context)
        
        # Add external comments section if available and requested
        if external_comments and include_external:
            context_sections.append(
                "EXTERNAL COMMENTS (from lab partners/demonstrators):\n\n"
                f"{external_comments}\n\n"
                "Please incorporate relevant information from these external comments "
                "into the appropriate sections of the lab book."
            )
        
        # Assemble full context
        context = "\n\n".join(context_sections)
        
        # Build the prompt with context and transcript
        prompt = prompt_template.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            transcript=transcript,
            context=context if context else "[No additional context available]"
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
    
    def post_process_with_external_api(self, lab_book_content, api_provider="openai", max_tokens=1000):
        """Send the lab book to an external API for analysis and suggestions"""
        print(f"Sending lab book to external API ({api_provider}) for Smart Analysis...")
        
        api_keys = EXTERNAL_API_KEYS.get(api_provider, {})
        if not api_keys or not api_keys.get("api_key"):
            print(f"No API key found for {api_provider}")
            return self._generate_demo_analysis(lab_book_content)
        
        # Format prompt for the post-processing
        analysis_prompt = self._create_post_processing_prompt(lab_book_content)
        
        if api_provider == "openai":
            return self._process_with_openai(analysis_prompt, api_keys, max_tokens)
        elif api_provider == "anthropic":
            return self._process_with_anthropic(analysis_prompt, api_keys, max_tokens)
        else:
            print(f"Unsupported API provider: {api_provider}")
            return self._generate_demo_analysis(lab_book_content)
    
    def _create_post_processing_prompt(self, lab_book_content):
        """Create a prompt for post-processing analysis"""
        # Use the configured post-processing prompt
        return POST_PROCESSING_PROMPT.format(lab_book=lab_book_content)
    
    def _process_with_openai(self, prompt, api_keys, max_tokens):
        """Process content using OpenAI API"""
        try:
            print(f"Making request to OpenAI API with API key: {api_keys.get('api_key')[:4]}...")
            
            # Use requests directly instead of the openai library for more explicit error handling
            import requests
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_keys.get('api_key')}"
            }
            
            payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a helpful scientific advisor."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print("OpenAI API request successful")
                return content
            else:
                print(f"OpenAI API Error: Status code {response.status_code}")
                print(f"Response: {response.text}")
                return self._generate_demo_analysis(prompt)
                
        except Exception as e:
            print(f"Error using OpenAI API: {e}")
            return self._generate_demo_analysis(prompt)
        
    def _process_with_anthropic(self, prompt, api_keys, max_tokens):
        """Process content using Anthropic API"""
        try:
            # Using requests directly for Anthropic API
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": api_keys.get("api_key"),
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": "claude-3-opus-20240229",
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                print(f"Error from Anthropic API: {response.status_code}")
                print(response.text)
                return self._generate_demo_analysis(prompt)
                
        except Exception as e:
            print(f"Error using Anthropic API: {e}")
            return self._generate_demo_analysis(prompt)
    
    def _generate_demo_lab_book(self, transcript):
        """Generate a simple demo lab book when no LLM is available"""
        # Extract potential participants (look for names in the transcript)
        participants = set()
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        for match in re.finditer(name_pattern, transcript):
            participants.add(match.group(0))
        
        participants_str = ", ".join(participants) if participants else "Unknown Participants"
        
        # Create a simple structured lab book with the new format
        return f"""# Lab Experiment Session

**Date:** {datetime.now().strftime("%Y-%m-%d")}

**Participants:** {participants_str}

## Aims
[This section would outline what the experiment planned to investigate]

## Choices
[This section would document key decisions made during the lab session]

## Summary
[This section would summarize the main discoveries and learnings]

## Questions
[This section would list areas needing further investigation]

---
Note: This is a demo lab book. For full functionality, please ensure Ollama is running with your preferred model.
"""
    
    def _generate_demo_analysis(self, lab_book_content):
        """Generate a demo analysis when no API is available"""
        return """
1. AIMS AND OVERVIEW
This experiment appears to focus on investigating a specific scientific phenomenon, with clear methodology but some limitations in scope.

2. ANALYSIS OF KEY CHOICES
The experimental design shows thoughtful selection of parameters, though additional controls might have strengthened the results. The methods chosen are appropriate for the stated aims.

3. ASSESSMENT OF FINDINGS
The results demonstrate a relationship between the tested variables, though statistical significance could be more rigorously established. The interpretation aligns with current scientific understanding.

4. SUGGESTED FOLLOW-UP
Further investigation should explore: 
- How different conditions affect the observed phenomenon
- Whether the findings generalize to related systems
- More precise measurement techniques to reduce uncertainty

Note: This is a demo analysis. For comprehensive feedback, please configure an external API in your config file.
"""