"""Non-modal desktop alerts and a stoppable alarm; no browser/server needed."""

import sys
import threading
import tkinter as tk


class AlarmSound:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = None

    def start(self, repeat=True):
        self.stop()
        signal = threading.Event()
        self._stop = signal

        def play():
            if sys.platform != "win32":
                return
            import winsound
            while not signal.is_set():
                try:
                    winsound.Beep(1100, 220)
                    if signal.wait(.12):
                        break
                    winsound.Beep(750, 220)
                except RuntimeError:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                if not repeat or signal.wait(1.2):
                    break

        self._thread = threading.Thread(target=play, daemon=True, name="fall-alarm")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=.6)


class AlertNotifier:
    """All Tk calls happen on the caller's main thread. Audio runs separately."""
    def __init__(self, root=None, sound=True):
        self.root = root
        self.owns_root = root is None
        self.sound_enabled = sound
        self.sound = AlarmSound()
        self.window = None
        self.kind = None
        self._blink_id = None

    def show(self, kind, detail=""):
        priority = {"TEST": 0, "EARLY_WARNING": 1, "LYING_CHECK": 2, "FALL": 3}
        if self.window is not None and priority.get(self.kind, 0) > priority.get(kind, 0):
            return
        if self.window is not None and self.window.winfo_exists() and self.kind == kind:
            return
        self.acknowledge()
        self.kind = kind
        try:
            if self.root is None:
                self.root = tk.Tk()
                self.root.withdraw()
            window = self.window = tk.Toplevel(self.root)
            window.title("FallDetection — Thông báo")
            window.geometry("520x260")
            window.resizable(False, False)
            window.attributes("-topmost", True)
            fall = kind == "FALL"
            color = "#b91c1c" if fall else "#a16207" if kind in ("LYING_CHECK", "EARLY_WARNING") else "#1d4ed8"
            title = ("CẢNH BÁO SỚM: CHUYỂN ĐỘNG MẠNH" if kind == "EARLY_WARNING" else
                     "CẢNH BÁO TÉ NGÃ" if fall else "CẦN KIỂM TRA: NẰM KÉO DÀI"
                     if kind == "LYING_CHECK" else "THỬ ÂM THANH VÀ THÔNG BÁO")
            heading = tk.Label(window, text=title, bg=color, fg="white", font=("Segoe UI", 14, "bold"), pady=15)
            heading.pack(fill="x")
            def blink(lit=True):
                if self.window is window:
                    heading.configure(bg=color if lit else "#fff7ed", fg="white" if lit else color)
                    self._blink_id = window.after(400, blink, not lit)
            blink()
            tk.Label(window, text=detail, wraplength=470, justify="left",
                     font=("Segoe UI", 11), padx=20, pady=15).pack(fill="both", expand=True)
            tk.Button(window, text="Đã thấy — tắt chuông", command=self.acknowledge,
                      font=("Segoe UI", 11), padx=20, pady=6).pack(pady=(0, 15))
            window.protocol("WM_DELETE_WINDOW", self.acknowledge)
            window.lift()
            if self.sound_enabled and sys.platform != "win32":
                window.bell()
        except tk.TclError:
            # A terminal without a desktop can still receive the sound/console alert.
            self.window = None
        if self.sound_enabled:
            self.sound.start(repeat=True)

    def acknowledge(self):
        self.sound.stop()
        if self.window is not None:
            try:
                if self._blink_id is not None:
                    self.window.after_cancel(self._blink_id)
                self.window.destroy()
            except tk.TclError:
                pass
        self.window = None
        self._blink_id = None
        self.kind = None

    def tick(self):
        if self.owns_root and self.root is not None:
            try:
                self.root.update()
            except tk.TclError:
                self.root = None

    def close(self):
        self.acknowledge()
        if self.owns_root and self.root is not None:
            self.root.destroy()
            self.root = None
