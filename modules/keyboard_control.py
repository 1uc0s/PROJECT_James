# modules/keyboard_control.py
import keyboard
import threading
import time
import os
import sys
from datetime import datetime

class KeyboardController:
    def __init__(self, recorder, session_manager):
        """Initialize keyboard controller with recorder and session manager"""
        self.recorder = recorder
        self.session_manager = session_manager
        self.listener_thread = None
        self.running = False
        
        # Define default key bindings
        self.pause_key = 'ctrl+space'        # Pause/resume recording
        self.end_key = 'ctrl+shift+e'        # End session and generate lab book
        self.segment_key = 'ctrl+shift+s'    # Mark a new segment in recording
        self.labbook_key = 'ctrl+shift+l'    # Generate lab book without ending session
        
        # Status variables
        self.is_paused = False
        self.current_segment = 1
    
    def start_listening(self):
        """Start listening for keyboard shortcuts"""
        if self.listener_thread and self.listener_thread.is_alive():
            print("Keyboard listener is already running")
            return
        
        self.running = True
        self.listener_thread = threading.Thread(target=self._listener_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
        # Display instructions
        self._show_instructions()
    
    def stop_listening(self):
        """Stop listening for keyboard shortcuts"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)
    
    def _listener_loop(self):
        """Main listener loop for keyboard events"""
        try:
            # Register all handlers
            keyboard.add_hotkey(self.pause_key, self._toggle_pause)
            keyboard.add_hotkey(self.end_key, self._end_session)
            keyboard.add_hotkey(self.segment_key, self._new_segment)
            keyboard.add_hotkey(self.labbook_key, self._generate_labbook)
            
            # Keep thread alive
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in keyboard listener: {e}")
        finally:
            # Clean up
            try:
                keyboard.unhook_all()
            except:
                pass
    
    def _toggle_pause(self):
        """Toggle pause/resume recording"""
        try:
            if not self.is_paused:
                self.recorder.pause_recording()
                self.is_paused = True
                print("\n⏸️  Recording paused. Press Ctrl+Space to resume.")
            else:
                self.recorder.resume_recording()
                self.is_paused = False
                print("\n▶️  Recording resumed. Press Ctrl+Space to pause.")
        except Exception as e:
            print(f"\nError toggling pause: {e}")
    
    def _end_session(self):
        """End the session and generate a lab book"""
        try:
            print("\n🛑 Ending session and generating lab book...")
            self.recorder.stop_recording()
            self.session_manager.end_session(generate_labbook=True)
            self.running = False
            print("\n✅ Session ended and lab book generated.")
        except Exception as e:
            print(f"\nError ending session: {e}")
    
    def _new_segment(self):
        """Start a new recording segment while maintaining the same session"""
        try:
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
        except Exception as e:
            print(f"\nError creating new segment: {e}")
    
    def _generate_labbook(self):
        """Generate a lab book from current session without ending it"""
        try:
            # Pause recording temporarily
            was_paused = self.is_paused
            if not was_paused:
                self.recorder.pause_recording()
                self.is_paused = True
            
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
                self.is_paused = False
                
            print("\n✅ Interim lab book generated. Recording continues.")
        except Exception as e:
            print(f"\nError generating lab book: {e}")
    
    def _show_instructions(self):
        """Display keyboard shortcut instructions"""
        print("\n🎹 Keyboard controls active:")
        print(f"  {self.pause_key} - Pause/resume recording")
        print(f"  {self.segment_key} - Save current segment and start a new one")
        print(f"  {self.labbook_key} - Generate lab book without ending session")
        print(f"  {self.end_key} - End session and generate final lab book")
        print("\n🎤 Recording active - Speak clearly for best results")