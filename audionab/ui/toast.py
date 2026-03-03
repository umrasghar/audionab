"""Toast notification widget for non-blocking messages."""

import logging

try:
    import customtkinter as ctk
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Toast colors by level
TOAST_COLORS = {
    "success": {"bg": "#065f46", "text": "#a7f3d0", "border": "#2dd4bf"},
    "error": {"bg": "#7f1d1d", "text": "#fca5a5", "border": "#f87171"},
    "warning": {"bg": "#78350f", "text": "#fde68a", "border": "#fbbf24"},
    "info": {"bg": "#1e3a5f", "text": "#bfdbfe", "border": "#7aa2f7"},
}


class ToastManager:
    """Manages toast notifications that appear at the bottom of the window."""

    def __init__(self, root):
        self.root = root
        self._current_toast = None
        self._dismiss_id = None

    def show(self, message, level="info", duration=4000):
        """Show a toast notification.

        Args:
            message: Text to display
            level: One of 'success', 'error', 'warning', 'info'
            duration: Auto-dismiss after this many milliseconds (0 = stay)
        """
        self.dismiss()

        colors = TOAST_COLORS.get(level, TOAST_COLORS["info"])

        toast = ctk.CTkFrame(
            self.root,
            fg_color=colors["bg"],
            corner_radius=10,
            border_width=1,
            border_color=colors["border"]
        )

        label = ctk.CTkLabel(
            toast, text=message,
            font=ctk.CTkFont(size=12),
            text_color=colors["text"],
            wraplength=600
        )
        label.pack(padx=16, pady=10, side="left", fill="x", expand=True)

        close_btn = ctk.CTkButton(
            toast, text="x", width=28, height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text"],
            font=ctk.CTkFont(size=12),
            command=self.dismiss
        )
        close_btn.pack(side="right", padx=(0, 8), pady=6)

        toast.place(relx=0.5, rely=1.0, anchor="s", y=-16)
        self._current_toast = toast

        if duration > 0:
            self._dismiss_id = self.root.after(duration, self.dismiss)

    def dismiss(self):
        """Dismiss the current toast."""
        if self._dismiss_id is not None:
            self.root.after_cancel(self._dismiss_id)
            self._dismiss_id = None
        if self._current_toast is not None:
            try:
                self._current_toast.destroy()
            except Exception:
                pass
            self._current_toast = None
