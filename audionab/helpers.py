"""Utility functions for AudioNab."""

import os
import subprocess
import sys
from datetime import datetime, timedelta


def format_size(size_bytes):
    """Format bytes into human-readable size string."""
    if size_bytes is None or size_bytes <= 0:
        return "---"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_time_ago(dt_str):
    """Format a datetime string as a relative time (e.g. '5m ago')."""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        diff = datetime.now() - dt
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            return f"{int(diff.seconds / 60)}m ago"
        elif diff < timedelta(days=1):
            return f"{int(diff.seconds / 3600)}h ago"
        elif diff < timedelta(days=7):
            return f"{diff.days}d ago"
        else:
            return dt.strftime("%b %d, %Y")
    except Exception:
        return dt_str or "---"


def open_folder(filepath):
    """Open the folder containing a file in the system file manager."""
    filepath = os.path.normpath(filepath)
    if sys.platform == "win32":
        if os.path.exists(filepath):
            subprocess.Popen(["explorer", "/select,", filepath])
        else:
            folder = os.path.dirname(filepath)
            if os.path.exists(folder):
                subprocess.Popen(["explorer", folder])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", filepath])
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(filepath)])


def bind_tree(widget, event, callback):
    """Bind an event to a widget and all its descendants."""
    widget.bind(event, callback, add="+")
    for child in widget.winfo_children():
        bind_tree(child, event, callback)
