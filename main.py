#!/usr/bin/env python
# main.py - Updated version with lab cycle support, enhanced diarization and post-processing
import os
import sys
import time
import threading
import argparse
from datetime import datetime

# Import project modules
from modules.robust_audio import RobustAudioRecorder
from modules.enhanced_speech_processing import EnhancedSpeechProcessor
from modules.llm_interface_updated import LLMInterface
from modules.document_generator import DocumentGenerator
from modules.session_manager_updated import SessionManager
from modules.lab_cycle_manager import LabCycleManager

# Import configuration
from config import (
    OUTPUT_DIR, AUDIO_DIR, DEFAULT_LAB_CYCLE, 
    DEFAULT_API_PROVIDER, DEFAULT_POST_PROCESS,
    USE_OPENAI, OPENAI_DEFAULT_MODEL, OPENAI_MODELS
)

class RecordingController:
    """Terminal-based recording controller using keyboard input in the main thread"""
    def __init__(self, recorder, session_manager):
        """Initialize the recording controller with recorder and session manager"""
        self.recorder = recorder
        self.session_manager = session_manager
        self.running = True
        self.paused = False
        self.current_segment = 1
        
    def start(self):
        """Start the controller in a loop"""
        self.recorder.start_recording()
        self._show_instructions()
        
        try:
            while self.running:
                # Get keyboard input without using keyboard module
                cmd = input("\nCommand (p/r/s/l/q): ").strip().lower()
                
                if cmd == 'p':  # Pause
                    self._pause()
                elif cmd == 'r':  # Resume
                    self._resume()
                elif cmd == 's':  # New Segment
                    self._new_segment()
                elif cmd == 'l':  # Generate lab book
                    self._generate_labbook()
                elif cmd == 'q':  # Quit
                    self._end_session()
                else:
                    print("Unknown command. Try again.")
        
        except KeyboardInterrupt:
            print("\nReceived interrupt. Ending session...")
            self._end_session()
            
        except Exception as e:
            print(f"\nError: {e}")
            self._end_session()
    
    def _pause(self):
        """Pause recording"""
        if not self.paused:
            self.recorder.pause_recording()
            self.paused = True
            print("\n⏸️  Recording paused.")
        else:
            print("\nAlready paused.")
    
    def _resume(self):
        """Resume recording"""
        if self.paused:
            self.recorder.resume_recording()
            self.paused = False
            print("\n▶️  Recording resumed.")
        else:
            print("\nAlready recording.")
    
    def _new_segment(self):
        """Start a new recording segment"""
        self.recorder.stop_recording()
        audio_file = self.recorder.get_last_recording()
        if audio_file:
            self.session_manager.add_recording(audio_file)
            print(f"\n📁 Saved segment {self.current_segment} to session")
            self.current_segment += 1
        
        # Start a new recording segment
        time.sleep(0.5)  # Brief pause between recordings
        self.recorder.start_recording()
        print(f"\n🎤 Started new recording segment {self.current_segment}")
    
    def _generate_labbook(self):
        """Generate interim lab book"""
        # Pause recording temporarily
        was_paused = self.paused
        if not was_paused:
            self.recorder.pause_recording()
            self.paused = True
        
        print("\n📔 Generating interim lab book...")
        
        # Save current recording segment
        temp_file = self.recorder.save_current_segment()
        if temp_file:
            self.session_manager.add_recording(temp_file)
        
        # Generate lab book
        self.session_manager.generate_labbook()
        
        # Resume if it wasn't paused before
        if not was_paused:
            self.recorder.resume_recording()
            self.paused = False
            
        print("\n✅ Interim lab book generated. Recording continues.")
    
    def _end_session(self):
        """End recording session"""
        print("\n🛑 Ending session and generating lab book...")
        self.recorder.stop_recording()
        audio_file = self.recorder.get_last_recording()
        if audio_file:
            self.session_manager.add_recording(audio_file)
            
        self.session_manager.end_session(generate_labbook=True)
        self.running = False
        print("\n✅ Session ended and lab book generated.")
    
    def _show_instructions(self):
        """Display instructions"""
        print("\n🎤 Recording controls:")
        print("  p - Pause recording")
        print("  r - Resume recording")
        print("  s - Save current segment and start a new one")
        print("  l - Generate lab book without ending session")
        print("  q - End session and generate final lab book")
        print("  (You can also press Ctrl+C to end the session)")
        print("\n🎤 Recording active - Speak clearly for best results")

