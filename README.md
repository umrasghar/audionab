<p align="center">
  <img src="assets/icon-256.png" width="96" alt="AudioNab icon" />
</p>

<h1 align="center">AudioNab</h1>

<p align="center">
  <strong>Nab the audio from any video.</strong><br>
  A lightweight Windows audio extractor built for OBS users, podcasters, and anyone who needs audio fast.
</p>

<p align="center">
  <a href="https://github.com/umrasghar/audionab/actions/workflows/ci.yml"><img src="https://github.com/umrasghar/audionab/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/umrasghar/audionab/releases/latest"><img src="https://img.shields.io/github/v/release/umrasghar/audionab?label=release" alt="Release" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/python-%3E%3D3.8-3776AB.svg" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/platform-Windows-0078D6.svg" alt="Windows" />
</p>

---

## Demo

<!-- Demo GIF coming soon -->

---

## Features

- **One-click conversion** -- Right-click any video, select "Nab Audio", done
- **Modern dark UI** -- Sleek interface built with customtkinter, with dark/light theme toggle
- **5 output formats** -- MP3, FLAC, WAV, AAC, and Opus
- **3-pass fault-tolerant conversion** -- Handles broken metadata, corrupt streams, and crashed OBS recordings
- **Conversion history** -- Searchable log with filter by All / Success / Failed
- **Watch folder mode** -- Monitors your OBS output folder and auto-converts new recordings
- **System tray** -- Minimize to tray with balloon notifications on completion
- **Deepgram transcription** -- Automatically transcribe converted audio to `.txt` via the Deepgram API
- **Batch conversion** -- Select multiple files at once, with cancel support
- **Drag and drop** -- Drop files directly onto the app window
- **Configurable** -- Bitrate (64k--320k), output postfix, custom output folder
- **Keyboard shortcuts** -- `Ctrl+O` open files, `Escape` close dialogs, `Ctrl+Comma` settings, `F5` refresh
- **Right-click context menu** -- Windows Explorer integration with Windows 11 support
- **Portable standalone .exe** -- Built with Nuitka, no Python installation required
- **Installer** -- Inno Setup installer with Start Menu shortcuts, Add/Remove Programs entry, and bundled FFmpeg
- **36+ input formats** -- 22 video and 14 audio formats supported

---

## Quick Start

### Option A: Download the Installer (recommended)

