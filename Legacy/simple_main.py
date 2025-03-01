#!/usr/bin/env python
# simple_main.py - Simplified version of main.py to avoid segmentation faults
import os
import sys
import time
import argparse
from datetime import datetime

# Import simplified modules
from modules.Legacy.simple_audio import SimpleAudioRecorder
from modules.speech_processing import SpeechProcessor
from modules.llm_interface import LLMInterface
from modules.document_generator import DocumentGenerator
from modules.session_manager import SessionManager

# Import configuration
from config import OUTPUT_DIR, AUDIO_DIR

def record_and_process():
    """Record audio and process it into a lab book"""
    print("\n=== Lab Book Generator: Simple Mode ===\n")
    
    # Initialize recorder
    recorder = SimpleAudioRecorder()
    
    try:
        # Start recording
        print("Starting recording... Press Ctrl+C to stop.")
        recorder.start_recording()
        
        # Wait for Ctrl+C
        while True:
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping recording...")
    finally:
        # Stop recording
        audio_file = recorder.stop_recording()
        
        if not audio_file:
            print("No audio recorded. Exiting.")
            return
            
        print(f"Audio saved to: {audio_file}")
        
        # Process audio with Whisper
        try:
            print("\nProcessing audio with Whisper...")
            processor = SpeechProcessor(whisper_model="base")
            transcript_file, transcript_data = processor.process_audio(audio_file)
            
            # Generate lab book
            print("\nGenerating lab book...")
            llm = LLMInterface()
            transcript_text = transcript_data["full_text"]
            lab_book_content = llm.generate_lab_book(transcript_text)
            
            # Save output
            doc_generator = DocumentGenerator()
            md_file = doc_generator.generate_markdown(lab_book_content)
            
            print(f"\nLab book saved to: {md_file}")
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            print("Try running with --debug to identify the issue")

def process_existing_audio(audio_file):
    """Process an existing audio file"""
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        return
        
    try:
        print(f"Processing audio file: {audio_file}")
        
        # Process audio with Whisper
        processor = SpeechProcessor(whisper_model="base")
        transcript_file, transcript_data = processor.process_audio(audio_file)
        
        # Generate lab book
        llm = LLMInterface()
        transcript_text = transcript_data["full_text"]
        lab_book_content = llm.generate_lab_book(transcript_text)
        
        # Save output
        doc_generator = DocumentGenerator()
        md_file = doc_generator.generate_markdown(lab_book_content)
        
        print(f"\nLab book saved to: {md_file}")
        
    except Exception as e:
        print(f"Error processing audio: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Simplified Lab Book Generator")
    parser.add_argument("--record", action="store_true", help="Record and process audio")
    parser.add_argument("--process", type=str, help="Process existing audio file")
    parser.add_argument("--debug", action="store_true", help="Run debug tests")
    
    args = parser.parse_args()
    
    if args.debug:
        # Import and run debug script
        from debug.debug import main as debug_main
        debug_main()
        return
        
    if args.record:
        record_and_process()
    elif args.process:
        process_existing_audio(args.process)
    else:
        print("Please specify --record, --process, or --debug")
        print("Example: python simple_main.py --record")

if __name__ == "__main__":
    main()