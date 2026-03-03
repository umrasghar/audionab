"""System tray integration using pystray."""

import logging
import threading

logger = logging.getLogger(__name__)

# Attempt to import pystray — optional dependency
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False


def _create_icon_image(size=64):
    """Load AudioNab icon from assets, or generate dynamically as fallback."""
    # Try loading pre-built icon
    try:
        import sys
        from pathlib import Path as _Path
        if getattr(sys, 'frozen', False):
            bases = []
            meipass = getattr(sys, '_MEIPASS', '')
            if meipass:
                bases.append(_Path(meipass))
            bases.append(_Path(sys.executable).parent)
        else:
            bases = [_Path(__file__).resolve().parent.parent]
        for base in bases:
            icon_path = base / "assets" / "icon-64.png"
            if icon_path.exists():
                img = Image.open(str(icon_path))
                if size != 64:
                    img = img.resize((size, size), Image.LANCZOS)
                return img
    except Exception:
        pass

    # Fallback: generate dynamically
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size - 3, size - 3], fill="#7aa2f7")
    cx, cy = size // 2, size // 2
    s = size // 4
    draw.polygon([
        (cx, cy - s - 2),
        (cx - s, cy + s),
        (cx + s, cy + s)
    ], fill="white")
    inner_s = s // 2
    draw.polygon([
        (cx, cy - inner_s + 4),
        (cx - inner_s, cy + s),
        (cx + inner_s, cy + s)
    ], fill="#7aa2f7")
    draw.rectangle([cx - s + 4, cy + 2, cx + s - 4, cy + 6], fill="white")
    return img


class TrayManager:
    """Manages the system tray icon and menu."""

    def __init__(self, app):
        """
        Args:
            app: AudioNabApp instance with .root, .config, .toast methods
        """
        self.app = app
        self.icon = None
        self._thread = None

    def start(self):
        """Start the tray icon in a daemon thread."""
        if not HAS_PYSTRAY:
            logger.debug("pystray not available, skipping tray")
            return

        menu = pystray.Menu(
            pystray.MenuItem("Open AudioNab", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

        self.icon = pystray.Icon(
            "AudioNab",
            _create_icon_image(),
            "AudioNab",
            menu
        )

        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()
        logger.debug("Tray icon started")

    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None

    def notify(self, title, message):
        """Show a Windows balloon notification."""
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                logger.debug("Tray notification failed", exc_info=True)

    def _on_show(self, icon=None, item=None):
        """Show/restore the main window."""
        self.app.root.after(0, self._restore_window)

    def _restore_window(self):
        self.app.root.deiconify()
        self.app.root.lift()
        self.app.root.focus_force()

    def _on_quit(self, icon=None, item=None):
        """Quit the application."""
        self.stop()
        self.app.root.after(0, self.app.root.destroy)
