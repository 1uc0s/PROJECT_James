# config.py - Simplified folder structure with backwards compatibility
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Lab cycle structure - all data organized by cycles
LAB_CYCLES_DIR = os.path.join(DATA_DIR, "lab_cycles")

# Temporary directory for recordings not yet assigned to a cycle
TEMP_DIR = os.path.join(DATA_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Backwards compatibility - maintain old paths for modules that use them
AUDIO_DIR = os.path.join(TEMP_DIR, "audio")
TRANSCRIPT_DIR = os.path.join(TEMP_DIR, "transcripts")
IMAGE_DIR = os.path.join(TEMP_DIR, "images")
OUTPUT_DIR = os.path.join(TEMP_DIR, "output")

# Create these directories for backward compatibility
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Audio recording settings
AUDIO_FORMAT = "wav"
CHANNELS = 1
RATE = 44100
CHUNK = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 3  # seconds

# LLM settings
LLM_MODEL_PATH = "llama3.2:latest"  # Using Ollama with llama3.2
LLM_CONTEXT_SIZE = 4096
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2048

# Speaker diarization settings
USE_HF_API = True  # Whether to use HuggingFace API for diarization
PRIMARY_SPEAKER = "Me"  # Label for the primary speaker

# Lab cycle settings
DEFAULT_LAB_CYCLE = None  # Set this to a cycle ID to make it the default
RAG_MAX_RESULTS = 3  # Number of contexts to retrieve for RAG
VECTOR_DB_TYPE = "faiss"  # "faiss" or "simple" for vector similarity

# External API keys
EXTERNAL_API_KEYS = {
    "openai": {
        "api_key": os.environ.get("OPENAI_API_KEY", "")
    },
    "anthropic": {
        "api_key": os.environ.get("ANTHROPIC_API_KEY", "")
    }
}

# External API default settings
DEFAULT_API_PROVIDER = "openai"  # "openai" or "anthropic"
DEFAULT_POST_PROCESS = True  # Whether to post-process by default

# Lab book structure template - Updated to match the template in templates/labbook_template.md
LAB_BOOK_SECTIONS = [
    "Title",
    "Date",
    "Participants",
    "Aims",
    "Choices",
    "Summary",
    "Questions",
    "Smart Analysis",
    "External Comments"
]

# Function to get cycle-specific paths
def get_cycle_paths(cycle_id):
    """Get standard paths for a specific lab cycle"""
    cycle_dir = os.path.join(LAB_CYCLES_DIR, cycle_id)
    
    paths = {
        "root": cycle_dir,
        "audio": os.path.join(cycle_dir, "audio"),
        "transcripts": os.path.join(cycle_dir, "transcripts"),
        "lab_books": os.path.join(cycle_dir, "lab_books"),
        "resources": os.path.join(cycle_dir, "resources"),
        "knowledge_base": os.path.join(cycle_dir, "knowledge_base")
    }
    
    # Create directories if they don't exist
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    
    return paths

# Helper function for better timestamp formatting
def format_timestamp(include_seconds=False):
    """Return a formatted timestamp string with dashes instead of underscores"""
    import datetime
    if include_seconds:
        return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    else:
        return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

# Default prompt template - Updated to match the new sections
LAB_BOOK_PROMPT = """
Create a detailed lab book entry based on the following transcript.
Structure the lab book with these sections:
- Title: Derive a concise title from the experiment discussion
- Date: {date}
- Participants: List all participants mentioned in the transcript
- Aims: Clearly state the goals of the experiment
- Choices: List key decisions and materials chosen
- Summary: Summarize the outcomes and findings
- Questions: List areas for further investigation or open questions

Use a formal, scientific tone and organize information logically. 
If certain sections lack information, note this but don't invent details.

{context}

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

# Post-processing prompts - Renamed to Smart Analysis
POST_PROCESSING_PROMPT = """
You are a scientific advisor helping to improve this lab book and suggest next steps.
Please analyze the lab book below and provide the following:

1. A concise summary of what was done and the key findings
2. Three specific strengths in the lab book documentation
3. Three areas for improvement or expansion
4. Two specific follow-up experiments or analyses that would build upon these results
5. Any potential scientific misconceptions or errors that should be addressed

Lab Book:
{lab_book}
"""