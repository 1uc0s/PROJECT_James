#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Enhanced Lab Book Generator V2...${NC}"

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

# Install core dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"

# PyAudio often needs portaudio on Mac
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Installing portaudio with Homebrew (if needed)...${NC}"
    if command -v brew &> /dev/null; then
        if ! brew list portaudio &>/dev/null; then
            brew install portaudio
        fi
    else
        echo -e "${RED}Homebrew not found. Please install Homebrew to continue.${NC}"
        exit 1
    fi
fi

# Sound related packages
pip install pyaudio
pip install sounddevice
pip install pydub
pip install noisereduce

# Whisper for speech recognition
echo -e "${YELLOW}Installing Whisper from GitHub...${NC}"
pip install git+https://github.com/openai/whisper.git

# FFmpeg is required for Whisper
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}Installing FFmpeg...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        echo -e "${RED}Please install FFmpeg manually for your system${NC}"
    fi
fi

# Install PyTorch with appropriate backend
echo -e "${YELLOW}Installing PyTorch...${NC}"
if [[ "$OSTYPE" == "darwin"* ]] && [[ $(uname -m) == 'arm64' ]]; then
    # M1/M2 Mac
    pip install torch torchvision torchaudio
else
    # Other systems
    pip install torch torchvision torchaudio
fi

# Install PyAnnote for speaker diarization
echo -e "${YELLOW}Installing PyAnnote Audio...${NC}"
pip install pyannote.audio

# RAG dependencies (NEW)
echo -e "${YELLOW}Installing RAG dependencies...${NC}"
pip install faiss-cpu
pip install sentence-transformers
pip install scikit-learn

# LLM integration
echo -e "${YELLOW}Installing LLM integration...${NC}"
if [[ "$OSTYPE" == "darwin"* ]] && [[ $(uname -m) == 'arm64' ]]; then
    # M1/M2 Mac with Metal support
    CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
else
    pip install llama-cpp-python
fi
pip install transformers

# API clients for post-processing (NEW)
echo -e "${YELLOW}Installing API clients...${NC}"
pip install openai
pip install anthropic

# Image processing
pip install Pillow
pip install opencv-python

# Document generation
pip install python-docx
pip install markdown
pip install fpdf

# Utilities
pip install numpy
pip install tqdm

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Important:${NC} For Ollama integration, ensure Ollama is installed and running."
echo -e "Visit https://ollama.com/ to download Ollama, then run 'ollama serve' in another terminal."
echo -e "Install the model with: ${GREEN}ollama pull llama3.2${NC}"

echo -e "\n${YELLOW}New Features:${NC}"
echo -e "- Lab cycle organization with RAG"
echo -e "- Enhanced speaker diarization"
echo -e "- Post-processing with external LLMs (requires API keys)"

echo -e "\nTo set API keys for post-processing:"
echo -e "export OPENAI_API_KEY=your_openai_key_here"
echo -e "export ANTHROPIC_API_KEY=your_anthropic_key_here"

echo -e "\nTo start the lab book generator, run: ${GREEN}python main_updated.py --record${NC}"
echo -e "To create a new lab cycle: ${GREEN}python main_updated.py --create-cycle cycle1 --cycle-title \"Wave Experiments\"${NC}"