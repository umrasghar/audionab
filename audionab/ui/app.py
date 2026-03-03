"""Main AudioNab application window."""

import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, Menu, StringVar

try:
    import customtkinter as ctk
except ImportError:
    try:
        from tkinter import Tk, messagebox as _mb
        _r = Tk()
        _r.withdraw()
        _mb.showerror(
            "AudioNab",
            "customtkinter is required.\n\n"
            "Install it with:\npip install customtkinter"
        )
    except Exception:
        print("ERROR: pip install customtkinter")
    sys.exit(1)

from .. import (
    APP_NAME, APP_VERSION, APP_TAGLINE,
    SUPPORTED_ALL, SUPPORTED_VIDEO, SUPPORTED_AUDIO,
    OUTPUT_FORMATS,
    C_SUCCESS, C_ERROR, C_WARNING, C_ACCENT, C_PURPLE,
)
from ..converter import Converter
from ..database import HistoryDB
from ..config import Config
from ..context_menu import ContextMenuManager
from ..helpers import format_size, format_time_ago, open_folder, bind_tree
from ..transcriber import transcribe
from ..tray import TrayManager, HAS_PYSTRAY
from ..watcher import FolderWatcher, HAS_WATCHDOG
from .settings import SettingsWindow
from .toast import ToastManager

logger = logging.getLogger(__name__)

DB_NAME = "audionab_history.db"
CONFIG_NAME = "audionab_config.json"


