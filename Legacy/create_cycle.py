#!/usr/bin/env python
# create_cycle.py - Lightweight script for creating lab cycles
import os
import json
import sys
from datetime import datetime
import argparse

# Simplified version of get_cycle_paths that doesn't require importing config.py
def get_cycle_paths(cycle_id):
    """Get standard paths for a specific lab cycle"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    lab_cycles_dir = os.path.join(data_dir, "lab_cycles")
    
    cycle_dir = os.path.join(lab_cycles_dir, cycle_id)
    
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

def create_lab_cycle(cycle_id, title, description=None):
    """Create a new lab cycle without loading heavy dependencies"""
    print(f"Creating lab cycle: {title} (ID: {cycle_id})")
    
    # Create basic directory structure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    lab_cycles_dir = os.path.join(data_dir, "lab_cycles")
    
    # Ensure the lab_cycles directory exists
    os.makedirs(lab_cycles_dir, exist_ok=True)
    
    cycle_dir = os.path.join(lab_cycles_dir, cycle_id)
    
    if os.path.exists(cycle_dir):
        print(f"Error: Lab cycle '{cycle_id}' already exists")
        return False
    
    # Create directories using the helper function
    paths = get_cycle_paths(cycle_id)
    
    # Create metadata
    metadata = {
        "cycle_id": cycle_id,
        "title": title,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "sessions": [],
        "knowledge_base": {
            "indexed": False,
            "last_updated": None,
            "document_count": 0
        }
    }
    
    # Save metadata
    with open(os.path.join(paths["root"], "metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Created lab cycle: {title} (ID: {cycle_id})")
    if description:
        print(f"Description: {description}")
    
    return True

def list_lab_cycles():
    """List all available lab cycles"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    lab_cycles_dir = os.path.join(data_dir, "lab_cycles")
    
    # Ensure the lab_cycles directory exists
    if not os.path.exists(lab_cycles_dir):
        print("No lab cycles directory found. You haven't created any cycles yet.")
        return
    
    cycles = []
    
    for item in os.listdir(lab_cycles_dir):
        cycle_dir = os.path.join(lab_cycles_dir, item)
        metadata_file = os.path.join(cycle_dir, "metadata.json")
        
        if os.path.isdir(cycle_dir) and os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                cycles.append(metadata)
            except Exception as e:
                print(f"Error loading metadata for cycle {item}: {e}")
    
    if not cycles:
        print("No lab cycles found")
        return
    
    print("\nAvailable Lab Cycles:")
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

def main():
    parser = argparse.ArgumentParser(description='Lightweight Lab Cycle Manager')
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--create', type=str, help='Create a new lab cycle with provided ID')
    action_group.add_argument('--list', action='store_true', help='List all lab cycles')
    
    # Optional arguments
    parser.add_argument('--title', type=str, help='Title for new lab cycle', default='Untitled')
    parser.add_argument('--desc', type=str, help='Description for new lab cycle', default='')
    
    args = parser.parse_args()
    
    if args.create:
        create_lab_cycle(args.create, args.title, args.desc)
    elif args.list:
        list_lab_cycles()

if __name__ == "__main__":
    main()