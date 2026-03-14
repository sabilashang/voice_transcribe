# Voice Transcriber with Speaker Detection

> Professional-grade speech-to-text transcription with automatic speaker identification and diarization.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Voice Transcriber is a comprehensive Python-based system that converts speech to text while automatically identifying and distinguishing between different speakers. Built with a modern, intuitive GUI and powered by advanced machine learning, it makes professional transcription accessible to everyone.

### Key Features

- **🎤 True Live Transcription** - Continuous real-time speech-to-text that adapts to your natural speaking rhythm
  - Text appears immediately after you pause speaking (0.6s detection)
  - No fixed time chunks - transcribes when you naturally pause
  - Low latency: 1-2 seconds from speech to text
  - See [LIVE_TRANSCRIPTION_GUIDE.md](LIVE_TRANSCRIPTION_GUIDE.md) for detailed usage
- **👥 Automatic Speaker Detection** - Identify and distinguish up to 10 speakers in conversations
- **🎨 Modern UI** - Beautiful Neumorphism/Liquid Glass interface with smooth animations
- **🔄 Multi-format Support** - Process WAV, MP3, M4A, FLAC, OGG, AAC files
- **📊 Multiple Export Formats** - Save as TXT, JSON, CSV, SRT subtitles, or VTT
- **🎛️ Audio Enhancement** - Automatic noise reduction and volume normalization
- **⚡ Large File Support** - Efficiently handle files up to 2+ hours with automatic chunking

## Quick Start

### 1. Prerequisites

- **Python**: 3.8 or higher (3.10+ recommended)
- **OS**: Windows, macOS, or Linux
- **Audio**: A working microphone (for live transcription)
- **Optional (recommended)**: `ffmpeg` for full `.m4a` / advanced format support  
  - Windows: Download from `https://ffmpeg.org` and add `ffmpeg\bin` to your `PATH`
  - macOS (Homebrew): `brew install ffmpeg`
  - Linux (Debian/Ubuntu): `sudo apt-get install ffmpeg`

### 2. Clone and install

```bash
# Clone the repository
git clone https://github.com/sabilashang/voice_transcribe.git
cd voice_transcribe

# (Recommended) create a virtual environment
python -m venv .venv

# Activate it
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# Install runtime dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the application (GUI)

```bash
# Easiest entrypoint
python launch_gui.py

# Or run the GUI module directly
python voice_transcriber_gui.py
```

This opens the main Troice GUI with all tabs (Transcription, Speaker Detection, Speaker Management, Settings).

### Live Transcription Quick Guide

1. **Click Record (🔴)** - Wait for calibration (1 second)
2. **Start Speaking** - Text appears as you speak
3. **Natural Pauses** - System detects your natural speaking rhythm
4. **Stop When Done** - Click Stop (⏹️) to end recording

**Pro Tip**: Speak naturally and pause briefly between phrases for best results. See [LIVE_TRANSCRIPTION_GUIDE.md](LIVE_TRANSCRIPTION_GUIDE.md) for details.

### Usage

Launch the GUI application from the project root:

```bash
python launch_gui.py
```

The application provides four main tabs:
1. **🎤 Live Transcription** - Record and transcribe in real-time
2. **👥 Speaker Detection** - Identify speakers in audio files
3. **👤 Speaker Management** - Create and manage speaker profiles
4. **⚙️ Settings** - Configure language, engine, and audio settings

## Use Cases

- **Meeting Transcription** - Automatically transcribe and identify speakers in meetings
- **Interview Processing** - Convert interviews to text with speaker labels
- **Podcast Production** - Generate accurate transcripts with speaker identification
- **Legal Documentation** - Create official transcripts of depositions and proceedings
- **Research & Analysis** - Transcribe focus groups and research interviews
- **Content Creation** - Generate subtitles and transcripts for video content

## Technical Highlights

### Speech Recognition
- Multiple engines: Google Speech API, Sphinx (offline), Azure, Bing
- Multi-language support: English, Spanish, French, German, and more
- Accuracy: >90% for clear speech with automatic retry logic

### Speaker Diarization (Optional, In Development)
- Advanced ML-based voice feature extraction (MFCC, spectral features)
- Automatic speaker clustering and identification
- Voice profile creation and matching
- Available from the **Speaker Detection** and **Speaker Management** tabs
- Marked as **experimental / in active development** – APIs and behavior may change
- **Not required** for basic transcription; core speech-to-text works without diarization

### Performance
- Real-time processing for short segments
- Efficient chunking for large files (2+ hours)
- Memory-optimized streaming for 100+ MB files
- Automatic audio enhancement and noise reduction

## Architecture

```
voice_transcribe/
├── voice_transcriber.py        # Core transcription engine
├── speaker_detector.py         # Speaker diarization module
├── audio_processor.py          # Audio enhancement utilities
├── voice_transcriber_gui.py   # Main GUI application
├── launch_gui.py              # Application launcher
├── install.py                 # Automated installer
└── requirements.txt           # Python dependencies
```

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB for models and dependencies
- **Audio**: Microphone for real-time recording
- **OS**: Windows, macOS, Linux

## Configuration

### Language Support
English (US/UK), Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese

### Recognition Engines
- **Google** - High accuracy, requires internet
- **Sphinx** - Offline processing
- **Azure/Bing** - Enterprise options (API key required)

### Long Audio and Large Files

- Files longer than **60 seconds** are processed with intelligent chunking:
  - Base chunk size: **30 seconds**
  - For very long audio (e.g. **3+ hours**), the engine:
    - Keeps internal chunks under ~**20 minutes** to stay within API/time limits
    - Tries to **break at natural pauses** (silence) when approaching that limit
    - Streams recognized text into the GUI as chunks complete
- This makes long recordings (meetings, podcasts, lectures) feel seamless to the user while staying robust against API constraints.

## Development

### Running Tests
```bash
pip install -r requirements-dev.txt
pytest
```

### Code Quality
```bash
black .
flake8 .
```

## Troubleshooting

### PyAudio Installation
```bash
# Windows
pip install pipwin && pipwin install pyaudio

# macOS
brew install portaudio && pip install pyaudio

# Linux (Ubuntu/Debian)
sudo apt-get install python3-pyaudio && pip install pyaudio
```

### Common Issues
- **Microphone not found** - Check permissions and ensure no other app is using it
- **Low accuracy** - Use higher quality audio, reduce background noise
- **Slow processing** - Reduce sample rate or use shorter chunks

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built with:
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - Speech-to-text
- [Librosa](https://librosa.org/) - Audio processing
- [PyAnnote](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI

---

**Made with ❤️ for better conversations**