class AudioNabApp:
    def __init__(self):
        self.app_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            APP_NAME
        )
        os.makedirs(self.app_dir, exist_ok=True)

        self.db = HistoryDB(os.path.join(self.app_dir, DB_NAME))
        self.config = Config(os.path.join(self.app_dir, CONFIG_NAME))

        self.converting = False
        self._cancel_event = threading.Event()
        self._selected_data = None
        self.ffmpeg_path = Converter.find_ffmpeg()
        self.ffprobe_path = Converter.find_ffprobe(self.ffmpeg_path)

        ctk.set_appearance_mode(self.config.get("appearance_mode"))
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(APP_NAME)
        self.root.geometry("960x700")
        self.root.minsize(740, 520)

        # Set window icon
        icon_path = self._find_icon()
        if icon_path:
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                logger.debug("Failed to set window icon", exc_info=True)

        self.toast = ToastManager(self.root)

        # System tray
        self.tray = TrayManager(self)
        if HAS_PYSTRAY:
            self.tray.start()

        # Watch folder
        self.watcher = FolderWatcher(
            self.config, self.db, self.ffmpeg_path, self.ffprobe_path,
            on_conversion_done=self._on_watch_conversion
        )

        self._build_ui()
        self._refresh_history()
        self._setup_dnd()
        self._setup_shortcuts()

        # Handle window close — minimize to tray or quit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Auto-start watch folder if configured
        watch_folder = self.config.get("watch_folder")
        if self.config.get("watch_enabled") and watch_folder:
            self.watcher.start(watch_folder)

    def _find_icon(self):
        """Locate the .ico file — checks bundled (frozen) and dev locations."""
        candidates = []
        if getattr(sys, 'frozen', False):
            # PyInstaller onefile extraction dir
            meipass = getattr(sys, '_MEIPASS', '')
            if meipass:
                candidates.append(Path(meipass) / "assets" / "icon.ico")
            # Installed / Nuitka location (next to exe)
            candidates.append(Path(sys.executable).parent / "assets" / "icon.ico")
        else:
            # Dev mode — project root
            candidates.append(
                Path(__file__).resolve().parent.parent.parent / "assets" / "icon.ico"
            )
        for c in candidates:
            if c.exists():
                return str(c)
        return None

    def _build_ui(self):
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=18)
        self._main_frame = main

        self._build_header(main)
        self._build_ffmpeg_banner(main)
        self._build_stats(main)
        self._build_progress(main)
        self._build_history(main)
        self._build_status(main)

    # -- Header --
    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(
            title_row, text="AudioNab",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(side="left")
        ctk.CTkLabel(
            title_row, text=f"  v{APP_VERSION}",
            font=ctk.CTkFont(size=12), text_color="gray45"
        ).pack(side="left", pady=(8, 0))

        ffmpeg_ok = bool(self.ffmpeg_path)
        tag = f"{APP_TAGLINE}   ·   FFmpeg {'ready' if ffmpeg_ok else 'not found!'}"
        tag_color = "gray50" if ffmpeg_ok else C_ERROR
        self.tagline_label = ctk.CTkLabel(
            left, text=tag, font=ctk.CTkFont(size=12), text_color=tag_color
        )
        self.tagline_label.pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        self.convert_btn = ctk.CTkButton(
            right, text="  Nab Audio  ",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, corner_radius=12,
            command=self._pick_files
        )
        self.convert_btn.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            right, text="Settings",
            fg_color=("gray78", "gray25"), hover_color=("gray68", "gray32"),
            text_color=("gray15", "gray85"),
            height=44, corner_radius=12, font=ctk.CTkFont(size=13),
            command=self._show_settings
        ).pack(side="left")

    # -- FFmpeg banner --
    def _build_ffmpeg_banner(self, parent):
        if self.ffmpeg_path:
            return
        banner = ctk.CTkFrame(parent, fg_color="#7f1d1d", corner_radius=10)
        banner.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            banner,
            text="  FFmpeg not found  ---  Install via PowerShell:  winget install Gyan.FFmpeg",
            font=ctk.CTkFont(size=12), text_color="#fca5a5"
        ).pack(padx=16, pady=12)

    # -- Stats cards --
    def _build_stats(self, parent):
        self._stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._stats_frame.pack(fill="x", pady=(0, 14))
        self._stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        stats = self.db.get_stats()
        self.stat_widgets = {}

        # Hide stats if no conversions yet
        if stats["total"] == 0:
            self._stats_frame.pack_forget()
            self._stats_hidden = True
        else:
            self._stats_hidden = False

        defs = [
            ("total", "Total Nabbed", str(stats["total"]), C_ACCENT),
            ("success", "Successful", str(stats["success"]), C_SUCCESS),
            ("failed", "Failed", str(stats["failed"]), C_ERROR if stats["failed"] else "gray45"),
            ("saved", "Space Saved",
             format_size(max(0, stats["total_input"] - stats["total_output"])),
             C_PURPLE),
        ]

        for i, (key, label, value, color) in enumerate(defs):
            card = ctk.CTkFrame(self._stats_frame, corner_radius=12)
            card.grid(
                row=0, column=i, sticky="nsew",
                padx=(0 if i == 0 else 5, 0 if i == 3 else 5), pady=2
            )

            accent = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=2)
            accent.pack(fill="x", padx=16, pady=(12, 0))

            val_label = ctk.CTkLabel(
                card, text=value,
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=color
            )
            val_label.pack(anchor="w", padx=16, pady=(8, 0))

            ctk.CTkLabel(
                card, text=label,
                font=ctk.CTkFont(size=11), text_color="gray50"
            ).pack(anchor="w", padx=16, pady=(2, 14))

            self.stat_widgets[key] = (val_label, accent)

    # -- Progress (hidden) --
    def _build_progress(self, parent):
        self.progress_frame = ctk.CTkFrame(parent, corner_radius=12)

        self.progress_title = ctk.CTkLabel(
            self.progress_frame, text="Nabbing audio...",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.progress_title.pack(anchor="w", padx=18, pady=(14, 0))

        self.progress_detail = ctk.CTkLabel(
            self.progress_frame, text="",
            font=ctk.CTkFont(size=11), text_color="gray50"
        )
        self.progress_detail.pack(anchor="w", padx=18, pady=(2, 10))

        bar_row = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        bar_row.pack(fill="x", padx=18, pady=(0, 14))

        self.progress_bar = ctk.CTkProgressBar(bar_row, height=6, corner_radius=3)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 14))
        self.progress_bar.set(0)

        self.cancel_btn = ctk.CTkButton(
            bar_row, text="Cancel", width=80, height=32, corner_radius=8,
            fg_color=("gray78", "gray30"), hover_color=("gray68", "gray38"),
            text_color=("gray15", "gray85"),
            command=self._cancel_conversion
        )
        self.cancel_btn.pack(side="right")

    # -- History (card-based) --
    def _build_history(self, parent):
        hist_header = ctk.CTkFrame(parent, fg_color="transparent")
        hist_header.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            hist_header, text="History",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            hist_header, text="Clear All", width=75, height=30,
            corner_radius=8,
            fg_color=("gray78", "gray25"), hover_color=("gray68", "gray32"),
            text_color=("gray15", "gray85"),
            font=ctk.CTkFont(size=11),
            command=self._clear_history
        ).pack(side="right")

        # Search + filter bar
        search_bar = ctk.CTkFrame(parent, fg_color="transparent")
        search_bar.pack(fill="x", pady=(0, 8))

        self._search_var = StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_changed())
        search_entry = ctk.CTkEntry(
            search_bar, textvariable=self._search_var,
            placeholder_text="Search files...",
            width=250, height=32, corner_radius=8
        )
        search_entry.pack(side="left")

        self._filter_var = StringVar(value="All")
        self._filter_seg = ctk.CTkSegmentedButton(
            search_bar, values=["All", "Success", "Failed"],
            variable=self._filter_var,
            command=lambda v: self._refresh_history(),
            height=32
        )
        self._filter_seg.pack(side="right")

        self._search_debounce_id = None

        self.history_scroll = ctk.CTkScrollableFrame(
            parent, corner_radius=12,
            fg_color=("gray92", "#181825")
        )
        self.history_scroll.pack(fill="both", expand=True)

        self._ctx_menu = Menu(self.root, tearoff=0, font=("Segoe UI", 9))
        self._ctx_menu.add_command(label="Open Output Folder", command=self._open_output_folder)
        self._ctx_menu.add_command(label="Open Source Folder", command=self._open_source_folder)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="Transcribe", command=self._transcribe_selected)
        self._ctx_menu.add_command(label="Re-convert", command=self._reconvert_selected)
        self._ctx_menu.add_command(label="Delete Entry", command=self._delete_selected)

    def _show_empty_state(self):
        empty = ctk.CTkFrame(self.history_scroll, fg_color="transparent", height=200)
        empty.pack(fill="both", expand=True, pady=40)
        empty.pack_propagate(False)

        ctk.CTkLabel(
            empty, text="No conversions yet",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="gray40"
        ).pack(pady=(30, 4))
        ctk.CTkLabel(
            empty,
            text="Drop files here or click  Nab Audio  to get started\nSupports 30+ video and audio formats",
            font=ctk.CTkFont(size=12), text_color="gray45",
            justify="center"
        ).pack()

    def _create_history_row(self, data, is_even):
        dark = ctk.get_appearance_mode() == "Dark"
        if dark:
            bg = "#1e1e2e" if is_even else "#1a1a28"
            hover_bg = "#282840"
        else:
            bg = "#f0f0f5" if is_even else "#e8e8ed"
            hover_bg = "#d8d8e0"

        card = ctk.CTkFrame(
            self.history_scroll, corner_radius=10, height=62,
            fg_color=bg, cursor="hand2"
        )
        card.pack(fill="x", pady=2, padx=4)
        card.pack_propagate(False)

        status = data["status"]
        if status == "success":
            dot_color = C_SUCCESS
        elif status == "failed":
            dot_color = C_ERROR
        else:
            dot_color = C_WARNING

        # Top row: status dot + filename + format badge
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(10, 0))

        ctk.CTkLabel(
            top, text="\u25cf", text_color=dot_color,
            font=ctk.CTkFont(size=14), width=18
        ).pack(side="left")

        ctk.CTkLabel(
            top, text=data["source_name"],
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(side="left", padx=(4, 0))

        fmt_badge = ctk.CTkLabel(
            top, text=data["source_format"],
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray55"),
            fg_color=("gray82", "#2a2a3e"),
            corner_radius=4, width=44, height=20
        )
        fmt_badge.pack(side="right")

        # Bottom row: details
        bot = ctk.CTkFrame(card, fg_color="transparent")
        bot.pack(fill="x", padx=14, pady=(2, 10))

        if status == "failed" and data.get("error_msg"):
            detail_text = data["error_msg"][:80]
            detail_color = C_ERROR
        else:
            parts = []
            in_size = format_size(data["source_size"])
            out_size = format_size(data["output_size"]) if data["output_size"] else "---"
            parts.append(f"{in_size}  ->  {out_size}")
            parts.append(data["bitrate"])
            parts.append(format_time_ago(data["created_at"]))
            detail_text = "   \u00b7   ".join(parts)
            detail_color = ("gray45", "gray50")

        ctk.CTkLabel(
            bot, text=detail_text,
            font=ctk.CTkFont(size=11), text_color=detail_color,
            anchor="w"
        ).pack(side="left", padx=(22, 0))

        # Hover + click bindings
        def on_enter(e):
            card.configure(fg_color=hover_bg)

        def on_leave(e):
            card.configure(fg_color=bg)

        def on_click(e):
            self._selected_data = data

        def on_double(e):
            self._selected_data = data
            if data["output_path"]:
                open_folder(data["output_path"])

        def on_right(e):
            self._selected_data = data
            self._ctx_menu.post(e.x_root, e.y_root)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        bind_tree(card, "<Button-1>", on_click)
        bind_tree(card, "<Double-Button-1>", on_double)
        bind_tree(card, "<Button-3>", on_right)

        return card

    # -- Status bar --
    def _build_status(self, parent):
        self.status_var = StringVar(value="Ready --- drop files or click Nab Audio")
        self.status_label = ctk.CTkLabel(
            parent, textvariable=self.status_var,
            font=ctk.CTkFont(size=11), text_color="gray45"
        )
        self.status_label.pack(fill="x", pady=(10, 0), anchor="w")

    # -- Keyboard shortcuts --
    def _setup_shortcuts(self):
        self.root.bind("<Control-o>", lambda e: self._pick_files())
        self.root.bind("<Control-O>", lambda e: self._pick_files())
        self.root.bind("<Escape>", lambda e: self._cancel_conversion() if self.converting else None)
        self.root.bind("<Control-comma>", lambda e: self._show_settings())
        self.root.bind("<F5>", lambda e: self._refresh_all())

    def _refresh_all(self):
        self._refresh_history()
        self._refresh_stats()

    # -- Drag & drop --
    def _setup_dnd(self):
        try:
            import windnd

            def handle_drop(files):
                paths = []
                for f in files:
                    p = f.decode("utf-8") if isinstance(f, bytes) else str(f)
                    if Path(p).suffix.lower() in SUPPORTED_ALL:
                        paths.append(p)
                if paths:
                    self._convert_files(paths)
                else:
                    self.status_var.set("Dropped files are not in a supported format")

            windnd.hook_dropfiles(self.root, func=handle_drop)
            self.status_var.set("Ready --- drop files here or click Nab Audio")
        except ImportError:
            pass

    # -- Conversion --
    def _pick_files(self):
        if self.converting:
            return
        filetypes = [
            ("All Supported", " ".join(f"*{e}" for e in SUPPORTED_ALL)),
            ("Video Files", " ".join(f"*{e}" for e in SUPPORTED_VIDEO)),
            ("Audio Files", " ".join(f"*{e}" for e in SUPPORTED_AUDIO)),
            ("All Files", "*.*")
        ]
        files = filedialog.askopenfilenames(
            title="Select files to nab audio from", filetypes=filetypes
        )
        if files:
            self._convert_files(list(files))

    def _convert_files(self, file_paths):
        if not self.ffmpeg_path:
            self.toast.show(
                "FFmpeg is not installed. Run: winget install Gyan.FFmpeg",
                level="error", duration=8000
            )
            return
        if self.converting:
            return

        self.converting = True
        self._cancel_event.clear()
        self.convert_btn.configure(state="disabled")

        self.progress_frame.pack(
            fill="x", pady=(0, 14),
            before=self.history_scroll.master if hasattr(self.history_scroll, 'master') else self.history_scroll
        )
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        thread = threading.Thread(target=self._do_conversions, args=(file_paths,), daemon=True)
        thread.start()

    def _do_conversions(self, file_paths):
        bitrate = self.config.get("bitrate")
        fmt_name = self.config.get("output_format") or "MP3"
        fmt = OUTPUT_FORMATS.get(fmt_name, OUTPUT_FORMATS["MP3"])
        postfix = self.config.get("output_postfix") or ""
        total = len(file_paths)
        completed = 0
        skipped = 0

        for idx, src_path in enumerate(file_paths, 1):
            if self._cancel_event.is_set():
                break

            src = Path(src_path)
            self.root.after(0, lambda i=idx, n=src.name:
                            self._update_progress(f"Nabbing {i}/{total}", n))

            # FFprobe pre-check
            if self.ffprobe_path:
                probe = Converter.probe(str(src), self.ffprobe_path)
                if not probe["has_audio"] and probe["error"] is None:
                    row_id = self.db.add_conversion(str(src), "", bitrate)
                    self.db.update_conversion(
                        row_id, status="failed",
                        error_msg="No audio stream found in file",
                        completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    skipped += 1
                    continue

            if self.config.get("output_same_folder") or not self.config.get("custom_output_folder"):
                out_dir = src.parent
            else:
                out_dir = Path(self.config.get("custom_output_folder"))
                out_dir.mkdir(parents=True, exist_ok=True)

            out_name = f"{src.stem}{postfix}{fmt['ext']}"
            output_path = Converter.get_unique_output(str(out_dir / out_name))

            if not src.exists():
                continue
            if src.stat().st_size == 0:
                row_id = self.db.add_conversion(str(src), output_path, bitrate)
                self.db.update_conversion(
                    row_id, status="failed",
                    error_msg="File is empty (0 bytes)",
                    completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                continue

            row_id = self.db.add_conversion(str(src), output_path, bitrate)
            start_time = time.time()

            def progress_cb(msg, rid=row_id):
                self.root.after(0, lambda: self.progress_detail.configure(text=msg))

            success, pass_used, error_msg = Converter.convert(
                str(src), output_path, bitrate,
                ffmpeg_path=self.ffmpeg_path,
                progress_callback=progress_cb,
                cancel_event=self._cancel_event,
                output_format=fmt
            )
            duration = round(time.time() - start_time, 2)

            if self._cancel_event.is_set():
                self.db.update_conversion(
                    row_id, status="failed", error_msg="Cancelled",
                    duration_secs=duration,
                    completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception:
                    pass
                break

            if success:
                out_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                self.db.update_conversion(
                    row_id, status="success", pass_used=pass_used,
                    output_size=out_size, duration_secs=duration,
                    output_path=output_path,
                    completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                completed += 1

                # Auto-transcribe if enabled
                if self.config.get("auto_transcribe") and self.config.get("deepgram_api_key"):
                    self.root.after(0, lambda p=output_path, rid=row_id:
                                    self._start_transcription(p, rid))
            else:
                self.db.update_conversion(
                    row_id, status="failed", error_msg=error_msg,
                    duration_secs=duration,
                    completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

        cancelled = self._cancel_event.is_set()
        self.root.after(0, self._conversion_done, total, completed, cancelled, skipped)

    def _cancel_conversion(self):
        self._cancel_event.set()
        self.cancel_btn.configure(state="disabled", text="Cancelling...")

    def _update_progress(self, title, detail):
        self.progress_title.configure(text=title)
        self.progress_detail.configure(text=detail)

    def _conversion_done(self, total, completed, cancelled, skipped=0):
        self.converting = False
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="normal", text="Cancel")
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self._refresh_history()
        self._refresh_stats()

        if cancelled:
            msg = f"Cancelled --- {completed}/{total} file(s) completed"
            self.toast.show(msg, level="warning")
        elif skipped:
            msg = f"Done! Nabbed {completed} file(s), {skipped} skipped (no audio)"
            self.toast.show(msg, level="info")
        else:
            msg = f"Done! Nabbed audio from {completed} file(s)"
            self.toast.show(msg, level="success")

        self.status_var.set(msg)

        # Tray notification (useful when minimized)
        if not cancelled:
            self.tray.notify("AudioNab", msg)

    # -- Search --
    def _on_search_changed(self):
        """Debounce search input — refresh after 300ms of no typing."""
        if self._search_debounce_id:
            self.root.after_cancel(self._search_debounce_id)
        self._search_debounce_id = self.root.after(300, self._refresh_history)

    # -- History management --
    def _refresh_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        rows = self.db.get_history(limit=200)

        # Apply filter
        filter_val = getattr(self, '_filter_var', None)
        if filter_val:
            f = filter_val.get()
            if f == "Success":
                rows = [r for r in rows if r["status"] == "success"]
            elif f == "Failed":
                rows = [r for r in rows if r["status"] == "failed"]

        # Apply search
        search_var = getattr(self, '_search_var', None)
        if search_var:
            query = search_var.get().strip().lower()
            if query:
                rows = [r for r in rows if query in r["source_name"].lower()]

        if not rows:
            self._show_empty_state()
            return

        for i, row in enumerate(rows):
            self._create_history_row(dict(row), i % 2 == 0)

    def _refresh_stats(self):
        stats = self.db.get_stats()

        # Show stats frame if it was hidden and we now have conversions
        if getattr(self, '_stats_hidden', False) and stats["total"] > 0:
            self._stats_frame.pack(fill="x", pady=(0, 14),
                                   after=self.tagline_label.master.master)
            self._stats_hidden = False

        self.stat_widgets["total"][0].configure(text=str(stats["total"]))
        self.stat_widgets["success"][0].configure(text=str(stats["success"]))
        self.stat_widgets["failed"][0].configure(text=str(stats["failed"]))

        fail_color = C_ERROR if stats["failed"] else "gray45"
        self.stat_widgets["failed"][0].configure(text_color=fail_color)
        self.stat_widgets["failed"][1].configure(fg_color=fail_color)

        saved = max(0, stats["total_input"] - stats["total_output"])
        self.stat_widgets["saved"][0].configure(text=format_size(saved))

    def _clear_history(self):
        if messagebox.askyesno("Clear History",
                               "Delete all conversion history?\n(No files will be deleted)"):
            self.db.clear_history()
            self._refresh_history()
            self._refresh_stats()
            self.status_var.set("History cleared")

    def _open_output_folder(self):
        if self._selected_data and self._selected_data.get("output_path"):
            open_folder(self._selected_data["output_path"])

    def _open_source_folder(self):
        if self._selected_data and self._selected_data.get("source_path"):
            open_folder(self._selected_data["source_path"])

    def _reconvert_selected(self):
        if not self._selected_data:
            return
        if os.path.exists(self._selected_data["source_path"]):
            self._convert_files([self._selected_data["source_path"]])
        else:
            self.toast.show(
                f"Source file no longer exists: {self._selected_data['source_name']}",
                level="error"
            )

    def _delete_selected(self):
        if self._selected_data:
            self.db.delete_entry(self._selected_data["id"])
            self._selected_data = None
            self._refresh_history()
            self._refresh_stats()

    def _transcribe_selected(self):
        """Transcribe the selected history entry."""
        if not self._selected_data:
            return
        output_path = self._selected_data.get("output_path", "")
        row_id = self._selected_data.get("id")
        if output_path and os.path.exists(output_path):
            self._start_transcription(output_path, row_id)
        else:
            self.toast.show("Output file not found", level="error")

    def _start_transcription(self, audio_path, row_id):
        """Start transcription in a background thread."""
        api_key = self.config.get("deepgram_api_key")
        if not api_key:
            self.toast.show("Set Deepgram API key in Settings first", level="warning")
            return

        self.toast.show(f"Transcribing {Path(audio_path).name}...", level="info", duration=0)

        def _do_transcribe():
            result = transcribe(audio_path, api_key)
            self.root.after(0, lambda: self._transcription_done(result, row_id))

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def _transcription_done(self, result, row_id):
        """Handle transcription result on the main thread."""
        self.toast.dismiss()
        if result["success"]:
            self.toast.show(
                f"Transcript saved: {Path(result['output_path']).name}",
                level="success"
            )
            self.db.update_conversion(row_id, transcript_path=result["output_path"])
            self._refresh_history()
        else:
            self.toast.show(f"Transcription failed: {result['error']}", level="error")

    def _show_settings(self):
        SettingsWindow(self.root, self.config, self.app_dir, self.ffmpeg_path,
                       watcher=self.watcher)

    def _on_watch_conversion(self, filename, success):
        """Called from watcher thread when an auto-conversion finishes."""
        def _update():
            self._refresh_history()
            self._refresh_stats()
            if success:
                self.toast.show(f"Auto-nabbed: {filename}", level="success")
                self.tray.notify("AudioNab", f"Auto-nabbed: {filename}")
            else:
                self.toast.show(f"Auto-nab failed: {filename}", level="error")
        self.root.after(0, _update)

    def _on_close(self):
        """Handle window close — minimize to tray or quit."""
        if self.config.get("close_to_tray") and HAS_PYSTRAY:
            self.root.withdraw()
            self.tray.notify("AudioNab", "Minimized to tray. Right-click to quit.")
        else:
            self.watcher.stop()
            self.tray.stop()
            self.root.destroy()

    def run(self):
        self.root.mainloop()