def record_with_terminal_controls(args):
    """Record using terminal-based controls"""
    # Initialize recorder without noise filtering for stability
    recorder = RobustAudioRecorder()
    
    # Initialize session manager with cycle_id if provided
    session_manager = SessionManager(
        session_id=args.session_id,
        cycle_id=args.cycle_id or DEFAULT_LAB_CYCLE,
        whisper_model=args.whisper_model,
        llm_model=args.model,
        use_openai=args.use_openai,
        openai_model=args.openai_model
    )
    
    # Initialize controller
    controller = RecordingController(recorder, session_manager)
    
    print("\n=== Lab Book Generator: Terminal Controls ===\n")
    print("Starting new recording session...")
    
    # Start controller
    controller.start()

def process_audio_file(audio_path, model_path=None, whisper_model='base', 
                       output_format='both', custom_prompt=None, cycle_id=None,
                       post_process=DEFAULT_POST_PROCESS, api_provider=DEFAULT_API_PROVIDER,
                       use_openai=None, openai_model=None):
    """Process an audio file to generate a lab book"""
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return None
    
    print(f"Processing audio file: {audio_path}")
    
    # Step 1: Speech recognition and diarization
    speech_processor = EnhancedSpeechProcessor(whisper_model=whisper_model)
    transcript_file, transcript_data = speech_processor.process_audio(audio_path)
    
    # Get the main transcript and external comments
    transcript_text = transcript_data["full_text"]
    external_comments = transcript_data.get("external_text", "")
    
    print("\nTranscript Summary:")
    print(f"Duration: {transcript_data['duration']:.2f} seconds")
    print(f"Language: {transcript_data['language']}")
    
    speaker_categories = transcript_data.get("speaker_categories", {})
    speakers_by_role = {}
    for speaker_id, data in speaker_categories.items():
        role = data.get("role", "unknown")
        if role not in speakers_by_role:
            speakers_by_role[role] = []
        speakers_by_role[role].append(data.get("label", speaker_id))
    
    print(f"Primary speakers: {', '.join(speakers_by_role.get('primary', ['None detected']))}")
    print(f"External speakers: {', '.join(speakers_by_role.get('external', ['None detected']))}")
    
    # Step 2: Get RAG context if cycle_id is provided
    rag_context = ""
    if cycle_id:
        try:
            lab_cycle_manager = LabCycleManager()
            
            # Use the first 1000 characters of transcript as query
            query = transcript_text[:1000]
            rag_context = lab_cycle_manager.get_knowledge_context(
                cycle_id, query, max_results=3, format_for_prompt=True
            )
            
            if rag_context:
                print("Retrieved relevant context from previous sessions in this lab cycle")
        except Exception as e:
            print(f"Error retrieving RAG context: {e}")
    
    # Step 3: Load custom prompt if provided
    if custom_prompt and os.path.exists(custom_prompt):
        with open(custom_prompt, 'r') as f:
            prompt_template = f.read()
    else:
        prompt_template = None
    
    # Step 4: Generate lab book using LLM
    llm = LLMInterface(
        model_path=model_path,
        use_openai=use_openai,
        openai_model=openai_model
    )
    
    lab_book_content = llm.generate_lab_book(
        transcript_text, 
        prompt_template, 
        rag_context=rag_context,
        external_comments=external_comments
    )
    
    # Step 5: Create document
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
    
    # Step 6: Post-process with advanced LLM if requested
    if post_process:
        print("\nPost-processing lab book with advanced LLM...")
        try:
            analysis = llm.post_process_with_external_api(
                lab_book_content, 
                api_provider=api_provider
            )
            
            # Save analysis to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = os.path.join(OUTPUT_DIR, f"analysis_{timestamp}.md")
            
            with open(analysis_file, 'w') as f:
                f.write(f"# Analysis of Lab Book: {title}\n\n")
                f.write(analysis)
            
            print(f"Analysis saved to: {analysis_file}")
            output_files.append(analysis_file)
        except Exception as e:
            print(f"Error during post-processing: {e}")
            print("Continuing without post-processing analysis")
    
    # Step 7: If part of a lab cycle, add to knowledge base
    if cycle_id and output_format in ['markdown', 'both']:
        try:
            lab_cycle_manager = LabCycleManager()
            
            # Add to knowledge base
            document_id = lab_cycle_manager.add_document_to_knowledge_base(
                cycle_id,
                lab_book_content,
                title=title,
                document_id=f"labbook_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                metadata={"source_file": audio_path}
            )
            
            # Update the index
            lab_cycle_manager.build_knowledge_base_index(cycle_id)
            print(f"Added lab book to knowledge base for cycle '{cycle_id}'")
        except Exception as e:
            print(f"Error adding to knowledge base: {e}")
    
    return output_files

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

