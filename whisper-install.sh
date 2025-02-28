#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Installing Whisper from GitHub...${NC}"
pip install git+https://github.com/openai/whisper.git

echo -e "${GREEN}Installing FFmpeg if needed (for audio processing)...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    brew install ffmpeg
fi

echo -e "${YELLOW}Installing other essential components...${NC}"
pip install pyannote.audio
pip install torch torchvision torchaudio

echo -e "${YELLOW}Installing LLaMA-cpp with Metal support for M1...${NC}"
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python

echo -e "${YELLOW}Installing additional requirements...${NC}"
pip install transformers
pip install python-docx markdown fpdf
pip install Pillow opencv-python
pip install numpy tqdm

echo -e "${GREEN}Installation complete!${NC}"