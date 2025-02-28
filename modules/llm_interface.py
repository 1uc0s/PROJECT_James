# modules/llm_interface.py
import os
from datetime import datetime
from llama_cpp import Llama

from config import LLM_MODEL_PATH, LLM_CONTEXT_SIZE, LLM_TEMPERATURE, LLM_MAX_TOKENS, LAB_BOOK_PROMPT, IMAGE_ANALYSIS_PROMPT

class LLMInterface:
    def __init__(self, model_path=None):
        """Initialize the LLM interface using llama-cpp-python"""
        self.model_path = model_path or LLM_MODEL_PATH
        
        if not self.model_path:
            print("Warning: No LLM model path specified. Please set LLM_MODEL_PATH in config.py")
            print("Running in demo mode - responses will be placeholders")
            self.llm = None
            return
            
        # Check if model file exists
        if not os.path.exists(self.model_path):
            print(f"Warning: LLM model not found at {self.model_path}")
            print("Running in demo mode - responses will be placeholders")
            self.llm = None
            return
        
        print(f"Loading LLM model from {self.model_path}...")
        try:
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
            self.llm = None
    
    def generate_lab_book(self, transcript, custom_template=None):
        """Generate a structured lab book from transcript using the LLM"""
        # Prepare the prompt
        prompt_template = custom_template or LAB_BOOK_PROMPT
        prompt = prompt_template.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            transcript=transcript
        )
        
        if not self.llm:
            print("Using demo mode for lab book generation")
            return self._generate_demo_lab_book(transcript)
        
        # Generate response from LLM
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
    
    def analyze_image(self, image_path, transcript_context=None):
        """Analyze an image (graph, plot, etc.) and generate a description"""
        # Check if image exists
        if not os.path.exists(image_path):
            return "Error: Image file not found"
            
        # This would normally use a multimodal LLM
        # For now, we'll just return a placeholder response
        if not self.llm:
            return f"[Placeholder image analysis for {os.path.basename(image_path)}]"
            
        # In a real implementation, this would use a multimodal model
        # or integrate with a vision API
        return f"[Analysis of {os.path.basename(image_path)} would be generated here using a multimodal model]"
    
    def _generate_demo_lab_book(self, transcript):
        """Generate a simple demo lab book when no LLM is available"""
        # Extract potential participants (look for names in the transcript)
        import re
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
Note: This is a demo lab book. For full functionality, please configure a local LLM model.
"""


# Simple command-line test
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LLM interface")
    parser.add_argument("--model", help="Path to the LLM model")
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
