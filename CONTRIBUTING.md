# Contributing to Voice Transcriber

Thank you for your interest in contributing to Voice Transcriber! We welcome contributions from the community.

## Getting Started

1. **Fork the repository** and clone it locally
2. **Install dependencies**: `pip install -r requirements-dev.txt`
3. **Create a branch** for your feature or bugfix: `git checkout -b feature/your-feature-name`
4. **Make your changes** following our coding standards
5. **Test your changes** thoroughly
6. **Submit a pull request** with a clear description of your changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/voice_transcribe.git
cd voice_transcribe

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Check code quality
black .
flake8 .
```

## Coding Standards

### Python Style Guide
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use `black` for automatic code formatting
- Use `flake8` for linting
- Add type hints where applicable
- Write docstrings for all public functions and classes

### Code Quality
- Write unit tests for new features
- Maintain test coverage above 80%
- Keep functions focused and single-purpose
- Use meaningful variable and function names
- Add comments for complex logic

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_audio_processor.py
```

### Writing Tests
- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test names: `test_audio_enhancement_improves_quality`
- Test both success and failure cases
- Mock external dependencies (APIs, file I/O)

## Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features or bug fixes
3. **Ensure all tests pass** before submitting
4. **Update CHANGELOG** with your changes
5. **Write a clear PR description** explaining:
   - What problem you're solving
   - How you solved it
   - Any breaking changes
   - Screenshots (for UI changes)

## Bug Reports

When filing a bug report, please include:

- **Description**: Clear description of the bug
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, relevant dependencies
- **Error messages**: Complete error messages and stack traces
- **Audio files**: Sample audio files if relevant (use small test files)

## Feature Requests

When requesting a feature:

- **Use case**: Explain the problem you're trying to solve
- **Proposed solution**: Describe your ideal solution
- **Alternatives**: Any alternative solutions you've considered
- **Impact**: Who would benefit from this feature

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Prioritize the community's best interests

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or trolling
- Publishing others' private information
- Any unprofessional conduct

## Questions?

- Open an issue for questions about the codebase
- Tag your issue with `question` label
- Be specific about what you're trying to understand

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for making Voice Transcriber better! 🎉

