"""Download FFmpeg essentials for bundling with AudioNab.

Downloads pre-built ffmpeg.exe + ffprobe.exe from BtbN/FFmpeg-Builds.
Output: ffmpeg/ directory with ffmpeg.exe and ffprobe.exe

Usage:
    python scripts/download_ffmpeg.py [--output-dir DIR]
"""

import io
import os
import sys
import zipfile
import urllib.request

FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)

DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ffmpeg")


def download_ffmpeg(output_dir=None):
    output_dir = output_dir or DEFAULT_OUTPUT
    os.makedirs(output_dir, exist_ok=True)

    ffmpeg_path = os.path.join(output_dir, "ffmpeg.exe")
    ffprobe_path = os.path.join(output_dir, "ffprobe.exe")

    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        print(f"FFmpeg already exists at {output_dir}")
        return True

    print(f"Downloading FFmpeg from BtbN...")
    print(f"  URL: {FFMPEG_URL}")

    try:
        req = urllib.request.Request(FFMPEG_URL, headers={"User-Agent": "AudioNab"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            size_mb = len(data) / (1024 * 1024)
            print(f"  Downloaded: {size_mb:.1f} MB")
    except Exception as e:
        print(f"  ERROR: Download failed: {e}")
        return False

    print("  Extracting ffmpeg.exe and ffprobe.exe...")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            extracted = 0
            for name in zf.namelist():
                basename = os.path.basename(name)
                if basename in ("ffmpeg.exe", "ffprobe.exe"):
                    with zf.open(name) as src:
                        dest_path = os.path.join(output_dir, basename)
                        with open(dest_path, "wb") as dst:
                            dst.write(src.read())
                        extracted += 1
                        print(f"    {basename} -> {dest_path}")

            if extracted < 2:
                print("  WARNING: Could not find both ffmpeg.exe and ffprobe.exe in archive")
                return False

    except Exception as e:
        print(f"  ERROR: Extraction failed: {e}")
        return False

    print(f"\n  FFmpeg ready at: {output_dir}")
    return True


if __name__ == "__main__":
    output = None
    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    success = download_ffmpeg(output)
    sys.exit(0 if success else 1)