def list_sessions():
    """List all available sessions"""
    sessions = SessionManager.list_sessions()
    
    print("\nAvailable Sessions:")
    if sessions:
        # Sort sessions by start time (newest first)
        sessions.sort(key=lambda s: s.get("start_time", ""), reverse=True)
        
        for session in sessions:
            start_time = datetime.fromisoformat(session["start_time"]).strftime('%Y-%m-%d %H:%M:%S')
            end_time = "In Progress"
            if session["end_time"]:
                end_time = datetime.fromisoformat(session["end_time"]).strftime('%Y-%m-%d %H:%M:%S')
            
            cycle_info = f" (Cycle: {session['cycle_id']})" if session.get('cycle_id') else ""
            duration = f"{session['total_duration']:.2f}s"
            print(f"  Session: {session['session_id']}{cycle_info}")
            print(f"    Started: {start_time}")
            print(f"    Ended: {end_time}")
            print(f"    Recordings: {session['recordings']}")
            print(f"    Total Duration: {duration}")
            print(f"    Lab Books: {session['lab_books']}")
            print("")
    else:
        print("  No sessions found")

def list_lab_cycles():
    """List all available lab cycles"""
    lab_cycle_manager = LabCycleManager()
    cycles = lab_cycle_manager.list_lab_cycles()
    
    print("\nAvailable Lab Cycles:")
    if cycles:
        # Sort cycles by creation date (newest first)
        cycles.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        
        for cycle in cycles:
            created_at = datetime.fromisoformat(cycle["created_at"]).strftime('%Y-%m-%d %H:%M:%S')
            session_count = len(cycle.get("sessions", []))
            doc_count = cycle.get("knowledge_base", {}).get("document_count", 0)
            
            print(f"  Cycle: {cycle['cycle_id']} - {cycle['title']}")
            print(f"    Created: {created_at}")
            print(f"    Sessions: {session_count}")
            print(f"    Knowledge Base Documents: {doc_count}")
            if cycle.get("description"):
                print(f"    Description: {cycle['description']}")
            print("")
    else:
        print("  No lab cycles found")

def process_session(session_id, model_path=None, whisper_model='base', 
                   output_format='both', custom_prompt=None, cycle_id=None,
                   post_process=DEFAULT_POST_PROCESS, api_provider=DEFAULT_API_PROVIDER,
                   use_openai=None, openai_model=None):
    """Process an existing session to generate a lab book"""
    try:
        # Load the session
        session = SessionManager.load_session(
            session_id=session_id,
            cycle_id=cycle_id,  # Will auto-detect if not provided
            whisper_model=whisper_model,
            llm_model=model_path,
            use_openai=use_openai,
            openai_model=openai_model
        )
        
        # Generate lab book
        output_files = session.generate_labbook(
            output_format=output_format,
            custom_prompt=custom_prompt,
            post_process=post_process,
            api_provider=api_provider
        )
        
        if not output_files:
            print("\nFailed to generate lab book for this session.")
            return None
        
        print("\nLab book generated successfully!")
        print(f"Output files: {', '.join(output_files)}")
        
        return output_files
        
    except Exception as e:
        print(f"Error processing session: {e}")
        return None

