"""Tests for audionab.helpers — no GUI or FFmpeg required."""

import os
import sys
from datetime import datetime, timedelta

# Add parent to path so we can import audionab package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audionab.helpers import format_size, format_time_ago


class TestFormatSize:
    def test_none(self):
        assert format_size(None) == "---"

    def test_zero(self):
        assert format_size(0) == "---"

    def test_negative(self):
        assert format_size(-100) == "---"

    def test_bytes(self):
        assert format_size(500) == "500 B"

    def test_kilobytes(self):
        result = format_size(1536)
        assert "KB" in result
        assert "1.5" in result

    def test_megabytes(self):
        result = format_size(5 * 1024 * 1024)
        assert "MB" in result
        assert "5.0" in result

    def test_gigabytes(self):
        result = format_size(2 * 1024 * 1024 * 1024)
        assert "GB" in result
        assert "2.00" in result


class TestFormatTimeAgo:
    def test_just_now(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        assert format_time_ago(now) == "Just now"

    def test_minutes_ago(self):
        dt = (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        result = format_time_ago(dt)
        assert "m ago" in result

    def test_hours_ago(self):
        dt = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        result = format_time_ago(dt)
        assert "h ago" in result

    def test_days_ago(self):
        dt = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")
        result = format_time_ago(dt)
        assert "d ago" in result

    def test_old_date(self):
        result = format_time_ago("2023-01-15 10:30:00")
        assert "Jan" in result and "2023" in result

    def test_invalid_string(self):
        assert format_time_ago("not a date") == "not a date"

    def test_empty_string(self):
        assert format_time_ago("") == "---"

    def test_none(self):
        assert format_time_ago(None) == "---"
