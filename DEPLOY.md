# Deployment Guide

## Quick Deploy Checklist

This guide helps you deploy Voice Transcriber to production or demonstrate it for presentations.

### Pre-deployment Checklist

- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Settings configured: Copy `settings.json.example` to `settings.json`
- [ ] Audio permissions granted (microphone access)
- [ ] Tested on target platform (Windows/Mac/Linux)
- [ ] All tests passing: `pytest`

## Local Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run the application
python voice_transcriber_gui.py

# Run tests
pytest

# Check code quality
black .
flake8 .
```

## Demo Setup

For demonstrations (investors, YC interviews, etc.):

1. **Prepare Demo Audio**
   - Have 2-3 sample audio files ready (different scenarios)
   - Include multi-speaker conversation
   - Include different languages/accents
   - Keep files under 2 minutes for quick demos

2. **Pre-configure Settings**
   - Set optimal language and engine
   - Adjust audio parameters for your hardware
   - Test microphone before demo

3. **Demo Flow**
   - Start with live transcription (most impressive)
   - Show speaker detection with multi-speaker audio
   - Demonstrate export capabilities
   - Show settings customization

4. **Key Talking Points**
   - Real-time processing speed
   - High accuracy (>90% for clear speech)
   - Speaker identification capabilities
   - Multi-format support
   - Modern, intuitive UI

## Cloud Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port (if adding API)
EXPOSE 8000

# Run application
CMD ["python", "voice_transcriber_gui.py"]
```

### AWS Deployment

```bash
# EC2 instance setup
sudo apt-get update
sudo apt-get install -y python3 python3-pip portaudio19-dev

# Clone and setup
git clone <your-repo>
cd voice_transcribe
pip3 install -r requirements.txt

# Run with nohup for background execution
nohup python3 voice_transcriber_gui.py &
```

### Heroku Deployment

Create `Procfile`:
```
web: python voice_transcriber_gui.py
```

Create `runtime.txt`:
```
python-3.9.16
```

Deploy:
```bash
heroku create your-app-name
git push heroku main
```

## API Server Deployment

For programmatic access, consider adding a REST API:

```python
# api_server.py (example)
from flask import Flask, request, jsonify
from voice_transcriber import VoiceTranscriber

app = Flask(__name__)
transcriber = VoiceTranscriber()

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    result = transcriber.transcribe_audio_file(audio_file)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

## Production Considerations

### Performance Optimization
- Use GPU for faster processing (if available)
- Implement caching for repeated requests
- Set up CDN for audio file delivery
- Use load balancer for multiple instances

### Security
- Implement API authentication (JWT tokens)
- Add rate limiting
- Sanitize file uploads
- Use HTTPS for all connections
- Don't store audio files long-term (privacy)

### Monitoring
- Set up logging (CloudWatch, Datadog, etc.)
- Track error rates and performance metrics
- Monitor memory usage for large files
- Set up alerts for failures

### Scaling
- Horizontal scaling: Multiple worker instances
- Queue system for batch processing (Celery + Redis)
- Separate web server from processing workers
- Use managed services (AWS Transcribe, Google Speech-to-Text) for scale

## Troubleshooting

### Common Production Issues

**Issue**: Audio processing fails in production
- Check audio file permissions
- Verify ffmpeg/sox is installed
- Check memory limits

**Issue**: Poor performance under load
- Implement job queue system
- Use background workers
- Cache frequently processed files

**Issue**: Microphone not working
- Check system permissions
- Verify PyAudio is properly installed
- Test with different audio devices

## Maintenance

### Regular Tasks
- Update dependencies monthly: `pip install -U -r requirements.txt`
- Review and rotate logs
- Monitor disk space (audio files can accumulate)
- Test on latest Python versions
- Update documentation for new features

### Backup Strategy
- Backup speaker profiles database
- Export transcription history (if stored)
- Version control for configuration
- Document custom modifications

## Support & Resources

- GitHub Issues: Report bugs and request features
- Documentation: See README.md and ARCHITECTURE.md
- Contributing: See CONTRIBUTING.md
- License: MIT (see LICENSE file)

---

**Ready for production?** Make sure all checklist items are complete and you've tested thoroughly on your target platform.

