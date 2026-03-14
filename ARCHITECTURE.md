# Architecture Documentation

## System Overview

Voice Transcriber is built using a modular architecture that separates concerns into distinct components: audio processing, speech recognition, speaker detection, and user interface.

## Core Components

### 1. Audio Processor (`audio_processor.py`)
Handles all audio-related operations:
- **Audio Loading**: Multi-format support (WAV, MP3, M4A, FLAC, OGG, AAC)
- **Audio Enhancement**: 
  - Noise reduction using spectral subtraction
  - High-pass filtering (30Hz cutoff) to preserve low-pitched voices
  - Automatic volume normalization (up to 5x boost)
- **Audio Segmentation**: Smart chunking for large files (30-second segments)
- **Format Conversion**: Unified audio format handling via librosa

### 2. Voice Transcriber (`voice_transcriber.py`)
Core transcription engine:
- **Speech Recognition**:
  - Multiple engine support (Google, Sphinx, Azure, Bing)
  - Retry logic with exponential backoff (3 attempts per chunk)
  - Automatic fallback from Sphinx to Google
- **Language Support**: Multi-language recognition with confidence scoring
- **Large File Handling**: 
  - Streaming processing for 100+ MB files
  - Progress tracking and live transcription display
- **Export Capabilities**: TXT, JSON, CSV, SRT, VTT formats

### 3. Speaker Detector (`speaker_detector.py`)
Advanced speaker diarization system:
- **Feature Extraction**:
  - MFCC (Mel-frequency cepstral coefficients)
  - Spectral features (centroid, rolloff, bandwidth)
  - Zero-crossing rate and RMS energy
- **Speaker Clustering**:
  - Automatic optimal cluster determination
  - Agglomerative hierarchical clustering
  - Silhouette score optimization
- **Speaker Identification**:
  - Voice profile creation and matching
  - Confidence scoring for identifications
  - Speaker timeline generation

### 4. GUI Application (`voice_transcriber_gui.py`)
Modern user interface:
- **Design System**: Neumorphism/Liquid Glass aesthetic
- **Real-time Updates**: Live transcription display with threading
- **State Management**: Proper recording states (record/pause/stop)
- **Progress Feedback**: Animated progress bars and status updates
- **Tab-based Interface**: Organized by feature (transcribe, detect, manage, settings)

## Data Flow

### Live Transcription Flow
```
Microphone Input → PyAudio Capture → 3-second chunks → 
Audio Enhancement → Speech Recognition → Live Display → 
Final Transcription
```

### File Processing Flow
```
Audio File → Format Detection → Loading (streaming if large) →
Audio Enhancement → Chunking → Speech Recognition (with retry) →
Speaker Detection (optional) → Export (multiple formats)
```

### Speaker Detection Flow
```
Audio File → Feature Extraction → Segmentation →
Voice Clustering → Speaker Labeling → Timeline Generation →
Export with Speaker IDs
```

## Key Technical Decisions

### 1. Chunking Strategy
- **Small files (<1 min)**: Process as single unit
- **Medium files (1-2 min)**: 10-second chunks
- **Large files (>2 min)**: 30-second chunks with live display
- **Rationale**: Balance between accuracy and memory efficiency

### 2. Audio Enhancement Pipeline
- **30Hz high-pass filter**: Removes low-frequency noise while preserving bass voices
- **Adaptive volume boost**: Up to 5x amplification with clipping prevention
- **Noise reduction**: Spectral subtraction without voice distortion
- **Rationale**: Maximize recognition accuracy without losing voice content

### 3. Retry Logic
- **3 attempts per chunk**: Exponential backoff (1s, 2s, 4s)
- **Per-chunk isolation**: Failed chunks don't block subsequent processing
- **Automatic fallback**: Sphinx → Google engine switching
- **Rationale**: Maximize success rate for difficult audio segments

### 4. Threading Model
- **Main thread**: GUI and user interaction
- **Worker threads**: Audio processing and recognition
- **Queue-based communication**: Thread-safe updates to GUI
- **Rationale**: Responsive UI during long operations

## Performance Optimization

### Memory Management
- **Streaming audio loading**: For files >100MB
- **Chunk-based processing**: Prevents memory overflow
- **Garbage collection**: Explicit cleanup after large operations
- **Audio downsampling**: Optional quality reduction for speed

### Processing Speed
- **Parallel processing**: Multiple chunks can be processed concurrently
- **Caching**: Feature extraction results cached during speaker detection
- **Early termination**: Skip processing on user cancel
- **Optimized sample rates**: 16kHz default for best speed/accuracy balance

## Error Handling

### Graceful Degradation
1. **Recognition failures**: Retry → fallback engine → skip with warning
2. **Audio format issues**: Automatic format conversion → manual intervention
3. **Memory constraints**: Switch to streaming mode → reduce chunk size
4. **Missing models**: Fallback to simpler algorithms → user notification

### User Feedback
- **Toast notifications**: Non-blocking status updates
- **Progress indicators**: Real-time operation status
- **Error messages**: Clear, actionable error descriptions
- **Status subtitle**: Additional context for current operation

## Testing Strategy

### Unit Tests
- Audio processing functions
- Feature extraction algorithms
- Format conversion utilities
- Export format generators

### Integration Tests
- End-to-end transcription workflows
- Speaker detection accuracy
- Multi-format file handling
- GUI state management

### Performance Tests
- Large file processing (2+ hours)
- Memory usage under load
- Concurrent operation handling
- UI responsiveness during processing

## Future Enhancements

### Planned Features
- **Real-time streaming**: Process audio streams (URLs, live feeds)
- **Cloud integration**: Optional cloud-based processing for speed
- **Custom models**: Fine-tune recognition for specific accents/domains
- **Batch processing**: Process multiple files simultaneously
- **API server**: RESTful API for programmatic access

### Scalability Considerations
- **Distributed processing**: Multiple workers for enterprise use
- **Database integration**: Store transcriptions and speaker profiles
- **Microservices**: Break into independent services
- **Container deployment**: Docker support for easy deployment

## Dependencies

### Core Libraries
- **speech_recognition**: Multi-engine speech-to-text wrapper
- **pyaudio**: Audio input/output
- **librosa**: Advanced audio analysis and processing
- **pyannote.audio**: Professional speaker diarization
- **resemblyzer**: Voice embedding extraction

### ML/AI Stack
- **scikit-learn**: Clustering and classification
- **torch**: Deep learning models for speaker detection
- **transformers**: Advanced NLP capabilities (optional)

### GUI Framework
- **customtkinter**: Modern, themeable Tkinter
- **tkinter-tooltip**: Enhanced tooltips

## Configuration

### Settings Management
- **JSON-based**: Simple, human-readable configuration
- **Persistent**: Settings saved between sessions
- **Validation**: Input validation on settings changes
- **Defaults**: Sensible defaults for all parameters

### Configurable Parameters
- Language and recognition engine
- Audio sample rate and chunk duration
- Maximum speaker count for detection
- Volume boost and noise reduction levels
- Export format preferences

---

*This architecture is designed for modularity, maintainability, and extensibility. Each component can be enhanced or replaced independently while maintaining system integrity.*

