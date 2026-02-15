# Contributing to Telegram Video Downloader Bot

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
4. [Development Setup](#development-setup)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/telegram-video-bot.git
   cd telegram-video-bot
   ```
3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Reporting Bugs

When filing an issue, include:
- Clear, descriptive title
- Steps to reproduce the bug
- Expected vs actual behavior
- Your environment (Python version, OS, deployment method)
- Relevant logs or error messages

### Suggesting Features

For feature requests:
- Check if it's already been suggested
- Explain the use case clearly
- Describe the proposed solution
- Consider backwards compatibility

### Improving Documentation

Documentation improvements are always welcome:
- Fix typos or unclear explanations
- Add examples or use cases
- Improve setup instructions
- Update outdated information

## Development Setup

1. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run the bot locally**
   ```bash
   python bot.py
   ```

4. **Install development dependencies** (optional)
   ```bash
   pip install pytest flake8 black mypy
   ```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

### Code Formatting

Use `black` for code formatting:
```bash
black bot.py
```

### Type Hints

Use type hints where appropriate:
```python
def download_video(url: str) -> Optional[str]:
    """Download video from URL"""
    pass
```

### Comments

- Write self-documenting code when possible
- Add comments for complex logic
- Keep comments up-to-date with code changes

### Example of Good Code

```python
async def download_with_progress(
    url: str,
    progress_callback: Optional[callable] = None
) -> Optional[str]:
    """
    Download video with progress tracking.
    
    Args:
        url: Video URL to download
        progress_callback: Optional callback for progress updates
        
    Returns:
        Path to downloaded file, or None if download failed
    """
    try:
        # Implementation
        pass
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_downloader.py

# Run with coverage
pytest --cov=.
```

### Writing Tests

Add tests for new features:

```python
def test_video_download():
    """Test video download functionality"""
    url = "https://example.com/video.mp4"
    result = download_video(url)
    assert result is not None
    assert os.path.exists(result)
```

## Pull Request Process

### Before Submitting

1. **Test your changes thoroughly**
   - Run the bot locally
   - Test edge cases
   - Verify no regressions

2. **Update documentation**
   - Update README if needed
   - Add/update docstrings
   - Update CHANGELOG

3. **Format your code**
   ```bash
   black bot.py
   flake8 bot.py
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: video quality selection"
   ```

### Submitting PR

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use a clear, descriptive title
   - Reference related issues
   - Describe what changed and why
   - Include screenshots if relevant

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement
   
   ## Testing
   How was this tested?
   
   ## Related Issues
   Fixes #123
   
   ## Screenshots (if applicable)
   ```

### Review Process

1. Maintainer will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Celebrate! 🎉

## Feature Development Guidelines

### Adding New Download Sources

When adding support for a new video source:

1. **Check if yt-dlp already supports it**
   - yt-dlp supports 1000+ sites
   - Test with yt-dlp first

2. **Add fallback method if needed**
   - Implement custom downloader
   - Add error handling
   - Test thoroughly

3. **Update documentation**
   - Add to supported sources list
   - Include example URL

### Adding New Commands

For new bot commands:

1. **Add command handler**
   ```python
   async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
       """Handle /newcommand"""
       pass
   
   application.add_handler(CommandHandler("newcommand", new_command))
   ```

2. **Update help text**
   - Add command to `/start` message
   - Document in README

3. **Add admin checks if needed**
   ```python
   if update.effective_user.id != ADMIN_ID:
       await update.message.reply_text("Admin only!")
       return
   ```

## Areas That Need Help

Current priorities:

- [ ] Better error messages for unsupported sites
- [ ] Quality selection UI
- [ ] Playlist download support
- [ ] Better progress tracking for large files
- [ ] Additional admin panel features
- [ ] Unit tests
- [ ] Performance optimizations

## Questions?

- Open an issue for discussion
- Check existing issues first
- Be patient and respectful

## Recognition

Contributors will be:
- Listed in README
- Mentioned in release notes
- Thanked in commit messages

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏
