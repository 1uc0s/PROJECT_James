# Automated Lab Book Generator

A Python application that records lab sessions, identifies speakers, and uses a local LLM to generate structured lab books with multimodal support.

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

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure a local LLM:
   - Download a suitable LLM model (e.g., Llama 3, Mistral, Falcon)
   - Update `LLM_MODEL_PATH` in `config.py` with the path to your model

5. Set up speaker diarization (optional):
   - Create an account on HuggingFace
   - Generate an access token
   - Set the token as an environment variable: `export HF_TOKEN=your_token_here`

## Usage

### Record a New Lab Session

```bash
python main.py --record
```

This will start recording. Press `Ctrl+C` to stop recording and begin processing.

### Process an Existing Audio File

```bash
python main.py --process path/to/audio_file.wav
```

### Add an Image to the Latest Lab Book

```bash
python main.py --add-image path/to/image.png
```

### List Available Files

```bash
python main.py --list
```

### Additional Options

- `--output-format`: Choose output format (`markdown`, `docx`, or `both`)
- `--model`: Specify a custom LLM model path
- `--whisper-model`: Select Whisper model size (`tiny`, `base`, `small`, `medium`, `large`)
- `--max-duration`: Set maximum recording duration in seconds
- `--prompt`: Use a custom prompt template file

Example:
```bash
python main.py --record --output-format markdown --whisper-model small --max-duration 600
```

## Customization

### Lab Book Structure

You can customize the lab book structure by:
1. Modifying the `LAB_BOOK_SECTIONS` list in `config.py`
2. Editing the template file at `templates/labbook_template.md`
3. Creating a custom prompt file and using it with `--prompt`

### LLM Configuration

Adjust LLM parameters in `config.py`:
- `LLM_CONTEXT_SIZE`: Maximum context window size
- `LLM_TEMPERATURE`: Controls randomness in generation (0.0-1.0)
- `LLM_MAX_TOKENS`: Maximum tokens to generate

## Requirements

- Python 3.8+
- PyAudio and related audio libraries
- OpenAI Whisper
- PyAnnote Audio (for speaker diarization)
- llama-cpp-python
- OpenCV and PIL for image processing
- Various utilities for document generation

## Known Limitations

- Speaker diarization requires a HuggingFace token
- The quality of lab book generation depends on the LLM used
- Multimodal analysis requires a capable LLM with image understanding
- The application does not currently support real-time transcription

## License

[MIT License](LICENSE)
