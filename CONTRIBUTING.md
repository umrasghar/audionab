# Contributing to AudioNab

Thank you for your interest in contributing to AudioNab. This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/umrasghar/audionab.git
   cd audionab
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install FFmpeg** (one of the following methods):

   ```bash
   # Option A: Using winget
   winget install Gyan.FFmpeg

   # Option B: Using the bundled download script
   python scripts/download_ffmpeg.py
   ```

5. **Run the application:**

   ```bash
   python -m audionab
   ```

## Code Style

- **Linter:** [Ruff](https://docs.astral.sh/ruff/)
- **Line length:** 100 characters
- **Target:** Python 3.8+

Run the linter before submitting changes:

```bash
ruff check audionab/
```

## Running Tests

```bash
pytest tests/ -v
```

All tests must pass before a pull request will be reviewed.

## Project Structure

The AudioNab package is organized into 14 modules:

| Module | Description |
|--------|-------------|
| `audionab/__init__.py` | Constants, version, supported formats |
| `audionab/__main__.py` | Entry point (CLI + GUI routing) |
| `audionab/config.py` | JSON config management |
| `audionab/converter.py` | FFmpeg 3-pass converter |
| `audionab/context_menu.py` | Windows Registry context menu |
| `audionab/database.py` | SQLite history |
| `audionab/helpers.py` | Utility functions |
| `audionab/tray.py` | System tray (pystray) |
| `audionab/transcriber.py` | Deepgram transcription |
| `audionab/watcher.py` | Folder watch (watchdog) |
| `audionab/ui/app.py` | Main window (customtkinter) |
| `audionab/ui/settings.py` | Settings dialog |
| `audionab/ui/toast.py` | Toast notifications |

## Pull Request Process

1. **Fork** the repository and create a new branch from `main`:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines above.

3. **Run linting and tests** to ensure nothing is broken:

   ```bash
   ruff check audionab/
   pytest tests/ -v
   ```

4. **Open a pull request** against the `main` branch.

5. **Fill out the pull request template** completely. Describe what your PR does, the type of change, and how it was tested.

## Regenerating Icons

If you need to regenerate the application icons:

```bash
python scripts/generate_icon.py
```

## Reporting Bugs

Please use the [Bug Report template](https://github.com/umrasghar/audionab/issues/new?template=bug_report.md) when filing issues.

When reporting a bug, include the log file located at:

```
%LOCALAPPDATA%\AudioNab\audionab.log
```

This log contains detailed information about conversion attempts, errors, and application state that will help diagnose the issue.
