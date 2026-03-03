"""AudioNab entry point — supports both GUI and CLI modes."""

import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import APP_NAME, APP_VERSION, DB_NAME, CONFIG_NAME, OUTPUT_FORMATS
from .converter import Converter
from .database import HistoryDB
from .config import Config
from .context_menu import ContextMenuManager
from .helpers import format_size


def setup_logging():
    """Configure rotating file logger."""
    log_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        APP_NAME
    )
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "audionab.log")

    handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    root_logger = logging.getLogger("audionab")
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    return root_logger


def cli_convert(file_path):
    """Convert a single file from the command line."""
    app_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        APP_NAME
    )
    os.makedirs(app_dir, exist_ok=True)

    db = HistoryDB(os.path.join(app_dir, DB_NAME))
    config = Config(os.path.join(app_dir, CONFIG_NAME))
    ffmpeg_path = Converter.find_ffmpeg()

    if not ffmpeg_path:
        print("\n  [ERROR] FFmpeg not found. Install via: winget install Gyan.FFmpeg")
        input("  Press Enter to close...")
        return

    src = Path(file_path)
    if not src.exists():
        print(f"\n  [ERROR] File not found: {file_path}")
        input("  Press Enter to close...")
        return
    if src.stat().st_size == 0:
        print(f"\n  [ERROR] File is empty: {file_path}")
        input("  Press Enter to close...")
        return

    bitrate = config.get("bitrate")
    fmt_name = config.get("output_format") or "MP3"
    fmt = OUTPUT_FORMATS.get(fmt_name, OUTPUT_FORMATS["MP3"])
    postfix = config.get("output_postfix") or ""

    if config.get("output_same_folder") or not config.get("custom_output_folder"):
        out_dir = src.parent
    else:
        out_dir = Path(config.get("custom_output_folder"))
        out_dir.mkdir(parents=True, exist_ok=True)

    out_name = f"{src.stem}{postfix}{fmt['ext']}"
    output_path = Converter.get_unique_output(str(out_dir / out_name))
    row_id = db.add_conversion(str(src), output_path, bitrate)

    print(f"\n  +--------------------------------------+")
    print(f"  |  AudioNab v{APP_VERSION:<26s}|")
    print(f"  +--------------------------------------+\n")
    print(f"   Input:   {src.name}")
    print(f"   Size:    {format_size(src.stat().st_size)}")
    print(f"   Format:  {fmt_name}")
    print(f"   Bitrate: {bitrate}\n")

    start_time = time.time()
    success, pass_used, error_msg = Converter.convert(
        str(src), output_path, bitrate,
        ffmpeg_path=ffmpeg_path,
        progress_callback=lambda msg: print(f"   {msg}"),
        output_format=fmt
    )
    duration = round(time.time() - start_time, 2)

    if success:
        out_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        db.update_conversion(
            row_id, status="success", pass_used=pass_used,
            output_size=out_size, duration_secs=duration,
            output_path=output_path,
            completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        print(f"\n  +--------------------------------------+")
        print(f"  |  Audio nabbed successfully!           |")
        print(f"  +--------------------------------------+")
        print(f"   Output: {Path(output_path).name}")
        print(f"   Size:   {format_size(out_size)}")
        print(f"   Time:   {duration}s (Pass {pass_used})\n")
        time.sleep(3)
    else:
        db.update_conversion(
            row_id, status="failed", error_msg=error_msg,
            duration_secs=duration,
            completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        print(f"\n  [FAILED] {error_msg}")
        input("  Press Enter to close...")


def cli_install():
    """Install context menu from CLI."""
    app_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        APP_NAME
    )
    if ContextMenuManager.install(app_dir):
        print("AudioNab context menu installed!")
    else:
        print("Failed to install context menu.")
    time.sleep(2)


def cli_uninstall():
    """Uninstall context menu from CLI."""
    if ContextMenuManager.uninstall():
        print("AudioNab context menu uninstalled!")
    else:
        print("Failed to uninstall context menu.")
    time.sleep(2)


def main():
    """Main entry point — route to CLI or GUI."""
    logger = setup_logging()
    logger.info("AudioNab v%s starting (args: %s)", APP_VERSION, sys.argv[1:])

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--convert" and len(sys.argv) > 2:
            cli_convert(sys.argv[2])
            return
        elif cmd == "--install":
            cli_install()
            return
        elif cmd == "--uninstall":
            cli_uninstall()
            return
        elif cmd == "--enable-classic-menu":
            if ContextMenuManager.enable_classic_menu():
                print("Classic context menu enabled!")
            time.sleep(1)
            return
        elif cmd == "--disable-classic-menu":
            if ContextMenuManager.disable_classic_menu():
                print("Classic context menu disabled!")
            time.sleep(1)
            return
        elif os.path.isfile(cmd):
            cli_convert(cmd)
            return

    # GUI mode
    from .ui.app import AudioNabApp
    app = AudioNabApp()
    app.run()


if __name__ == "__main__":
    main()