def create_lab_cycle(cycle_id, title, description=None):
    """Create a new lab cycle"""
    lab_cycle_manager = LabCycleManager()
    
    try:
        lab_cycle_manager.create_lab_cycle(cycle_id, title, description)
        print(f"Created lab cycle: {title} (ID: {cycle_id})")
        
        if description:
            print(f"Description: {description}")
        
    except ValueError as e:
        print(f"Error creating lab cycle: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Lab Book Generator (with lab cycles and advanced features)')
    
    # Main operation modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--record', action='store_true', help='Start audio recording')
    mode_group.add_argument('--process', type=str, help='Process an existing audio file')
    mode_group.add_argument('--list', action='store_true', help='List available recordings and lab books')
    mode_group.add_argument('--sessions', action='store_true', help='List all recorded sessions')
    mode_group.add_argument('--process-session', type=str, help='Process an existing session')
    mode_group.add_argument('--create-cycle', type=str, help='Create a new lab cycle with provided ID')
    mode_group.add_argument('--cycles', action='store_true', help='List all lab cycles')
    
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
    parser.add_argument('--session-id', type=str, help='Specify a session ID')
    parser.add_argument('--cycle-id', type=str, help='Specify a lab cycle ID')
    parser.add_argument('--context-size', type=int, default=8192, 
                        help='Context size for the LLM (for large transcripts)')
    parser.add_argument('--cycle-title', type=str, help='Title for new lab cycle', default='Untitled')
    parser.add_argument('--cycle-desc', type=str, help='Description for new lab cycle', default='')
    parser.add_argument('--post-process', action='store_true', default=DEFAULT_POST_PROCESS,
                        help='Post-process with advanced LLM API')
    parser.add_argument('--no-post-process', action='store_true',
                        help='Skip post-processing with advanced LLM API')
    parser.add_argument('--api', type=str, choices=['openai', 'anthropic'], 
                        default=DEFAULT_API_PROVIDER, help='API provider for post-processing')
    
    # New arguments for OpenAI integration
    parser.add_argument('--use-openai', action='store_true', default=USE_OPENAI,
                        help='Use OpenAI API instead of local LLM')
    parser.add_argument('--use-local', action='store_true',
                        help='Use local LLM (Ollama) instead of OpenAI API')
    parser.add_argument('--openai-model', type=str, choices=OPENAI_MODELS,
                        default=OPENAI_DEFAULT_MODEL, help='Specify the OpenAI model to use')
    
    args = parser.parse_args()
    
    # Update config if context size is specified
    if args.context_size:
        from config import LLM_CONTEXT_SIZE
        LLM_CONTEXT_SIZE = args.context_size
    
    # Determine use_openai flag (--use-local overrides --use-openai)
    use_openai = args.use_openai
    if args.use_local:
        use_openai = False
    
    # Determine post-processing flag (--no-post-process overrides --post-process)
    post_process = args.post_process
    if args.no_post_process:
        post_process = False
    
    if args.record:
        # Record with terminal-based controls
        record_with_terminal_controls(args)
    
    elif args.process:
        # Process an existing audio file
        print("\n=== Lab Book Generator: Processing Mode ===\n")
        process_audio_file(
            args.process, 
            model_path=args.model,
            whisper_model=args.whisper_model,
            output_format=args.output_format,
            custom_prompt=args.prompt,
            cycle_id=args.cycle_id,
            post_process=post_process,
            api_provider=args.api,
            use_openai=use_openai,
            openai_model=args.openai_model
        )
    
    elif args.process_session:
        # Process an existing session
        print("\n=== Lab Book Generator: Session Processing Mode ===\n")
        process_session(
            args.process_session,
            model_path=args.model,
            whisper_model=args.whisper_model,
            output_format=args.output_format,
            custom_prompt=args.prompt,
            cycle_id=args.cycle_id,
            post_process=post_process,
            api_provider=args.api,
            use_openai=use_openai,
            openai_model=args.openai_model
        )
    
    elif args.list:
        # List available files
        print("\n=== Lab Book Generator: File Listing ===")
        list_files()
    
    elif args.sessions:
        # List available sessions
        print("\n=== Lab Book Generator: Session Listing ===")
        list_sessions()
    
    elif args.create_cycle:
        # Create a new lab cycle
        if not args.cycle_title:
            print("Error: --cycle-title is required when creating a lab cycle")
            return
            
        print("\n=== Lab Book Generator: Create Lab Cycle ===")
        create_lab_cycle(
            args.create_cycle,
            args.cycle_title,
            args.cycle_desc
        )
    
    elif args.cycles:
        # List available lab cycles
        print("\n=== Lab Book Generator: Lab Cycle Listing ===")
        list_lab_cycles()

if __name__ == "__main__":
    main()