1. Go to the [latest release](https://github.com/umrasghar/audionab/releases/latest)
2. Download `AudioNab-Setup-2.5.0.exe`
3. Run the installer -- FFmpeg is bundled, no separate install needed
4. Right-click any video file and select **"Nab Audio"**

### Option B: Run with Python

```bash
# Clone the repository
git clone https://github.com/umrasghar/audionab.git
cd audionab

# Install dependencies
pip install -r requirements.txt

# Run the app
python audionab.py
```

> **Prerequisites:** Python 3.8+ and FFmpeg on your PATH.
> Install FFmpeg via PowerShell: `winget install Gyan.FFmpeg`

---

## How It Works

### 3-Pass Conversion Pipeline

Every file goes through up to three passes. If a pass succeeds, the pipeline stops immediately. If it fails, the next pass uses progressively more aggressive recovery techniques.

```
 Input File
     |
     v
 +---------------------------+
 | Pass 1: Standard          |   map 0:a:0, genpts+igndts
 | Fastest, handles 95%      |   Strips metadata, regenerates timestamps
 +---------------------------+
     | fail
     v
 +---------------------------+
 | Pass 2: Recovery          |   analyzeduration 100M, probesize 100M
 | Extended probe for        |   map 0:a? (optional audio mapping)
 | corrupt OBS recordings    |   Handles crashed/incomplete files
 +---------------------------+
     | fail
     v
 +---------------------------+
 | Pass 3: Raw Extraction    |   analyzeduration 200M, probesize 200M
 | Maximum tolerance         |   -vn flag, ignores video entirely
 | Last resort               |   Extracts whatever audio exists
 +---------------------------+
     |
     v
  Output File (MP3/FLAC/WAV/AAC/Opus)
```

### OBS Recording Pipeline

```
  OBS Studio                 AudioNab                    Deepgram
 +-----------+     watch    +----------------+   API    +---------------+
 | Records   | ----------> | Auto-converts  | ------> | Transcribes   |
 | video     |   folder    | to audio       |         | audio to text |
 +-----------+    mode     +----------------+         +---------------+
                                 |                          |
                                 v                          v
                            recording.mp3             recording.txt
```

---

## Comparison

| Feature                     | AudioNab       | HandBrake      | VLC            | Online Tools    |
|-----------------------------|----------------|----------------|----------------|-----------------|
| Audio extraction focus      | Yes            | No (video)     | No (player)    | Varies          |
| Right-click context menu    | Yes            | No             | No             | No              |
| Fault-tolerant conversion   | 3-pass         | Single pass    | Single pass    | Single pass     |
| Crashed OBS recovery        | Yes            | No             | No             | No              |
| Watch folder auto-convert   | Yes            | Queue only     | No             | No              |
| Transcription               | Yes (Deepgram) | No             | No             | Some            |
| Batch conversion            | Yes            | Yes            | Yes            | Limited         |
| File size limit             | None           | None           | None           | Typically <2 GB |
| Privacy                     | Local only     | Local only     | Local only     | Uploaded        |
| Install size                | ~30 MB         | ~100 MB        | ~200 MB        | N/A             |
| Price                       | Free           | Free           | Free           | Freemium        |

---

## Usage

### GUI App

1. Launch `AudioNab.exe` (or run `python audionab.py`)
2. Click **"Nab Audio"** to pick files, or drag and drop them onto the window
3. Converted files appear next to the originals
4. Double-click any history entry to open its folder in Explorer
5. Use the filter bar to search history by filename, or filter by All / Success / Failed

### Right-Click Context Menu

1. Open the app and go to **Settings** (or press `Ctrl+Comma`)
2. Click **Install "Nab Audio" Menu** and accept the admin prompt
3. Right-click any supported video or audio file and select **"Nab Audio"**
4. On Windows 11: click **"Show more options"** first, or enable the classic menu in Settings

### Command Line

```bash
# Convert a single file
python audionab.py --convert "C:\Videos\recording.mkv"

# Install context menu (requires admin)
python audionab.py --install

# Uninstall context menu
python audionab.py --uninstall
```

---

## Edge Cases Handled

| Issue | How It's Handled |
|---|---|
| Broken/missing metadata | Stripped via `-map_metadata -1`, timestamps regenerated |
| Corrupt video stream | Audio extracted independently, video ignored |
| Faulty PTS/DTS timestamps | Rebuilt with `+genpts +igndts` flags |
| Crashed OBS recordings | Extended 100--200 MB probe in recovery passes |
| Empty (0-byte) files | Detected and skipped with clear error message |
| Duplicate output names | Auto-numbered: `file.mp3`, `file_1.mp3`, `file_2.mp3` |
| Wrong file extension | FFmpeg probes actual container format |
| No audio stream | All 3 passes attempted, clear error if none found |
| Encrypted/DRM files | Detected and reported |

---

## Supported Formats

**Output formats:** MP3, FLAC, WAV, AAC, Opus

**Video input:** `.mp4` `.mkv` `.avi` `.mov` `.wmv` `.flv` `.webm` `.m4v` `.ts` `.mts` `.m2ts` `.vob` `.mpg` `.mpeg` `.3gp` `.3g2` `.ogv` `.divx` `.asf` `.rm` `.rmvb` `.f4v`

**Audio input:** `.m4a` `.aac` `.ogg` `.opus` `.wma` `.flac` `.wav` `.aiff` `.ac3` `.dts` `.amr` `.ape` `.wv` `.mka`

---

## Building from Source

### 1. Clone and install dependencies

```bash
git clone https://github.com/umrasghar/audionab.git
cd audionab
pip install -r requirements.txt
```

### 2. Generate application icons

```bash
python scripts/generate_icon.py
```

This creates `assets/icon.ico`, `assets/icon-64.png`, and `assets/icon-256.png`.

### 3. Build the standalone executable

```bash
build.bat
```

The executable will be placed at `dist\AudioNab.exe`. It is fully portable.

### 4. Build the installer (optional)

Requires [Inno Setup 6+](https://jrsoftware.org/isinfo.php) to be installed.

```bash
iscc installer.iss
```

The installer will be output to `installer_output\AudioNab-Setup-2.5.0.exe`.

---

## Data Storage

All application data is stored locally in `%LOCALAPPDATA%\AudioNab\`:

```
AudioNab/
  audionab_history.db     # SQLite conversion history
  audionab_config.json    # User preferences and settings
  audionab.log            # Application log file
```

No data is sent externally unless Deepgram transcription is enabled, in which case audio is sent to the Deepgram API for processing.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.8+ |
| UI framework | customtkinter |
| Audio engine | FFmpeg (bundled or system) |
| Database | SQLite (conversion history) |
| Drag and drop | windnd |
| System tray | pystray + Pillow |
| Folder watcher | watchdog |
| Transcription | Deepgram API via httpx |
| Context menu | Windows Registry API |
| Build | PyInstaller (standalone .exe) |
| Installer | Inno Setup |
| CI/CD | GitHub Actions (pytest + ruff, automated release) |

---

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started, code style, and the pull request process.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes across all releases.

---

## License

MIT License -- see [LICENSE](LICENSE) for details.
