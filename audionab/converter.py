"""FFmpeg-based audio converter with 3-pass fault tolerance."""

import glob
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class Converter:
    @staticmethod
    def find_ffmpeg():
        """Find ffmpeg executable — checks bundled location first, then system."""
        # 1. Check next to the running exe / script (bundled with app)
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        for subdir in ["ffmpeg", ".", "bin"]:
            candidate = os.path.join(app_dir, subdir, "ffmpeg.exe")
            if os.path.exists(candidate):
                return candidate
        # Direct next to exe
        candidate = os.path.join(app_dir, "ffmpeg.exe")
        if os.path.exists(candidate):
            return candidate

        # 2. System PATH
        path = shutil.which("ffmpeg")
        if path:
            return path

        # 3. Common install locations
        common = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            os.path.expandvars(
                r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe"
            ),
        ]
        for p in common:
            matches = glob.glob(p)
            if matches and os.path.exists(matches[0]):
                return matches[0]
        return None

    @staticmethod
    def find_ffprobe(ffmpeg_path=None):
        """Find ffprobe executable, preferring same directory as ffmpeg."""
        if ffmpeg_path:
            ffprobe = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
            if sys.platform == "win32":
                ffprobe += ".exe"
            if os.path.exists(ffprobe):
                return ffprobe
        path = shutil.which("ffprobe")
        if path:
            return path
        return None

    @staticmethod
    def probe(input_path, ffprobe_path="ffprobe"):
        """Use ffprobe to check if file has audio streams and get duration.

        Returns dict with keys:
            has_audio (bool): Whether an audio stream exists
            duration (float|None): Duration in seconds if available
            audio_codec (str|None): Audio codec name
            error (str|None): Error message if probe failed
        """
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            result = subprocess.run(
                [
                    ffprobe_path, "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams", "-show_format",
                    input_path
                ],
                capture_output=True, text=True, timeout=30,
                creationflags=creationflags
            )
            if result.returncode != 0:
                return {"has_audio": True, "duration": None, "audio_codec": None,
                        "error": result.stderr.strip()}

            data = json.loads(result.stdout)
            audio_streams = [
                s for s in data.get("streams", [])
                if s.get("codec_type") == "audio"
            ]

            duration = None
            fmt = data.get("format", {})
            if fmt.get("duration"):
                try:
                    duration = float(fmt["duration"])
                except (ValueError, TypeError):
                    pass

            if not audio_streams:
                return {"has_audio": False, "duration": duration,
                        "audio_codec": None, "error": None}

            return {
                "has_audio": True,
                "duration": duration,
                "audio_codec": audio_streams[0].get("codec_name"),
                "error": None
            }
        except FileNotFoundError:
            logger.debug("ffprobe not found at %s", ffprobe_path)
            return {"has_audio": True, "duration": None, "audio_codec": None,
                    "error": "ffprobe not found"}
        except Exception as e:
            logger.debug("ffprobe failed: %s", e)
            return {"has_audio": True, "duration": None, "audio_codec": None,
                    "error": str(e)}

    @staticmethod
    def get_unique_output(output_path):
        """Return a unique output path, appending _1, _2, etc. if needed."""
        p = Path(output_path)
        if not p.exists():
            return str(p)
        counter = 1
        while True:
            new_path = p.parent / f"{p.stem}_{counter}{p.suffix}"
            if not new_path.exists():
                return str(new_path)
            counter += 1

    @staticmethod
    def convert(input_path, output_path, bitrate="192k", ffmpeg_path="ffmpeg",
                progress_callback=None, cancel_event=None, output_format=None):
        """Convert input audio with 3-pass fault tolerance.

        Args:
            output_format: dict from OUTPUT_FORMATS (if None, defaults to MP3)

        Returns (success: bool, pass_used: int, error_msg: str)
        """
        from . import OUTPUT_FORMATS

        if output_format is None:
            output_format = OUTPUT_FORMATS["MP3"]

        codec_args = list(output_format["codec_args"])
        bitrate_args = ["-ab", bitrate] if output_format["supports_bitrate"] else []

        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        passes = [
            {
                "label": "Standard conversion",
                "args": [
                    ffmpeg_path, "-hide_banner", "-loglevel", "error",
                    "-err_detect", "ignore_err",
                    "-fflags", "+genpts+discardcorrupt+igndts",
                    "-i", input_path,
                    "-map", "0:a:0",
                    *codec_args, *bitrate_args,
                    "-map_metadata", "-1",
                    "-y", output_path
                ]
            },
            {
                "label": "Recovery mode",
                "args": [
                    ffmpeg_path, "-hide_banner", "-loglevel", "error",
                    "-err_detect", "ignore_err",
                    "-fflags", "+genpts+discardcorrupt+igndts",
                    "-analyzeduration", "100M", "-probesize", "100M",
                    "-i", input_path,
                    "-map", "0:a?",
                    *codec_args, *bitrate_args,
                    "-map_metadata", "-1",
                    "-y", output_path
                ]
            },
            {
                "label": "Raw extraction",
                "args": [
                    ffmpeg_path, "-hide_banner", "-loglevel", "error",
                    "-err_detect", "ignore_err",
                    "-fflags", "+genpts+discardcorrupt+igndts",
                    "-analyzeduration", "200M", "-probesize", "200M",
                    "-i", input_path,
                    "-vn",
                    *codec_args, *(bitrate_args if bitrate_args else []),
                    "-map_metadata", "-1",
                    "-y", output_path
                ]
            }
        ]

        last_error = ""
        for i, p in enumerate(passes, 1):
            if cancel_event and cancel_event.is_set():
                return False, 0, "Cancelled"
            if progress_callback:
                progress_callback(f"Pass {i}/3: {p['label']}...")
            try:
                result = subprocess.run(
                    p["args"], capture_output=True, text=True,
                    timeout=3600, creationflags=creationflags
                )
                if result.returncode == 0 and os.path.exists(output_path):
                    if os.path.getsize(output_path) > 0:
                        logger.info("Conversion succeeded on pass %d: %s", i, input_path)
                        return True, i, ""
                last_error = result.stderr.strip() or f"Pass {i} produced empty output"
            except subprocess.TimeoutExpired:
                last_error = f"Pass {i} timed out (>1 hour)"
            except FileNotFoundError:
                return False, 0, "FFmpeg not found. Please install FFmpeg first."
            except Exception as e:
                last_error = str(e)
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception:
                pass

        logger.warning("All 3 passes failed for %s: %s", input_path, last_error)
        return False, 0, last_error
