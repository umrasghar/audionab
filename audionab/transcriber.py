"""Deepgram API integration for audio transcription."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"


def transcribe(audio_path, api_key, model="nova-2", smart_format=True,
               language="en"):
    """Transcribe an audio file using Deepgram's API.

    Args:
        audio_path: Path to the audio file
        api_key: Deepgram API key
        model: Deepgram model to use (default: nova-2)
        smart_format: Enable smart formatting (punctuation, etc.)
        language: Language code

    Returns:
        dict with keys:
            success (bool): Whether transcription succeeded
            transcript (str|None): The transcribed text
            error (str|None): Error message if failed
            output_path (str|None): Path to saved .txt file
    """
    try:
        import httpx
    except ImportError:
        return {
            "success": False, "transcript": None,
            "error": "httpx not installed. Run: pip install httpx",
            "output_path": None
        }

    if not api_key:
        return {
            "success": False, "transcript": None,
            "error": "No Deepgram API key configured",
            "output_path": None
        }

    if not os.path.exists(audio_path):
        return {
            "success": False, "transcript": None,
            "error": f"Audio file not found: {audio_path}",
            "output_path": None
        }

    # Determine content type from extension
    ext = Path(audio_path).suffix.lower()
    content_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".opus": "audio/ogg",
        ".ogg": "audio/ogg",
    }
    content_type = content_types.get(ext, "audio/mpeg")

    params = {
        "model": model,
        "smart_format": str(smart_format).lower(),
        "language": language,
    }

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": content_type,
    }

    try:
        file_size = os.path.getsize(audio_path)
        logger.info("Transcribing %s (%.1f MB) with Deepgram %s",
                     Path(audio_path).name, file_size / (1024 * 1024), model)

        with open(audio_path, "rb") as f:
            response = httpx.post(
                DEEPGRAM_API_URL,
                params=params,
                headers=headers,
                content=f,
                timeout=300.0  # 5 min timeout for large files
            )

        if response.status_code == 401:
            return {
                "success": False, "transcript": None,
                "error": "Invalid Deepgram API key",
                "output_path": None
            }

        if response.status_code == 402:
            return {
                "success": False, "transcript": None,
                "error": "Deepgram: insufficient credits",
                "output_path": None
            }

        if response.status_code != 200:
            return {
                "success": False, "transcript": None,
                "error": f"Deepgram API error ({response.status_code}): {response.text[:200]}",
                "output_path": None
            }

        data = response.json()
        transcript = ""

        # Extract transcript from response
        channels = data.get("results", {}).get("channels", [])
        if channels:
            alternatives = channels[0].get("alternatives", [])
            if alternatives:
                transcript = alternatives[0].get("transcript", "")

        if not transcript:
            return {
                "success": False, "transcript": None,
                "error": "Deepgram returned empty transcript",
                "output_path": None
            }

        # Save transcript to .txt file next to the audio
        audio_p = Path(audio_path)
        txt_path = audio_p.parent / f"{audio_p.stem}.txt"
        with open(str(txt_path), "w", encoding="utf-8") as f:
            f.write(transcript)

        logger.info("Transcript saved: %s (%d chars)", txt_path.name, len(transcript))

        return {
            "success": True,
            "transcript": transcript,
            "error": None,
            "output_path": str(txt_path)
        }

    except httpx.TimeoutException:
        return {
            "success": False, "transcript": None,
            "error": "Deepgram request timed out (file too large?)",
            "output_path": None
        }
    except httpx.ConnectError:
        return {
            "success": False, "transcript": None,
            "error": "Cannot connect to Deepgram (check internet connection)",
            "output_path": None
        }
    except Exception as e:
        logger.warning("Transcription failed: %s", e, exc_info=True)
        return {
            "success": False, "transcript": None,
            "error": str(e),
            "output_path": None
        }
