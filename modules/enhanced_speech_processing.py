# modules/enhanced_speech_processing.py
import os
import json
import whisper
from pyannote.audio import Pipeline
import torch
from datetime import datetime
import time
import warnings
import numpy as np

# Suppress deprecation warnings
warnings.filterwarnings("ignore")

from config import TRANSCRIPT_DIR, DATA_DIR

class EnhancedSpeechProcessor:
    def __init__(self, diarization_model="pyannote/speaker-diarization@3.1", whisper_model="base", 
                 primary_speaker=None, use_hf_api=False, hf_token=None):
        """Initialize the enhanced speech processor
        
        Args:
            diarization_model: Model to use for speaker diarization
            whisper_model: Model size for Whisper transcription
            primary_speaker: ID of the primary speaker (e.g., "user")
            use_hf_api: Whether to use HuggingFace API for diarization
            hf_token: HuggingFace API token (required if use_hf_api is True)
        """
        # Create transcripts directory if it doesn't exist
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        
        # Initialize Whisper for speech recognition
        print("Loading Whisper model...")
        try:
            self.whisper_model = whisper.load_model(whisper_model)
            print(f"Whisper {whisper_model} model loaded successfully")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            print("Please make sure Whisper is properly installed")
            raise
        
        # Store configurations
        self.primary_speaker = primary_speaker or "user"
        self.use_hf_api = use_hf_api
        
        # Initialize HF token with explicit priority:
        # 1. Parameter passed to constructor
        # 2. Environment variable
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        
        if not self.hf_token:
            print("WARNING: No HuggingFace token found. Speaker diarization requires a HF_TOKEN.")
            print("Set with: export HF_TOKEN=your_token_here or pass directly to the constructor.")
        else:
            print(f"HuggingFace token found. Token length: {len(self.hf_token)}")
        
        # Check for required token when using HF API
        if self.use_hf_api and not self.hf_token:
            print("Warning: HuggingFace API token (HF_TOKEN) not found.")
            print("Speaker diarization will be limited.")
            self.use_hf_api = False
        
        # Initialize speaker diarization based on configuration
        print("Setting up device for speech processing...")
        if torch.cuda.is_available():
            print("CUDA device available - using GPU acceleration")
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            print("Using Apple Metal (MPS) for acceleration")
            self.device = torch.device("mps")
        else:
            print("No GPU acceleration available - using CPU")
            self.device = torch.device("cpu")
            
        print(f"Device type: {type(self.device)}, Device: {self.device}")
            
        try:
            print(f"Loading diarization model on {self.device}...")
            
            if self.use_hf_api:
                # Use API-based diarization
                self.diarization = self._setup_hf_api_diarization()
            else:
                # Use local diarization
                token_status = "NO TOKEN" if not self.hf_token else f"Token available (length: {len(self.hf_token)})"
                print(f"HF Token status: {token_status}")
                
                print("About to call Pipeline.from_pretrained...")
                try:
                    self.diarization = Pipeline.from_pretrained(
                        diarization_model, 
                        use_auth_token=self.hf_token
                    )
                    print("Pipeline.from_pretrained successful")
                except Exception as e:
                    print(f"Error in Pipeline.from_pretrained: {e}")
                    print(f"Error type: {type(e)}")
                    raise
                
                # Move to appropriate device
                print(f"Moving diarization model to device. Current device: {self.device}, Type: {type(self.device)}")
                try:
                    # PyAnnote doesn't support MPS directly, use CPU for Apple Silicon
                    if torch.backends.mps.is_available():
                        print("MPS device detected - moving to CPU instead")
                        self.diarization = self.diarization.to(torch.device("cpu"))
                    else:
                        print(f"Moving to device: {self.device}")
                        self.diarization = self.diarization.to(self.device)
                    print("Device migration completed")
                except Exception as e:
                    print(f"Error moving model to device: {e}")
                    print(f"Error type: {type(e)}")
                    raise
                    
            print("Diarization model loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load diarization model: {e}")
            print(f"Detailed error type: {type(e)}")
            print("Continuing without speaker identification...")
            self.diarization = None
        
        # Speaker profiles directory for storing voice signatures
        self.speaker_profiles_dir = os.path.join(DATA_DIR, "speaker_profiles")
        os.makedirs(self.speaker_profiles_dir, exist_ok=True)
        
        # Load existing speaker profiles
        self.speaker_profiles = self._load_speaker_profiles()
    
    def _setup_hf_api_diarization(self):
        """Set up HuggingFace API for diarization"""
        # This is a placeholder for the actual API implementation
        # In a real implementation, this would use HF Inference API
        try:
            import requests
            # Test connection to HF API
            print(f"Testing connection to HuggingFace API with token: {self.hf_token[:4]}...")
            response = requests.get(
                "https://huggingface.co/api/models", 
                headers={"Authorization": f"Bearer {self.hf_token}"}
            )
            if response.status_code == 200:
                print("Successfully connected to HuggingFace API")
                return "hf_api"  # Just a marker that we're using the API
            else:
                print(f"Error connecting to HuggingFace API: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error setting up HuggingFace API: {e}")
            return None
    
    def _load_speaker_profiles(self):
        """Load existing speaker profiles"""
        profiles = {}
        
        profile_file = os.path.join(self.speaker_profiles_dir, "profiles.json")
        if os.path.exists(profile_file):
            try:
                with open(profile_file, 'r') as f:
                    profiles = json.load(f)
                print(f"Loaded {len(profiles)} speaker profiles")
            except Exception as e:
                print(f"Error loading speaker profiles: {e}")
        
        return profiles
    
    def _save_speaker_profiles(self):
        """Save speaker profiles to disk"""
        profile_file = os.path.join(self.speaker_profiles_dir, "profiles.json")
        try:
            with open(profile_file, 'w') as f:
                json.dump(self.speaker_profiles, f, indent=2)
            print(f"Saved {len(self.speaker_profiles)} speaker profiles")
        except Exception as e:
            print(f"Error saving speaker profiles: {e}")
    
    def _categorize_speakers(self, diarization_result):
        """Categorize speakers as primary user, lab partner, or demonstrator"""
        # This is a simplified approach - in a real implementation, 
        # you would use more sophisticated speaker recognition techniques
        
        speakers = {}
        speaker_durations = {}
        
        # Count total speaking time for each speaker
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            duration = turn.end - turn.start
            if speaker not in speaker_durations:
                speaker_durations[speaker] = 0
            speaker_durations[speaker] += duration
        
        # If we have no prior profiles, assume the person who speaks the most is the primary user
        if not self.speaker_profiles and speaker_durations:
            # Find speaker with maximum duration
            primary_speaker_id = max(speaker_durations, key=speaker_durations.get)
            
            # Assign categories based on speaking time
            for speaker, duration in speaker_durations.items():
                if speaker == primary_speaker_id:
                    speakers[speaker] = {
                        "role": "primary",
                        "label": "You",
                        "duration": duration
                    }
                else:
                    # For other speakers, label them as external
                    speakers[speaker] = {
                        "role": "external",
                        "label": f"Speaker {speaker.split('_')[-1]}",
                        "duration": duration
                    }
            
            # Add the primary speaker to profiles for future reference
            self.speaker_profiles["primary"] = {
                "speaker_id": primary_speaker_id,
                "label": "You",
                "role": "primary",
                "created_at": datetime.now().isoformat()
            }
            self._save_speaker_profiles()
            
        else:
            # If we have profiles, try to match speakers
            for speaker, duration in speaker_durations.items():
                matched = False
                
                # Check if this speaker matches a known profile
                for profile_id, profile in self.speaker_profiles.items():
                    # In a real implementation, you would use voice embeddings and similarity metrics
                    # For now, we're using a simple ID match
                    if profile.get("speaker_id") == speaker:
                        speakers[speaker] = {
                            "role": profile.get("role", "unknown"),
                            "label": profile.get("label", f"Speaker {speaker.split('_')[-1]}"),
                            "duration": duration
                        }
                        matched = True
                        break
                
                # If no match, mark as unknown external speaker
                if not matched:
                    speakers[speaker] = {
                        "role": "external",
                        "label": f"Speaker {speaker.split('_')[-1]}",
                        "duration": duration
                    }
        
        return speakers
    
    def process_audio(self, audio_path, classify_speakers=True):
        """Process audio file to get transcript with speaker diarization and classification"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        # Generate base filename for output
        base_filename = os.path.splitext(os.path.basename(audio_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(TRANSCRIPT_DIR, f"{base_filename}_transcript_{timestamp}.json")
        
        # Step 1: Transcribe audio with Whisper
        print("Transcribing audio with Whisper...")
        result = self.whisper_model.transcribe(audio_path)
        
        # Step 2: Perform speaker diarization if available
        speakers = {}
        speaker_categories = {}
        
        if self.diarization:
            try:
                print("Performing speaker diarization...")
                
                if self.use_hf_api and self.diarization == "hf_api":
                    # Use HuggingFace API for diarization
                    diarization = self._perform_hf_api_diarization(audio_path)
                else:
                    # Use local diarization model
                    diarization = self.diarization(audio_path)
                
                # Categorize speakers
                if classify_speakers:
                    speaker_categories = self._categorize_speakers(diarization)
                
                # Process diarization results
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    # Map segments to speakers
                    start_time = turn.start
                    end_time = turn.end
                    
                    # Find segments that overlap with this speaker turn
                    for segment in result["segments"]:
                        seg_start = segment["start"]
                        seg_end = segment["end"]
                        
                        # Check for overlap
                        if max(start_time, seg_start) < min(end_time, seg_end):
                            if segment["id"] not in speakers:
                                speakers[segment["id"]] = speaker
            except Exception as e:
                print(f"Error during diarization: {e}")
                print("Continuing without speaker identification...")
        
        # Step 3: Create structured transcript with speakers
        transcript_data = {
            "audio_file": audio_path,
            "date": time.strftime("%Y-%m-%d"),
            "language": result["language"],
            "duration": result["segments"][-1]["end"] if result["segments"] else 0,
            "segments": [],
            "speaker_categories": speaker_categories
        }
        
        # Track speaker segments for categorization
        primary_segments = []
        external_segments = []
        
        # Add speaker information to segments
        for segment in result["segments"]:
            speaker_id = speakers.get(segment["id"], "unknown")
            
            # Get speaker category and label if available
            category = speaker_categories.get(speaker_id, {})
            role = category.get("role", "unknown")
            label = category.get("label", 
                                f"Speaker {speaker_id.split('_')[-1]}" if speaker_id != "unknown" else "Unknown")
            
            segment_data = {
                "id": segment["id"],
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "speaker": speaker_id,
                "speaker_label": label,
                "speaker_role": role
            }
            
            # Add to appropriate category list
            if role == "primary":
                primary_segments.append(segment_data)
            else:
                external_segments.append(segment_data)
                
            transcript_data["segments"].append(segment_data)
        
        # Create full transcript text, distinguishing between primary and external speakers
        full_transcript = ""
        for segment in transcript_data["segments"]:
            speaker_prefix = f"[{segment['speaker_label']}]: "
            full_transcript += f"{speaker_prefix}{segment['text']}\n"
        
        # Add categorized text sections
        primary_text = "\n".join([f"{s['text']}" for s in primary_segments])
        external_text = "\n".join([f"[{s['speaker_label']}]: {s['text']}" for s in external_segments])
        
        transcript_data["full_text"] = full_transcript.strip()
        transcript_data["primary_text"] = primary_text.strip()
        transcript_data["external_text"] = external_text.strip()
        
        # Save transcript to file
        with open(output_file, 'w') as f:
            json.dump(transcript_data, f, indent=2)
        
        print(f"Transcript saved to {output_file}")
        return output_file, transcript_data
    
    def _perform_hf_api_diarization(self, audio_path):
        """Use HuggingFace API for diarization"""
        # This is a placeholder for actual API implementation
        # In a real implementation, this would send the audio file to the HF API
        # and parse the response into a format compatible with PyAnnote
        
        print("Using HuggingFace API for diarization would go here")
        # For now, we'll create a mock diarization result similar to PyAnnote output
        
        # This is a simplified implementation - in practice, you would:
        # 1. Send the audio to the HF API
        # 2. Get the diarization result
        # 3. Convert it to a format compatible with PyAnnote
        
        from pyannote.core import Segment, Timeline, Annotation
        
        # Create a simple mock diarization with a primary speaker and one external speaker
        annotation = Annotation()
        
        # Mock two speakers with alternating 10-second segments
        audio_info = whisper.load_audio(audio_path)
        duration = len(audio_info) / whisper.SAMPLE_RATE
        
        # Create segments for "primary" speaker
        for i in range(0, int(duration), 20):
            end = min(i + 10, duration)
            annotation[Segment(i, end)] = "SPEAKER_0"
        
        # Create segments for "external" speaker
        for i in range(10, int(duration), 20):
            end = min(i + 10, duration)
            annotation[Segment(i, end)] = "SPEAKER_1"
        
        return annotation
    
    def add_speaker_profile(self, speaker_id, label, role="external", metadata=None):
        """Add or update a speaker profile"""
        self.speaker_profiles[speaker_id] = {
            "speaker_id": speaker_id,
            "label": label,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self._save_speaker_profiles()
        print(f"Added speaker profile for {label} (ID: {speaker_id}, Role: {role})")
        
    def get_transcript_text(self, transcript_data, include_external=True):
        """Extract transcript text from processed data with options for filtering"""
        if isinstance(transcript_data, str):
            # If a file path is provided, load the transcript
            with open(transcript_data, 'r') as f:
                transcript_data = json.load(f)
        
        if include_external:
            return transcript_data.get("full_text", "")
        else:
            return transcript_data.get("primary_text", "")
    
    def get_external_comments(self, transcript_data):
        """Extract only external comments from the transcript"""
        if isinstance(transcript_data, str):
            # If a file path is provided, load the transcript
            with open(transcript_data, 'r') as f:
                transcript_data = json.load(f)
        
        return transcript_data.get("external_text", "")