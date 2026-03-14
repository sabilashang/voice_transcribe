# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-31

### Added
- Real-time live transcription with visual feedback
- Automatic speaker detection and diarization
- Multi-format audio support (WAV, MP3, M4A, FLAC, OGG, AAC)
- Modern Neumorphism/Liquid Glass UI design
- Multiple export formats (TXT, JSON, CSV, SRT, VTT)
- Audio enhancement with automatic noise reduction
- Volume normalization and boosting for quiet audio
- Large file support with automatic chunking (2+ hours)
- Retry logic with exponential backoff
- Speaker profile creation and management
- Multi-language support (10+ languages)
- Multiple recognition engines (Google, Azure, Bing)
- Settings persistence across sessions
- Progress tracking with animated indicators
- Toast notifications for non-blocking feedback
- Drag-and-drop file support
- Live transcription display during processing

### Technical Features
- Memory-efficient streaming for 100+ MB files
- Robust retry and error handling for recognition
- Voice-preserving audio filtering (30Hz cutoff)
- Thread-safe GUI updates
- Proper state management for recording controls
- Chunk-based processing with progress tracking

### Documentation
- Comprehensive README with quick start guide
- Architecture documentation for developers
- Contributing guidelines
- MIT License
- Example settings configuration

## [Unreleased]

### Planned Features
- Real-time streaming audio processing
- Cloud integration for faster processing
- Custom model training for specific accents
- Batch processing for multiple files
- RESTful API for programmatic access
- Docker containerization
- Video file support (audio extraction)
- Emotion detection in speech
- Automatic language detection

---

For more information, see the [README](README.md) and [ARCHITECTURE](ARCHITECTURE.md) documentation.

