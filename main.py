#!/usr/bin/env python
# main.py
import os
import sys
import time
import argparse
from datetime import datetime

# Import project modules
from modules.audio_capture import AudioRecorder
from modules.speech_processing import SpeechProcessor
from modules.llm_interface import LLMInterface
from modules.document_generator import DocumentGenerator
from modules.image_processor import ImageProcessor
from utils.helpers import get_most_recent_file, extract_title_from_content

# Import configuration
from config import OUTPUT_DIR, AUDIO_DIR, IMAGE_DIR

def setup_argparse():
    """Set up command line argument parsing"""
    parser = argparse.ArgumentParser(description='Lab Book Generator')
    
    # Main operation modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--record', action='store_true', help='Start audio recording')
    mode_group.add_argument('--process', type=str, help='Process an existing audio file')
    mode_group.add_argument('--add-image', type=str, help='Add an image to the latest lab book')
    mode_group.add_argument('--list', action='store_true', help='List available recordings and lab books')
    
    # Optional arguments
    parser.add_argument('--output-format', type=str, choices=['markdown', 'docx', 'both'], 
                        default='both', help='Output format for the lab book')
    parser.add_argument('--model', type=str, help='Path to custom LLM model')
    parser.add_argument('--whisper-model', type=str, default='base', 
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size for speech recognition')
    parser.add_argument('--max-duration', type=int, default=0, 
                        help='Maximum recording duration in seconds (0 = unlimited)')
    parser.add_argument('--prompt', type=str, help='Custom prompt template file for the LLM')
    
    return parser.parse_args()

def record_lab_session(max_duration=0):
    """Record a new lab session"""
    recorder = AudioRecorder()
    
    print("Starting recording... Press Ctrl+C to stop.")
    try:
        recorder.start_recording()
        
        # Record until interrupted or max duration reached
        start_time = time.time()
        while True:
            if max_duration > 0 and (time.time() - start_time) > max_duration:
                print(f"\nMaximum duration of {max_duration} seconds reached")
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping recording...")
    finally:
        audio_file = recorder.stop_recording()
        return audio_file

def process_audio_file(audio_path, model_path=None, whisper_model='base', output_format='both', custom_prompt=None):
    """Process an audio file to generate a lab book"""
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return None
    
    print(f"Processing audio file: {audio_path}")
    
    # Step 1: Speech recognition and diarization
    speech_processor = SpeechProcessor(whisper_model=whisper_model)
    transcript_file, transcript_data = speech_processor.process_audio(audio_path)
    transcript_text = transcript_data["full_text"]
    
    print("\nTranscript Summary:")
    print(f"Duration: {transcript_data['duration']:.2f} seconds")
    print(f"Language: {transcript_data['language']}")
    print(f"Speakers identified: {len(set(seg['speaker'] for seg in transcript_data['segments'] if seg['speaker'] != 'unknown'))}")
    
    # Step 2: Load custom prompt if provided
    if custom_prompt and os.path.exists(custom_prompt):
        with open(custom_prompt, 'r') as f:
            prompt_template = f.read()
    else:
        prompt_template = None
    
    # Step 3: Generate lab book using LLM
    llm = LLMInterface(model_path)
    lab_book_content = llm.generate_lab_book(transcript_text, prompt_template)
    
    # Step 4: Create document
    doc_generator = DocumentGenerator()
    
    # Extract a title from the generated content
    title_line = lab_book_content.split("\n")[0] if lab_book_content else ""
    if title_line.startswith("# "):
        title = title_line[2:].strip()
    else:
        title = f"Lab Session {datetime.now().strftime('%Y-%m-%d')}"
    
    # Generate documents in requested formats
    output_files = []
    
    if output_format in ['markdown', 'both']:
        md_file = doc_generator.generate_markdown(lab_book_content, title)
        output_files.append(md_file)
    
    if output_format in ['docx', 'both']:
        docx_file = doc_generator.generate_docx(lab_book_content, title)
        output_files.append(docx_file)
    
    print("\nLab book generation complete!")
    print(f"Output files: {', '.join(output_files)}")
    
    return output_files

def add_image_to_lab_book(image_path, model_path=None):
    """Add an image to the most recent lab book"""
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return False
    
    # Find the most recent lab book file
    md_file = get_most_recent_file(OUTPUT_DIR, ".md")
    docx_file = get_most_recent_file(OUTPUT_DIR, ".docx")
    
    if not md_file and not docx_file:
        print("Error: No lab book found to add image to")
        return False
    
    # Prefer markdown file if both exist
    lab_book_path = md_file if md_file else docx_file
    
    # Import and process the image
    image_processor = ImageProcessor()
    imported_image = image_processor.import_image(image_path)
    
    # Check if the image is a graph
    is_graph = image_processor.is_graph(imported_image)
    
    # Get a description for the image
    llm = LLMInterface(model_path)
    if is_graph:
        image_caption = llm.analyze_image(imported_image)
    else:
        image_caption = f"Image: {os.path.basename(image_path)}"
    
    # Add the image to the document
    doc_generator = DocumentGenerator()
    success = doc_generator.add_image_to_document(lab_book_path, imported_image, image_caption)
    
    if success:
        print(f"Image added to lab book {lab_book_path}")
    
    return success

def list_files():
    """List available recordings and lab books"""
    print("\nAvailable Audio Recordings:")
    if os.path.exists(AUDIO_DIR):
        audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
        audio_files.sort(key=lambda f: os.path.getctime(os.path.join(AUDIO_DIR, f)), reverse=True)
        
        if audio_files:
            for f in audio_files:
                creation_time = datetime.fromtimestamp(os.path.getctime(os.path.join(AUDIO_DIR, f))).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {f} - Created: {creation_time}")
        else:
            print("  No recordings found")
    else:
        print("  Audio directory not found")
    
    print("\nGenerated Lab Books:")
    if os.path.exists(OUTPUT_DIR):
        lab_books = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.md') or f.endswith('.docx')]
        lab_books.sort(key=lambda f: os.path.getctime(os.path.join(OUTPUT_DIR, f)), reverse=True)
        
        if lab_books:
            for f in lab_books:
                creation_time = datetime.fromtimestamp(os.path.getctime(os.path.join(OUTPUT_DIR, f))).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {f} - Created: {creation_time}")
        else:
            print("  No lab books found")
    else:
        print("  Output directory not found")
    
    print("\nAvailable Images:")
    if os.path.exists(IMAGE_DIR):
        images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        images.sort(key=lambda f: os.path.getctime(os.path.join(IMAGE_DIR, f)), reverse=True)
        
        if images:
            for f in images:
                creation_time = datetime.fromtimestamp(os.path.getctime(os.path.join(IMAGE_DIR, f))).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {f} - Created: {creation_time}")
        else:
            print("  No images found")
    else:
        print("  Image directory not found")

def main():
    """Main application entry point"""
    args = setup_argparse()
    
    if args.record:
        # Record a new lab session
        print("\n=== Lab Book Generator: Recording Mode ===\n")
        audio_file = record_lab_session(args.max_duration)
        if audio_file:
            # Process the recorded audio
            print("\n=== Processing Recording ===\n")
            process_audio_file(
                audio_file, 
                model_path=args.model,
                whisper_model=args.whisper_model,
                output_format=args.output_format,
                custom_prompt=args.prompt
            )
    
    elif args.process:
        # Process an existing audio file
        print("\n=== Lab Book Generator: Processing Mode ===\n")
        process_audio_file(
            args.process, 
            model_path=args.model,
            whisper_model=args.whisper_model,
            output_format=args.output_format,
            custom_prompt=args.prompt
        )
    
    elif args.add_image:
        # Add an image to the most recent lab book
        print("\n=== Lab Book Generator: Add Image Mode ===\n")
        add_image_to_lab_book(args.add_image, args.model)
    
    elif args.list:
        # List available files
        print("\n=== Lab Book Generator: File Listing ===")
        list_files()
    
    else:
        # This shouldn't happen due to the mutually_exclusive_group being required
        print("No action specified. Use --record, --process, or --add-image")
        print("Run with --help for more information")

if __name__ == "__main__":
    main()
