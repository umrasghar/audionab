"""Watch folder for auto-conversion of new video files."""

import logging
import os
import threading
import time
from pathlib import Path

from . import SUPPORTED_VIDEO, OUTPUT_FORMATS
from .converter import Converter

logger = logging.getLogger(__name__)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


class _StableFileHandler(FileSystemEventHandler):
    """Detects new video files and waits for them to stabilize before converting."""

    STABILIZE_SECS = 5  # Wait for file to stop growing

    def __init__(self, on_stable_file):
        super().__init__()
        self._on_stable_file = on_stable_file
        self._pending = {}  # path -> last_size
        self._lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        ext = Path(event.src_path).suffix.lower()
        if ext in SUPPORTED_VIDEO:
            logger.debug("Watch: new file detected: %s", event.src_path)
            with self._lock:
                self._pending[event.src_path] = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        # Also catch modified events for files that existed before observer started
        ext = Path(event.src_path).suffix.lower()
        if ext in SUPPORTED_VIDEO:
            with self._lock:
                if event.src_path not in self._pending:
                    self._pending[event.src_path] = 0

    def check_pending(self):
        """Called periodically to check if pending files have stabilized."""
        with self._lock:
            paths = list(self._pending.keys())

        stable = []
        for path in paths:
            try:
                if not os.path.exists(path):
                    with self._lock:
                        self._pending.pop(path, None)
                    continue

                current_size = os.path.getsize(path)
                with self._lock:
                    last_size = self._pending.get(path, 0)
                    if current_size == last_size and current_size > 0:
                        # File hasn't changed — it's stable
                        stable.append(path)
                        del self._pending[path]
                    else:
                        self._pending[path] = current_size
            except Exception:
                pass

        for path in stable:
            logger.info("Watch: file stabilized: %s", path)
            self._on_stable_file(path)


class FolderWatcher:
    """Watches a folder for new video files and auto-converts them."""

    def __init__(self, config, db, ffmpeg_path, ffprobe_path=None,
                 on_conversion_done=None):
        self.config = config
        self.db = db
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.on_conversion_done = on_conversion_done
        self._observer = None
        self._handler = None
        self._poll_thread = None
        self._running = False

    @property
    def is_running(self):
        return self._running

    def start(self, folder_path):
        """Start watching a folder."""
        if not HAS_WATCHDOG:
            logger.warning("watchdog not installed, cannot start folder watcher")
            return False

        if self._running:
            self.stop()

        if not os.path.isdir(folder_path):
            logger.warning("Watch folder does not exist: %s", folder_path)
            return False

        self._handler = _StableFileHandler(self._on_new_file)
        self._observer = Observer()
        self._observer.schedule(self._handler, folder_path, recursive=False)
        self._observer.daemon = True
        self._observer.start()
        self._running = True

        # Start polling thread for stability checks
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        logger.info("Watch folder started: %s", folder_path)
        return True

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=3)
            except Exception:
                pass
            self._observer = None
        self._handler = None
        logger.info("Watch folder stopped")

    def _poll_loop(self):
        """Periodically check pending files for stability."""
        while self._running:
            time.sleep(2)
            if self._handler:
                try:
                    self._handler.check_pending()
                except Exception:
                    logger.debug("Poll check error", exc_info=True)

    def _on_new_file(self, file_path):
        """Called when a new video file has stabilized."""
        src = Path(file_path)
        fmt_name = self.config.get("output_format") or "MP3"
        fmt = OUTPUT_FORMATS.get(fmt_name, OUTPUT_FORMATS["MP3"])
        postfix = self.config.get("output_postfix") or ""
        bitrate = self.config.get("bitrate")

        out_name = f"{src.stem}{postfix}{fmt['ext']}"
        output_path = str(src.parent / out_name)

        # Don't re-convert if output already exists
        if os.path.exists(output_path):
            logger.debug("Watch: output already exists, skipping: %s", output_path)
            return

        output_path = Converter.get_unique_output(output_path)

        # FFprobe pre-check
        if self.ffprobe_path:
            probe = Converter.probe(str(src), self.ffprobe_path)
            if not probe["has_audio"] and probe["error"] is None:
                logger.info("Watch: no audio stream in %s, skipping", src.name)
                return

        logger.info("Watch: auto-converting %s -> %s", src.name, Path(output_path).name)

        row_id = self.db.add_conversion(str(src), output_path, bitrate)
        start_time = time.time()

        success, pass_used, error_msg = Converter.convert(
            str(src), output_path, bitrate,
            ffmpeg_path=self.ffmpeg_path,
            output_format=fmt
        )
        duration = round(time.time() - start_time, 2)

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if success:
            out_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            self.db.update_conversion(
                row_id, status="success", pass_used=pass_used,
                output_size=out_size, duration_secs=duration,
                output_path=output_path, completed_at=now
            )
            logger.info("Watch: converted %s in %.1fs", src.name, duration)
        else:
            self.db.update_conversion(
                row_id, status="failed", error_msg=error_msg,
                duration_secs=duration, completed_at=now
            )
            logger.warning("Watch: failed to convert %s: %s", src.name, error_msg)

        if self.on_conversion_done:
            self.on_conversion_done(src.name, success)
