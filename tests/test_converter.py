"""Tests for audionab.converter — no FFmpeg required (mocked)."""

import os
import sys
import tempfile
import threading
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audionab.converter import Converter


class TestFindFFmpeg:
    def test_returns_string_or_none(self):
        result = Converter.find_ffmpeg()
        assert result is None or isinstance(result, str)

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    def test_finds_via_which(self, mock_which):
        assert Converter.find_ffmpeg() == "/usr/bin/ffmpeg"

    @patch("shutil.which", return_value=None)
    def test_returns_none_when_not_found(self, mock_which):
        with patch("glob.glob", return_value=[]):
            with patch("os.path.exists", return_value=False):
                assert Converter.find_ffmpeg() is None


class TestGetUniqueOutput:
    def test_no_conflict(self):
        path = os.path.join(tempfile.gettempdir(), "unique_test_audionab.mp3")
        # Ensure it doesn't exist
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        assert Converter.get_unique_output(path) == path

    def test_with_conflict(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        try:
            result = Converter.get_unique_output(tmp.name)
            assert result != tmp.name
            assert "_1" in result
        finally:
            os.unlink(tmp.name)


class TestProbe:
    @patch("subprocess.run")
    def test_probe_with_audio(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"streams":[{"codec_type":"audio","codec_name":"aac"}],'
                   '"format":{"duration":"120.5"}}',
            stderr=""
        )
        result = Converter.probe("test.mp4")
        assert result["has_audio"] is True
        assert result["duration"] == 120.5
        assert result["audio_codec"] == "aac"

    @patch("subprocess.run")
    def test_probe_no_audio(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"streams":[{"codec_type":"video","codec_name":"h264"}],'
                   '"format":{"duration":"60.0"}}',
            stderr=""
        )
        result = Converter.probe("test.mp4")
        assert result["has_audio"] is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_probe_ffprobe_not_found(self, mock_run):
        result = Converter.probe("test.mp4")
        assert result["has_audio"] is True  # Optimistic fallback
        assert "not found" in result["error"]


class TestConvert:
    @patch("subprocess.run")
    def test_success_on_first_pass(self, mock_run):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.write(b"fake mp3 data")
        tmp.close()

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        success, pass_used, error = Converter.convert(
            "input.mp4", tmp.name, "192k"
        )
        assert success is True
        assert pass_used == 1
        assert error == ""

        os.unlink(tmp.name)

    def test_cancel_event(self):
        cancel = threading.Event()
        cancel.set()
        success, pass_used, error = Converter.convert(
            "input.mp4", "output.mp3", cancel_event=cancel
        )
        assert success is False
        assert error == "Cancelled"

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_ffmpeg_not_found(self, mock_run):
        success, pass_used, error = Converter.convert(
            "input.mp4", "output.mp3"
        )
        assert success is False
        assert "FFmpeg not found" in error
