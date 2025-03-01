# Automated Lab Book Generator V2

A Python application that records lab sessions, identifies speakers, and uses LLMs to generate structured lab books with multimodal support, lab cycle organization, and advanced analysis.

## New Features in V2

- **Lab Cycle Organization**: Group related lab sessions into cycles (e.g., "Wave Experiments")
- **RAG Knowledge Base**: Each lab cycle builds a knowledge base for improved context in future sessions
- **Enhanced Speaker Diarization**: Better distinguish between the primary user and external speakers
- **External Comments Section**: Lab partner or demonstrator comments are properly categorized
- **Post-Processing Analysis**: Get feedback and improvement suggestions from advanced LLMs

## Features

- **Audio Recording**: Captures lab sessions with automatic silence detection
- **Speech Recognition**: Transcribes audio using OpenAI's Whisper
- **Speaker Diarization**: Identifies different speakers in the recording
- **Lab Book Generation**: Creates structured lab books using a local LLM
- **Multimodal Support**: Analyzes graphs and images for inclusion in lab books
- **Multiple Output Formats**: Generates lab books in Markdown and/or DOCX format

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/labbook-generator.git
   cd labbook-generator
   ```

2. Run the setup script:
   ```bash
   chmod +x setup-v2.sh
   ./setup-v2.sh
   ```

3. (Optional) Set API keys for advanced post-processing:
   ```bash
   export OPENAI_API_KEY=your_openai_key_here
   export ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

4. (Optional) Set up speaker diarization with HuggingFace:
   ```bash
   export HF_TOKEN=your_huggingface_token_here
   ```

## Usage

### Create a Lab Cycle

Organize your lab sessions into cycles:

```bash
python main_updated.py --create-cycle waves --cycle-title "Wave Experiments" --cycle-desc "Lab experiments focusing on wave properties and interference"
```

### Record a Lab Session in a Cycle

```bash
python main_updated.py --record --cycle-id waves
```

This will start recording. Use the following commands during recording:
- `p` - Pause recording
- `r` - Resume recording
- `s` - Save current segment and start a new one
- `l` - Generate interim lab book
- `q` or `Ctrl+C` - End session and generate lab book

### Process an Existing Audio File

```bash
python main_updated.py --process path/to/audio_file.wav --cycle-id waves
```

### List Lab Cycles

```bash
python main_updated.py --cycles
```

### List Sessions in a Cycle

```bash
python main_updated.py --sessions
```

### Additional Options

- `--output-format`: Choose output format (`markdown`, `docx`, or `both`)
- `--model`: Specify a custom LLM model path
- `--whisper-model`: Select Whisper model size (`tiny` to `large`)
- `--post-process`: Enable analysis with advanced LLM APIs (default if API keys available)
- `--no-post-process`: Disable advanced LLM post-processing
- `--api`: Choose API provider for post-processing (`openai` or `anthropic`)

Example:
```bash
python main_updated.py --record --cycle-id waves --output-format markdown --whisper-model small --api anthropic
```

## Lab Cycle RAG System

The RAG (Retrieval Augmented Generation) system automatically:
1. Stores all lab book content in a knowledge base for each lab cycle
2. Retrieves relevant context from previous lab sessions when generating new lab books
3. Provides continuity and knowledge transfer between related sessions

## Enhanced Speaker Diarization

The system now:
1. Distinguishes between the primary user and external speakers
2. Creates a separate "External Comments" section in the lab book
3. Maintains profiles for known speakers for better identification

## Post-Processing with Advanced LLMs

After generating a lab book, the system can:
1. Send the content to OpenAI or Anthropic APIs for advanced analysis
2. Receive feedback on strengths, weaknesses, and potential improvements
3. Get suggestions for follow-up experiments or additional analyses

## Configuration

Edit `config_updated.py` to customize:
- Default lab cycle
- LLM parameters 
- Speaker diarization settings
- RAG system configuration
- Post-processing options

## Known Limitations

- Speaker diarization accuracy depends on audio quality and speaker separation
- RAG context retrieval requires sufficient previous lab content
- Advanced post-processing requires API keys and internet access

## License

[MIT License](LICENSE)