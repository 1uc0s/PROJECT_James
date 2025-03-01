# utils/helpers.py
import os
import json
import time
from datetime import datetime

def get_most_recent_file(directory, extension=None):
    """Get the most recently created file in a directory"""
    if not os.path.exists(directory):
        return None
        
    files = os.listdir(directory)
    if extension:
        files = [f for f in files if f.endswith(extension)]
    
    if not files:
        return None
    
    # Sort by creation time, newest first
    files.sort(key=lambda f: os.path.getctime(os.path.join(directory, f)), reverse=True)
    
    return os.path.join(directory, files[0])

def extract_title_from_content(content):
    """Extract a title from the content"""
    if not content:
        return None
    
    lines = content.split('\n')
    for line in lines[:5]:  # Check only first few lines
        # Look for heading format "# Title"
        if line.startswith('# '):
            return line[2:].strip()
    
    return None

def timestamp_string(include_seconds=False):
    """Return a formatted timestamp string with dashes instead of underscores"""
    if include_seconds:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    else:
        return datetime.now().strftime("%Y-%m-%d_%H-%M")

def save_json(data, filepath):
    """Save data as JSON to the specified file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(filepath):
    """Load JSON data from the specified file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def create_labeled_transcript(transcript_data):
    """Create a nicely formatted transcript with speaker labels"""
    if isinstance(transcript_data, str):
        # If a file path is provided, load the transcript
        with open(transcript_data, 'r') as f:
            transcript_data = json.load(f)
    
    formatted = []
    current_speaker = None
    
    for segment in transcript_data.get("segments", []):
        speaker = segment.get("speaker", "unknown")
        text = segment.get("text", "").strip()
        
        if not text:
            continue
            
        # Add speaker label only when speaker changes
        if speaker != current_speaker:
            formatted.append(f"\n[{speaker}]:")
            current_speaker = speaker
        
        formatted.append(text)
    
    return " ".join(formatted)

def get_audio_duration(audio_file):
    """Get the duration of an audio file in seconds"""
    import wave
    
    try:
        with wave.open(audio_file, 'r') as wf:
            # Get basic audio properties
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0

def parse_lab_book_sections(content):
    """Parse a lab book content into sections"""
    sections = {}
    
    # Extract title
    title_match = content.split('\n')[0] if content else ""
    if title_match.startswith('# '):
        sections['title'] = title_match[2:].strip()
    else:
        sections['title'] = None
    
    # Split content by section headers
    parts = content.split('##')
    
    # Process intro section (before any ## headers)
    intro = parts[0].strip()
    sections['intro'] = intro
    
    # Process each section
    for part in parts[1:]:
        if not part.strip():
            continue
            
        lines = part.strip().split('\n')
        section_name = lines[0].strip().lower().replace(' ', '_')
        section_content = '\n'.join(lines[1:]).strip()
        
        sections[section_name] = section_content
    
    return sections

# Test function
if __name__ == "__main__":
    # Test timestamp
    print(f"Current timestamp: {timestamp_string()}")
    print(f"Current timestamp with seconds: {timestamp_string(True)}")
    
    # Test get_most_recent_file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    most_recent = get_most_recent_file(test_dir, ".py")
    print(f"Most recent Python file: {most_recent}")