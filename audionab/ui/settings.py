"""Settings window for AudioNab."""

import logging
from tkinter import filedialog, messagebox, StringVar, BooleanVar

try:
    import customtkinter as ctk
except ImportError:
    pass

from .. import (
    APP_NAME, APP_VERSION, APP_TAGLINE, APP_REPO,
    BITRATE_OPTIONS, OUTPUT_FORMAT_NAMES, C_SUCCESS, C_ERROR,
)
from ..context_menu import ContextMenuManager

logger = logging.getLogger(__name__)


class SettingsWindow:
    def __init__(self, parent, config, app_dir, ffmpeg_path, watcher=None):
        self.config = config
        self.app_dir = app_dir
        self.watcher = watcher

        self.top = ctk.CTkToplevel(parent)
        self.top.title(f"{APP_NAME} --- Settings")
        self.top.geometry("520x750")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.after(10, lambda: self._center(parent))

        self._build(ffmpeg_path)

    def _center(self, parent):
        self.top.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.top.winfo_width(), self.top.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.top.geometry(f"+{x}+{y}")

    def _build(self, ffmpeg_path):
        scroll = ctk.CTkScrollableFrame(self.top, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=22, pady=18)

        # -- Output Format --
        self._section(scroll, "Output Format")
        fmt_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        fmt_frame.pack(fill="x", pady=(0, 4))

        self.format_var = StringVar(value=self.config.get("output_format"))
        ctk.CTkOptionMenu(
            fmt_frame, variable=self.format_var,
            values=OUTPUT_FORMAT_NAMES, width=130
        ).pack(side="left")
        ctk.CTkLabel(
            fmt_frame, text="MP3 (small), FLAC (lossless), WAV (uncompressed)",
            font=ctk.CTkFont(size=11), text_color="gray50"
        ).pack(side="left", padx=14)

        # -- Bitrate --
        self._section(scroll, "Audio Bitrate")
        br_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        br_frame.pack(fill="x", pady=(0, 4))

        self.bitrate_var = StringVar(value=self.config.get("bitrate"))
        ctk.CTkOptionMenu(
            br_frame, variable=self.bitrate_var,
            values=BITRATE_OPTIONS, width=130
        ).pack(side="left")
        ctk.CTkLabel(
            br_frame, text="Higher = better quality, larger file",
            font=ctk.CTkFont(size=11), text_color="gray50"
        ).pack(side="left", padx=14)

        # -- Output Postfix --
        self._section(scroll, "Output File Postfix")
        pf_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        pf_frame.pack(fill="x", pady=(0, 4))

        self.postfix_var = StringVar(value=self.config.get("output_postfix"))
        ctk.CTkEntry(
            pf_frame, textvariable=self.postfix_var,
            width=130, placeholder_text="-mp3"
        ).pack(side="left")
        ctk.CTkLabel(
            pf_frame, text='e.g. recording.mkv -> recording-mp3.mp3  (leave empty for no postfix)',
            font=ctk.CTkFont(size=11), text_color="gray50"
        ).pack(side="left", padx=14)

        # -- Output Location --
        self._section(scroll, "Output Location")

        self.same_folder_var = BooleanVar(value=self.config.get("output_same_folder"))
        ctk.CTkSwitch(
            scroll, text="Save audio next to original file",
            variable=self.same_folder_var, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(0, 8))

        custom_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        custom_frame.pack(fill="x", pady=(0, 4))

        self.custom_folder_var = StringVar(value=self.config.get("custom_output_folder"))
        ctk.CTkEntry(
            custom_frame, textvariable=self.custom_folder_var,
            width=310, placeholder_text="Custom output folder..."
        ).pack(side="left")
        ctk.CTkButton(
            custom_frame, text="Browse", width=75, height=32,
            corner_radius=8,
            fg_color=("gray78", "gray25"), hover_color=("gray68", "gray32"),
            text_color=("gray15", "gray85"),
            command=self._browse_folder
        ).pack(side="left", padx=8)

        # -- Watch Folder --
        self._section(scroll, "Watch Folder (Auto-Convert)")

        self.watch_enabled_var = BooleanVar(value=self.config.get("watch_enabled"))
        ctk.CTkSwitch(
            scroll, text="Auto-convert new videos in watched folder",
            variable=self.watch_enabled_var, font=ctk.CTkFont(size=12),
            command=self._toggle_watch
        ).pack(anchor="w", pady=(0, 8))

        watch_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        watch_frame.pack(fill="x", pady=(0, 4))

        self.watch_folder_var = StringVar(value=self.config.get("watch_folder"))
        ctk.CTkEntry(
            watch_frame, textvariable=self.watch_folder_var,
            width=310, placeholder_text="e.g. C:\\Users\\you\\Videos\\OBS"
        ).pack(side="left")
        ctk.CTkButton(
            watch_frame, text="Browse", width=75, height=32,
            corner_radius=8,
            fg_color=("gray78", "gray25"), hover_color=("gray68", "gray32"),
            text_color=("gray15", "gray85"),
            command=self._browse_watch_folder
        ).pack(side="left", padx=8)

        watcher_running = self.watcher and self.watcher.is_running
        status_text = "Watching..." if watcher_running else "Not watching"
        status_color = C_SUCCESS if watcher_running else "gray45"
        self._watch_status = ctk.CTkLabel(
            scroll, text=status_text,
            font=ctk.CTkFont(size=11), text_color=status_color
        )
        self._watch_status.pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            scroll,
            text="Monitors folder for new .mkv/.mp4 files from OBS.\n"
                 "Auto-converts when recording finishes (file stabilizes).",
            font=ctk.CTkFont(size=11), text_color="gray45", justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # -- Deepgram API --
        self._section(scroll, "Deepgram Transcription")

        dk_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        dk_frame.pack(fill="x", pady=(0, 4))

        self.deepgram_key_var = StringVar(value=self.config.get("deepgram_api_key"))
        self._dk_entry = ctk.CTkEntry(
            dk_frame, textvariable=self.deepgram_key_var,
            width=350, placeholder_text="Deepgram API key...",
            show="*"
        )
        self._dk_entry.pack(side="left")
        ctk.CTkButton(
            dk_frame, text="Show", width=55, height=32,
            corner_radius=8,
            fg_color=("gray78", "gray25"), hover_color=("gray68", "gray32"),
            text_color=("gray15", "gray85"),
            command=self._toggle_key_visibility
        ).pack(side="left", padx=8)

        self.auto_transcribe_var = BooleanVar(value=self.config.get("auto_transcribe"))
        ctk.CTkSwitch(
            scroll, text="Auto-transcribe after conversion",
            variable=self.auto_transcribe_var, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(8, 0))

        ctk.CTkLabel(
            scroll,
            text="Sends converted audio to Deepgram for transcription.\n"
                 "Saves .txt file next to the audio output.",
            font=ctk.CTkFont(size=11), text_color="gray45", justify="left"
        ).pack(anchor="w", pady=(4, 0))

        # -- Right-Click Menu --
        self._section(scroll, "Right-Click Menu")

        ctx_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        ctx_frame.pack(fill="x", pady=(0, 4))

        ctk.CTkButton(
            ctx_frame, text='Install "Nab Audio"',
            width=170, height=38, corner_radius=10,
            command=self._install_ctx
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            ctx_frame, text="Uninstall", width=95, height=38,
            corner_radius=10,
            fg_color=("gray78", "gray25"), hover_color=("gray68", "gray32"),
            text_color=("gray15", "gray85"),
            command=self._uninstall_ctx
        ).pack(side="left")

        ctk.CTkLabel(
            scroll,
            text='Adds "Nab Audio" to right-click for 30+ formats.\nRequires admin privileges.',
            font=ctk.CTkFont(size=11), text_color="gray45", justify="left"
        ).pack(anchor="w", pady=(4, 0))

        # -- Win11 Context Menu --
        self._section(scroll, "Windows 11 Context Menu")

        self.classic_menu_var = BooleanVar(value=ContextMenuManager.is_classic_menu_enabled())
        ctk.CTkSwitch(
            scroll, text="Show full context menu (skip 'Show more options')",
            variable=self.classic_menu_var, font=ctk.CTkFont(size=12),
            command=self._toggle_classic_menu
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            scroll,
            text=(
                "Enables classic full right-click menu on Windows 11\n"
                "so 'Nab Audio' appears directly. Affects all apps.\n"
                "Requires sign-out or restart to take effect."
            ),
            font=ctk.CTkFont(size=11), text_color="gray45", justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # -- Appearance --
        self._section(scroll, "Appearance")
        appear_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        appear_frame.pack(fill="x", pady=(0, 4))

        self.appear_var = StringVar(value=self.config.get("appearance_mode"))
        ctk.CTkOptionMenu(
            appear_frame, variable=self.appear_var,
            values=["Dark", "Light", "System"],
            width=130, command=self._change_appearance
        ).pack(side="left")
        ctk.CTkLabel(
            appear_frame, text="App theme",
            font=ctk.CTkFont(size=11), text_color="gray50"
        ).pack(side="left", padx=14)

        # -- FFmpeg --
        self._section(scroll, "FFmpeg")
        if ffmpeg_path:
            ctk.CTkLabel(
                scroll, text=f"Installed:  {ffmpeg_path}",
                font=ctk.CTkFont(size=11), text_color=C_SUCCESS
            ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                scroll, text="Not found!  Run:  winget install Gyan.FFmpeg",
                font=ctk.CTkFont(size=11), text_color=C_ERROR
            ).pack(anchor="w")

        # -- About --
        self._section(scroll, "About")
        ctk.CTkLabel(
            scroll,
            text=f"{APP_NAME} v{APP_VERSION}\n{APP_TAGLINE}\n{APP_REPO}",
            font=ctk.CTkFont(size=11), text_color="gray45", justify="left"
        ).pack(anchor="w")

        # -- Save --
        ctk.CTkButton(
            scroll, text="Save & Close",
            height=42, corner_radius=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save
        ).pack(pady=(22, 10))

    def _section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(20, 8))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.custom_folder_var.set(folder)
            self.same_folder_var.set(False)

    def _change_appearance(self, mode):
        ctk.set_appearance_mode(mode)

    def _toggle_classic_menu(self):
        if self.classic_menu_var.get():
            if ContextMenuManager.enable_classic_menu():
                messagebox.showinfo(
                    "Classic Menu Enabled",
                    "Full right-click menu enabled!\n\n"
                    "Sign out and back in (or restart)\n"
                    "for the change to take effect."
                )
            else:
                self.classic_menu_var.set(False)
                messagebox.showerror("Failed", "Could not enable classic context menu.")
        else:
            if ContextMenuManager.disable_classic_menu():
                messagebox.showinfo(
                    "Classic Menu Disabled",
                    "Windows 11 compact menu restored.\n\n"
                    "Sign out and back in (or restart)\n"
                    "for the change to take effect."
                )
            else:
                self.classic_menu_var.set(True)
                messagebox.showerror("Failed", "Could not disable classic context menu.")

    def _install_ctx(self):
        if ContextMenuManager.install(self.app_dir):
            self.config.set("context_menu_installed", True)
            messagebox.showinfo(
                "Installed",
                '"Nab Audio" added to right-click menu!\n\n'
                "Right-click any video/audio file to use it."
            )
        else:
            messagebox.showinfo(
                "Admin Required",
                "An admin prompt will appear.\nClick 'Yes' to install."
            )

    def _uninstall_ctx(self):
        if messagebox.askyesno("Uninstall", 'Remove "Nab Audio" from right-click menu?'):
            if ContextMenuManager.uninstall():
                self.config.set("context_menu_installed", False)
                messagebox.showinfo("Uninstalled", "Context menu entries removed!")
            else:
                messagebox.showinfo(
                    "Admin Required",
                    "An admin prompt will appear.\nClick 'Yes' to uninstall."
                )

    def _browse_watch_folder(self):
        folder = filedialog.askdirectory(title="Select folder to watch")
        if folder:
            self.watch_folder_var.set(folder)

    def _toggle_watch(self):
        if not self.watcher:
            return
        if self.watch_enabled_var.get():
            folder = self.watch_folder_var.get()
            if folder and self.watcher.start(folder):
                self._watch_status.configure(text="Watching...", text_color=C_SUCCESS)
            else:
                self.watch_enabled_var.set(False)
                self._watch_status.configure(text="Not watching (invalid folder?)", text_color=C_ERROR)
        else:
            self.watcher.stop()
            self._watch_status.configure(text="Not watching", text_color="gray45")

    def _toggle_key_visibility(self):
        if self._dk_entry.cget("show") == "*":
            self._dk_entry.configure(show="")
        else:
            self._dk_entry.configure(show="*")

    def _save(self):
        self.config.set("output_format", self.format_var.get())
        self.config.set("bitrate", self.bitrate_var.get())
        self.config.set("output_postfix", self.postfix_var.get())
        self.config.set("output_same_folder", self.same_folder_var.get())
        self.config.set("custom_output_folder", self.custom_folder_var.get())
        self.config.set("watch_folder", self.watch_folder_var.get())
        self.config.set("watch_enabled", self.watch_enabled_var.get())
        self.config.set("deepgram_api_key", self.deepgram_key_var.get())
        self.config.set("auto_transcribe", self.auto_transcribe_var.get())
        self.config.set("appearance_mode", self.appear_var.get())
        self.top.destroy()
