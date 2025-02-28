# modules/speech_processing.py
import os
import json
import whisper
from pyannote.audio import Pipeline
import torch
from datetime import datetime
import time

from config import TRANSCRIPT_DIR

class SpeechProcessor:
    def __init__(self, diarization_model="pyannote/speaker-diarization@2.1", whisper_model="base"):
        # Create transcripts directory if it doesn't exist
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        
        # Initialize Whisper for speech recognition
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model(whisper_model)
        
        # Initialize speaker diarization if GPU is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            print(f"Loading diarization model on {self.device}...")
            # Note: This requires a HuggingFace token in practice
            self.diarization = Pipeline.from_pretrained(
                diarization_model, 
                use_auth_token=os.environ.get("HF_TOKEN")
            ).to(self.device)
            print("Diarization model loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load diarization model: {e}")
            print("Continuing without speaker identification...")
            self.diarization = None
    
    def process_audio(self, audio_path):
        """Process audio file to get transcript with speaker diarization"""
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
        if self.diarization:
            try:
                print("Performing speaker diarization...")
                diarization = self.diarization(audio_path)
                
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
            "segments": []
        }
        
        # Add speaker information to segments
        for segment in result["segments"]:
            segment_data = {
                "id": segment["id"],
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "speaker": speakers.get(segment["id"], "unknown")
            }
            transcript_data["segments"].append(segment_data)
        
        # Create full transcript text
        full_transcript = ""
        for segment in transcript_data["segments"]:
            speaker_prefix = f"[{segment['speaker']}]: " if segment['speaker'] != "unknown" else ""
            full_transcript += f"{speaker_prefix}{segment['text']}\n"
        
        transcript_data["full_text"] = full_transcript.strip()
        
        # Save transcript to file
        with open(output_file, 'w') as f:
            json.dump(transcript_data, f, indent=2)
        
        print(f"Transcript saved to {output_file}")
        return output_file, transcript_data
    
    def get_transcript_text(self, transcript_data):
        """Extract the full text transcript from processed data"""
        if isinstance(transcript_data, str):
            # If a file path is provided, load the transcript
            with open(transcript_data, 'r') as f:
                transcript_data = json.load(f)
        
        return transcript_data.get("full_text", "")


# Simple command-line test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python speech_processing.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    processor = SpeechProcessor()
    transcript_file, _ = processor.process_audio(audio_file)
    print(f"Transcript created: {transcript_file}")