"""
AudioNab — Lightweight Audio Extractor
=======================================
Nab the audio from any video in one click.
"""

APP_NAME = "AudioNab"
APP_VERSION = "2.5.0"
APP_TAGLINE = "Nab the audio from any video."
APP_REPO = "https://github.com/umrasghar/audionab"
DB_NAME = "audionab_history.db"
CONFIG_NAME = "audionab_config.json"
REGISTRY_KEY_NAME = "AudioNab"
REGISTRY_LABEL = "Nab Audio"

SUPPORTED_VIDEO = (
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    ".ts", ".mts", ".m2ts", ".vob", ".mpg", ".mpeg",
    ".3gp", ".3g2", ".ogv", ".divx", ".asf", ".rm", ".rmvb", ".f4v"
)
SUPPORTED_AUDIO = (
    ".m4a", ".aac", ".ogg", ".opus", ".wma", ".flac", ".wav", ".aiff",
    ".ac3", ".dts", ".amr", ".ape", ".wv", ".mka"
)
SUPPORTED_ALL = SUPPORTED_VIDEO + SUPPORTED_AUDIO

BITRATE_OPTIONS = ["64k", "96k", "128k", "160k", "192k", "256k", "320k"]
DEFAULT_BITRATE = "192k"
DEFAULT_OUTPUT_POSTFIX = "-mp3"

# Output format definitions: {name: {ext, codec_args, supports_bitrate}}
OUTPUT_FORMATS = {
    "MP3": {
        "ext": ".mp3",
        "codec_args": ["-c:a", "libmp3lame", "-ar", "44100", "-ac", "2",
                        "-write_xing", "1", "-id3v2_version", "3"],
        "supports_bitrate": True,
    },
    "FLAC": {
        "ext": ".flac",
        "codec_args": ["-c:a", "flac", "-ar", "44100", "-ac", "2"],
        "supports_bitrate": False,
    },
    "WAV": {
        "ext": ".wav",
        "codec_args": ["-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2"],
        "supports_bitrate": False,
    },
    "AAC": {
        "ext": ".m4a",
        "codec_args": ["-c:a", "aac", "-ar", "44100", "-ac", "2"],
        "supports_bitrate": True,
    },
    "Opus": {
        "ext": ".opus",
        "codec_args": ["-c:a", "libopus", "-ar", "48000", "-ac", "2"],
        "supports_bitrate": True,
    },
}
OUTPUT_FORMAT_NAMES = list(OUTPUT_FORMATS.keys())

# Colors
C_SUCCESS = "#2dd4bf"
C_ERROR = "#f87171"
C_WARNING = "#fbbf24"
C_ACCENT = "#7aa2f7"
C_PURPLE = "#a78bfa"

# Win11 classic context menu registry path
WIN11_CLASSIC_MENU_KEY = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
