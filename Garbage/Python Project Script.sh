#!/bin/bash

# Define the project name (you can change this or make it a script parameter)
PROJECT_NAME="PROJECT_James"

# Create the project directory (uncomment if you want to create a new directory)
# mkdir -p "$PROJECT_NAME"
# cd "$PROJECT_NAME"

# Create main directory structure
echo "Creating project structure for $PROJECT_NAME..."
mkdir -p modules
mkdir -p utils
mkdir -p templates
mkdir -p data
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/output

# Create Python package initialization files
touch modules/__init__.py
touch utils/__init__.py

# Create main Python files
touch main.py
touch config.py

# Create module files
touch modules/audio_capture.py
touch modules/speech_processing.py
touch modules/llm_interface.py
touch modules/document_generator.py
touch modules/image_processor.py

# Create utility files
touch utils/helpers.py

# Create a basic README file
cat > README.md << EOL
# $PROJECT_NAME

## Description
A brief description of your project.

## Project Structure
\`\`\`
.
├── modules/               # Core functionality modules
│   ├── audio_capture.py
│   ├── speech_processing.py
│   ├── llm_interface.py
│   ├── document_generator.py
│   └── image_processor.py
├── utils/                 # Utility functions and helpers
│   └── helpers.py
├── templates/             # Template files
├── data/                  # Data directory
│   ├── raw/               # Raw input data
│   ├── processed/         # Processed data
│   └── output/            # Output data and results
├── main.py                # Main application entry point
├── config.py              # Configuration settings
└── README.md              # This file
\`\`\`

## Installation
Instructions for setting up the project.

## Usage
Instructions for using the project.
EOL

# Create a basic .gitignore file
cat > .gitignore << EOL
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Virtual environments
venv/
env/
ENV/

# Data directories (uncomment if you want to exclude data)
# data/raw/
# data/processed/
# data/output/

# IDE specific files
.idea/
.vscode/
*.swp
*.swo

# OS specific files
.DS_Store
Thumbs.db
EOL

echo "Project structure created successfully!"
echo "Use 'cd $PROJECT_NAME' to enter your project directory (if needed)."
