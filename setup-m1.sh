#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Lab Book Generator for Mac M1...${NC}"

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install core dependencies one by one
echo -e "${YELLOW}Installing dependencies...${NC}"

# PyAudio often needs portaudio on Mac
echo -e "${YELLOW}Installing portaudio with Homebrew (if needed)...${NC}"
if ! brew list portaudio &>/dev/null; then
    brew install portaudio
fi

# Install Python packages with error handling
install_package() {
    echo -e "${YELLOW}Installing $1...${NC}"
    if pip install $1; then
        echo -e "${GREEN}Successfully installed $1${NC}"
    else
        echo -e "${RED}Failed to install $1${NC}"
        return 1
    fi
}

# Basic audio processing
install_package pyaudio || echo -e "${YELLOW}Trying alternate method for PyAudio...${NC}" && pip install --global-option='build_ext' --global-option='-I/opt/homebrew/include' --global-option='-L/opt/homebrew/lib' pyaudio
install_package sounddevice
install_package pydub

# Speech recognition
echo -e "${YELLOW}Installing OpenAI Whisper...${NC}"
pip install -U openai-whisper

# Install PyTorch with Apple Metal support
echo -e "${YELLOW}Installing PyTorch with Apple Metal support...${NC}"
pip install torch torchvision torchaudio

# Speaker diarization
echo -e "${YELLOW}Installing PyAnnote Audio...${NC}"
pip install pyannote.audio

# LLM integration
echo -e "${YELLOW}Installing LLaMA-cpp with Metal support...${NC}"
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
install_package transformers

# Image processing
install_package Pillow
install_package opencv-python

# Document generation
install_package python-docx
install_package markdown
install_package fpdf

# Utilities
install_package numpy
install_package tqdm

echo -e "${GREEN}Setup complete! Activate the environment with: source venv/bin/activate${NC}"