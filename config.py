# config.py
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Audio recording settings
AUDIO_FORMAT = "wav"
CHANNELS = 1
RATE = 44100
CHUNK = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 3  # seconds

# File paths
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
TRANSCRIPT_DIR = os.path.join(DATA_DIR, "transcripts")
IMAGE_DIR = os.path.join(DATA_DIR, "images")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# LLM settings
LLM_MODEL_PATH = "ollama:llama3.2"  # Using Ollama with llama3.2
LLM_CONTEXT_SIZE = 4096
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2048

# Lab book structure template
LAB_BOOK_SECTIONS = [
    "Title",
    "Date",
    "Participants",
    "Objectives",
    "Materials and Methods",
    "Procedure",
    "Observations",
    "Results",
    "Analysis",
    "Conclusions",
    "Next Steps"
]

# Default prompt template
LAB_BOOK_PROMPT = """
Create a detailed lab book entry based on the following transcript.
Structure the lab book with these sections:
- Title: Derive a concise title from the experiment discussion
- Date: {date}
- Participants: List all participants mentioned in the transcript
- Objectives: Clearly state the goals of the experiment
- Materials and Methods: List all equipment, reagents and methods mentioned
- Procedure: Describe the step-by-step process followed
- Observations: Note all observations mentioned
- Results: Summarize the outcomes and findings
- Analysis: Provide analysis of the results
- Conclusions: Summarize the key conclusions
- Next Steps: Suggest follow-up experiments or actions

Use a formal, scientific tone and organize information logically. 
If certain sections lack information, note this but don't invent details.

Transcript:
{transcript}
"""

# Image analysis prompt
IMAGE_ANALYSIS_PROMPT = """
Analyze the following graph/image and provide a detailed description:
1. What type of graph/visualization is this?
2. What are the axes representing?
3. What are the key trends or patterns visible?
4. What conclusions can be drawn from this visualization?
5. How does this relate to the experiment described in the transcript?

Be specific and technical in your description.
"""
