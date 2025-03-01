# modules/session_manager.py
import os
import json
import time
import shutil
from datetime import datetime
import glob

from config import AUDIO_DIR, DATA_DIR
from modules.speech_processing import SpeechProcessor
from modules.llm_interface import LLMInterface
from modules.document_generator import DocumentGenerator
from utils.helpers import get_audio_duration

class SessionManager:
    def __init__(self, session_id=None, whisper_model="base", llm_model=None):
        """Initialize session manager for tracking session recordings"""
        # Generate session ID if not provided
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create session directory
        self.session_dir = os.path.join(DATA_DIR, "sessions", self.session_id)
        self.session_audio_dir = os.path.join(self.session_dir, "audio")
        self.session_transcript_dir = os.path.join(self.session_dir, "transcripts")
        self.session_output_dir = os.path.join(self.session_dir, "output")
        
        # Create directories
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(self.session_audio_dir, exist_ok=True)
        os.makedirs(self.session_transcript_dir, exist_ok=True)
        os.makedirs(self.session_output_dir, exist_ok=True)
        
        # Initialize session data
        self.recordings = []
        self.transcripts = []
        self.metadata = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "recordings": [],
            "total_duration": 0,
            "lab_books": []
        }
        
        # Save initial metadata
        self._save_metadata()
        
        # Set up processors
        self.whisper_model = whisper_model
        self.llm_model = llm_model
        self.speech_processor = None
        self.llm = None
        self.doc_generator = None
        
        print(f"Session '{self.session_id}' initialized")
    
    def add_recording(self, audio_file):
        """Add a recording to the current session"""
        if not os.path.exists(audio_file):
            print(f"Warning: Audio file not found: {audio_file}")
            return False
            
        # Copy to session directory with sequential naming
        filename = os.path.basename(audio_file)
        base_name, ext = os.path.splitext(filename)
        new_filename = f"segment_{len(self.recordings) + 1:03d}{ext}"
        destination = os.path.join(self.session_audio_dir, new_filename)
        
        # Copy the file
        shutil.copy2(audio_file, destination)
        
        # Get duration
        duration = get_audio_duration(destination)
        
        # Update metadata
        recording_info = {
            "filename": new_filename,
            "original_file": audio_file,
            "path": destination,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "processed": False
        }
        
        self.recordings.append(recording_info)
        self.metadata["recordings"].append(recording_info)
        self.metadata["total_duration"] += duration
        
        # Save updated metadata
        self._save_metadata()
        
        print(f"Added recording: {new_filename} ({duration:.2f} seconds)")
        return True
    
    def end_session(self, generate_labbook=True):
        """End the current session and optionally generate a lab book"""
        self.metadata["end_time"] = datetime.now().isoformat()
        self._save_metadata()
        
        if generate_labbook:
            return self.generate_labbook()
        
        return None
    
    def generate_labbook(self, output_format="both", custom_prompt=None):
        """Generate a lab book from all recordings in the session"""
        # Initialize processors if needed
        if not self.speech_processor:
            self.speech_processor = SpeechProcessor(whisper_model=self.whisper_model)
        if not self.llm:
            self.llm = LLMInterface(self.llm_model)
        if not self.doc_generator:
            self.doc_generator = DocumentGenerator()
        
        # Process all unprocessed recordings
        for i, recording in enumerate(self.recordings):
            if not recording.get("processed", False):
                print(f"Processing recording {i+1}/{len(self.recordings)}: {recording['filename']}")
                try:
                    # Process audio
                    transcript_file, transcript_data = self.speech_processor.process_audio(recording["path"])
                    
                    # Save transcript to session directory
                    base_name = os.path.splitext(recording["filename"])[0]
                    session_transcript = os.path.join(
                        self.session_transcript_dir, 
                        f"{base_name}_transcript.json"
                    )
                    
                    # Copy transcript
                    with open(transcript_file, 'r') as src:
                        transcript_content = json.load(src)
                    
                    with open(session_transcript, 'w') as dst:
                        json.dump(transcript_content, dst, indent=2)
                    
                    # Update recording info
                    recording["processed"] = True
                    recording["transcript"] = session_transcript
                    self.transcripts.append(transcript_data)
                    
                except Exception as e:
                    print(f"Error processing recording {recording['filename']}: {e}")
        
        # Save updated metadata
        self._save_metadata()
        
        # Generate combined transcript
        full_transcript = self._combine_transcripts()
        
        if not full_transcript:
            print("No transcript data available to generate lab book")
            return None
        
        # Generate lab book using LLM
        print("Generating lab book from combined transcripts...")
        lab_book_content = self.llm.generate_lab_book(full_transcript, custom_prompt)
        
        # Extract title or create default
        title = None
        if lab_book_content:
            lines = lab_book_content.split('\n')
            if lines and lines[0].startswith('# '):
                title = lines[0][2:].strip()
        
        if not title:
            title = f"Lab Session {datetime.now().strftime('%Y-%m-%d')}"
        
        # Generate output files
        output_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format in ['markdown', 'both']:
            md_file = os.path.join(self.session_output_dir, f"labbook_{timestamp}.md")
            with open(md_file, 'w') as f:
                f.write(lab_book_content)
            output_files.append(md_file)
            
        if output_format in ['docx', 'both']:
            docx_file = self.doc_generator.generate_docx(lab_book_content, title)
            # Copy to session directory
            session_docx = os.path.join(self.session_output_dir, f"labbook_{timestamp}.docx")
            shutil.copy2(docx_file, session_docx)
            output_files.append(session_docx)
        
        # Update metadata
        labbook_info = {
            "timestamp": timestamp,
            "title": title,
            "files": output_files,
            "duration": self.metadata["total_duration"]
        }
        self.metadata["lab_books"].append(labbook_info)
        self._save_metadata()
        
        print(f"Lab book generated: {', '.join(output_files)}")
        return output_files
    
    def _combine_transcripts(self):
        """Combine all transcripts into a single text"""
        if not self.transcripts:
            return None
            
        combined_text = f"--- LAB SESSION TRANSCRIPT ---\nDate: {datetime.now().strftime('%Y-%m-%d')}\nDuration: {self.metadata['total_duration']:.2f} seconds\n\n"
        
        # Sort transcripts by start time
        for i, transcript in enumerate(self.transcripts):
            combined_text += f"--- SEGMENT {i+1} ---\n"
            combined_text += transcript.get("full_text", "")
            combined_text += "\n\n"
        
        return combined_text
    
    def _save_metadata(self):
        """Save session metadata to file"""
        metadata_file = os.path.join(self.session_dir, "session_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_session_info(self):
        """Get information about the current session"""
        return {
            "session_id": self.session_id,
            "start_time": self.metadata["start_time"],
            "end_time": self.metadata["end_time"],
            "recordings": len(self.recordings),
            "total_duration": self.metadata["total_duration"],
            "lab_books": len(self.metadata["lab_books"])
        }

    @classmethod
    def list_sessions(cls):
        """List all available sessions"""
        sessions_dir = os.path.join(DATA_DIR, "sessions")
        if not os.path.exists(sessions_dir):
            return []
            
        sessions = []
        for session_dir in os.listdir(sessions_dir):
            metadata_file = os.path.join(sessions_dir, session_dir, "session_metadata.json")
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    sessions.append({
                        "session_id": metadata["session_id"],
                        "start_time": metadata["start_time"],
                        "end_time": metadata["end_time"],
                        "recordings": len(metadata["recordings"]),
                        "total_duration": metadata["total_duration"],
                        "lab_books": len(metadata["lab_books"])
                    })
                except Exception as e:
                    print(f"Error loading session metadata for {session_dir}: {e}")
        
        return sessions
    
    @classmethod
    def load_session(cls, session_id, whisper_model="base", llm_model=None):
        """Load an existing session"""
        sessions_dir = os.path.join(DATA_DIR, "sessions")
        session_dir = os.path.join(sessions_dir, session_id)
        
        if not os.path.exists(session_dir):
            raise ValueError(f"Session '{session_id}' not found")
            
        metadata_file = os.path.join(session_dir, "session_metadata.json")
        if not os.path.exists(metadata_file):
            raise ValueError(f"Session metadata not found for '{session_id}'")
            
        # Create new session manager
        session = cls(session_id, whisper_model, llm_model)
        
        # Load metadata
        with open(metadata_file, 'r') as f:
            session.metadata = json.load(f)
        
        # Load recordings
        session.recordings = session.metadata["recordings"]
        
        # Load transcripts
        for recording in session.recordings:
            if recording.get("processed", False) and "transcript" in recording:
                if os.path.exists(recording["transcript"]):
                    try:
                        with open(recording["transcript"], 'r') as f:
                            transcript_data = json.load(f)
                        session.transcripts.append(transcript_data)
                    except Exception as e:
                        print(f"Error loading transcript {recording['transcript']}: {e}")
        
        print(f"Loaded session '{session_id}' with {len(session.recordings)} recordings")
        return session