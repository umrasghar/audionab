# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-03-04

### Added

- Multi-format output: MP3, FLAC, WAV, AAC, Opus
- Deepgram API transcription (auto-transcribe after conversion)
- Watch folder mode with automatic conversion of new recordings
- System tray integration with minimize-to-tray and notifications
- History search and filter (All / Success / Failed)
- FFprobe pre-check to detect files with no audio stream
- Configurable output filename postfix (default: -mp3)
- Toast notification system replacing modal dialogs
- Keyboard shortcuts (Ctrl+O, Escape, Ctrl+Comma, F5)
- Custom output folder support
- Windows 11 classic context menu toggle
- Inno Setup installer (Start Menu, Add/Remove Programs, clean uninstall)
- CI/CD pipeline via GitHub Actions
- Automated release pipeline (build exe + installer on tag push)

### Technical

- Modular package architecture (14 modules)
- SQLite WAL mode with schema versioning
- Rotating file logger (5MB, 3 backups)
- 40 pytest tests
- 3-pass fault-tolerant conversion engine

[2.5.0]: https://github.com/AdeelIlyas/audionab/releases/tag/v2.5.0
