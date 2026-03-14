# 🎤 Voice Transcriber - Real-Time Speech-to-Text

<div align="center">

**Transform speech into text instantly. Professional transcription made simple.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub stars](https://img.shields.io/github/stars/sabilashang/voice_transcribe?style=social)](https://github.com/sabilashang/voice_transcribe)

[🚀 Quick Start](#quick-start) • [📖 Documentation](#usage) • [💡 Features](#key-features) • [🎯 Use Cases](#use-cases)

</div>

---

## ✨ What Makes This Special?

**Watch your words appear on screen as you speak.** This isn't batch processing—it's **true continuous transcription**. Speak naturally, pause briefly, and within **~1 second**, your words appear on screen. Perfect for meetings, interviews, lectures, or any scenario where you need instant transcription.

### 🎯 Key Features

#### 🎤 **Continuous Real-Time Transcription**
- **Text appears ~1 second after you speak** - No waiting, no batching
- **Truly continuous** - Keeps listening and transcribing as long as you're recording
- **Natural pause detection** - Adapts to your speaking rhythm (detects pauses in ~0.6 seconds)
- **Low latency** - From speech to text in 1-2 seconds
- **Live display** - See your words appear in real-time as you speak
- Perfect for live meetings, interviews, lectures, and note-taking

#### 📁 **File Transcription**
- **Multi-file support** - Queue and process multiple audio files
- **Smart chunking** - Handles files from seconds to **3+ hours** seamlessly
- **Pause-aware splitting** - Breaks long files at natural pauses for better accuracy
- **Live progress** - Watch transcription stream in real-time for large files
- **Disfluency cleanup** - Automatically removes "um", "uh", and other fillers

#### 🎨 **Beautiful Modern Interface**
- **Neumorphism/Liquid Glass design** - Sleek, modern UI that's a joy to use
- **Smooth animations** - Polished interactions throughout
- **Responsive controls** - Intuitive buttons that do exactly what they say
- **Real-time feedback** - Progress bars, status updates, and live text display

#### 🔧 **Powerful & Flexible**
- **Multiple audio formats** - WAV, MP3, M4A, FLAC, OGG, AAC
- **Multiple export formats** - TXT, JSON, CSV, SRT subtitles, VTT
- **Audio enhancement** - Automatic noise reduction and volume normalization
- **Multi-language support** - English, Spanish, French, German, and more
- **Cloud engines** - Google (high accuracy), Azure, Bing

#### 👥 **Speaker Detection** *(In Development)*
- Advanced ML-based speaker identification
- Voice profile creation and matching
- Available from dedicated tabs (experimental)

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

### 🎙️ Live Transcription - How It Works

**The magic happens in real-time:**

1. **Click Record (🔴)** - System calibrates your microphone (~1 second)
2. **Start Speaking** - Talk naturally, at your own pace
3. **Watch the Magic** - **Within ~1 second of your pause**, your words appear on screen
4. **Keep Going** - The system continuously listens and transcribes
5. **Pause/Resume** - Use ⏸️ to pause, ▶️ to resume, ⏹️ to stop

**What makes it special:**
- ✅ **Truly continuous** - Never stops listening while recording
- ✅ **Natural rhythm** - Detects when you pause (not fixed time chunks)
- ✅ **Instant feedback** - See your words appear ~1 second after speaking
- ✅ **No interruption** - Keep talking, it keeps transcribing

**Pro Tip**: Speak naturally with brief pauses between phrases. The system adapts to your speaking style automatically. See [LIVE_TRANSCRIPTION_GUIDE.md](LIVE_TRANSCRIPTION_GUIDE.md) for advanced tips.

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

## 🎯 Perfect For

| Use Case | Why It's Perfect |
|----------|------------------|
| **📝 Live Note-Taking** | Speak your notes, see them appear instantly. Perfect for lectures, meetings, or brainstorming |
| **🎙️ Meeting Transcription** | Record entire meetings with continuous transcription. Export for sharing or archiving |
| **🎬 Content Creation** | Transcribe podcasts, videos, or interviews. Export as subtitles (SRT/VTT) or transcripts |
| **📚 Research & Interviews** | Capture research interviews with real-time transcription. No need to replay audio |
| **⚖️ Legal Documentation** | Create accurate transcripts of depositions, proceedings, or client meetings |
| **🎓 Educational Content** | Transcribe lectures, webinars, or educational videos for accessibility |
| **💼 Business Meetings** | Never miss important points. Continuous transcription keeps up with fast-paced discussions |

## ⚡ Technical Highlights

### 🎤 Real-Time Speech Recognition
- **Multiple engines**: Google Speech API (high accuracy), Azure, Bing
- **Multi-language**: English (US/UK), Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese
- **High accuracy**: >90% for clear speech with automatic retry logic
- **Continuous processing**: Listens and transcribes continuously, not in fixed chunks
- **Low latency**: ~1 second from speech pause to text display

### 📊 Performance & Scalability
- **Real-time processing** - Instant transcription for live speech
- **Large file support** - Handles files from seconds to **3+ hours** seamlessly
- **Smart chunking** - Intelligent pause-aware splitting for long files
- **Memory efficient** - Streaming processing for 100+ MB files
- **Audio enhancement** - Automatic noise reduction and volume normalization
- **Disfluency removal** - Cleans up "um", "uh", and other fillers automatically

### 👥 Speaker Detection *(In Development)*
- Advanced ML-based voice feature extraction (MFCC, spectral features)
- Automatic speaker clustering and identification
- Voice profile creation and matching
- **Note**: Available from dedicated tabs, marked as experimental
- **Core transcription works perfectly without it** - speaker detection is optional

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

## License & Attribution

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the `LICENSE` file for details.

If you use this project's **ideas, structure, or overall design** (including the real-time transcription flow, tab layout, or UI/UX patterns), please provide clear **attribution** in your project documentation, such as:

> "Based on the `voice_transcribe` project by the Voice Transcriber Contributors (`https://github.com/sabilashang/voice_transcribe`)."

## Acknowledgments

Built with:
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - Speech-to-text
- [Librosa](https://librosa.org/) - Audio processing
- [PyAnnote](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI

---

## 🌟 Why Choose Voice Transcriber?

✅ **Truly Continuous** - Not batch processing. Real-time transcription that keeps up with you  
✅ **Beautiful UI** - Modern, intuitive interface that's a joy to use  
✅ **Production Ready** - Handles everything from quick notes to 3-hour recordings  
✅ **Open Source** - GPL-3.0 licensed, free to use, modify, and share under the same terms  
✅ **Cross-Platform** - Works on Windows, macOS, and Linux  

## 📸 Screenshots

*Coming soon - Beautiful UI screenshots*

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [`LICENSE`](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for better conversations**

[⭐ Star this repo](https://github.com/sabilashang/voice_transcribe) • [🐛 Report Bug](https://github.com/sabilashang/voice_transcribe/issues) • [💡 Request Feature](https://github.com/sabilashang/voice_transcribe/issues)

</div>
