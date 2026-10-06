"""Small Tkinter application sharing the console detection engine."""

from datetime import datetime
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

if __package__:
    from .alerts import AlertNotifier
    from .main import build_parser, monitor_frames, validate_args
else:
    from alerts import AlertNotifier
    from main import build_parser, monitor_frames, validate_args

PROJECT = Path(__file__).resolve().parents[1]
POSE_REASONS = {
    "person not detected or occluded": "Chưa nhận ra người hoặc người bị che khuất.",
    "missing keypoints": "Chưa thấy rõ vai và hông.",
    "need exactly one person": "Cần đúng một người rõ trong khung hình.",
    "vertical torso": "Thân người đang thẳng.",
    "horizontal torso and leg": "Thân và chân nằm ngang.",
    "ambiguous pose or hidden legs": "Góc thân chưa rõ hoặc chân bị che.",
}


class FallDetectionApp:
    def __init__(self, root, initial=None):
        self.root = root
        self.initial = initial or build_parser().parse_args([])
        self.worker = None
        self.stop_event = threading.Event()
        self.frames = queue.Queue(maxsize=1)
        self.events = queue.SimpleQueue()
        self.notifier = AlertNotifier(root)
        self.closing = False
        self.stopping = False
        self.run_error = None
        self.frame_count = 0
        self.alert_count = 0
        self.last_update = None
        self.live_sensor = None
        self.sensor_frames = queue.Queue(maxsize=1)
        self.log_path = None
        self._photo = None
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", lambda event: self.stop())
        self._poll_id = self.root.after(40, self._poll)

    def _build(self):
        r = self.root
        r.title("FallDetection — Camera & Sensor")
        width, height = min(1180, r.winfo_screenwidth()-60), min(850, r.winfo_screenheight()-80)
        r.geometry(f"{width}x{height}")
        r.minsize(1050, min(780, r.winfo_screenheight()-80))
        r.configure(bg="#edf2f7")
        style = ttk.Style(r)
        style.theme_use("clam")
        style.configure("TFrame", background="#edf2f7")
        style.configure("TLabel", background="#edf2f7", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 6))
        style.configure("Start.TButton", background="#166534", foreground="white")
        style.configure("Confirm.Horizontal.TProgressbar", background="#2563eb", troughcolor="#dbeafe")

        header = tk.Frame(r, bg="#14243b", padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="FallDetection", font=("Segoe UI", 22, "bold"),
                 bg="#14243b", fg="white").pack(anchor="w")
        tk.Label(header, text="Camera nhìn tư thế · Sensor xác nhận chuyển động · Cảnh báo có âm thanh",
                 font=("Segoe UI", 10), bg="#14243b", fg="#c7d5e5").pack(anchor="w")

        controls = ttk.Frame(r, padding=(16, 10))
        controls.pack(fill="x")
        self.source = tk.StringVar(value="Video" if self.initial.source == "video" else "Webcam")
        self.path = tk.StringVar(value=self.initial.path or "")
        self.camera = tk.StringVar(value=str(self.initial.camera))
        self.port = tk.StringVar(value=self.initial.port)
        self.video_live_sensor = tk.BooleanVar(value=self.initial.video_live_sensor)
        self.sound = tk.BooleanVar(value=not self.initial.no_alerts)
        self.notifier.sound_enabled = self.sound.get()
        self.source_box = ttk.Combobox(controls, textvariable=self.source,
                                      values=("Webcam", "Video"), state="readonly", width=9)
        self.source_box.grid(row=0, column=0, padx=(0, 8))
        self.path_entry = ttk.Entry(controls, textvariable=self.path, width=36)
        self.path_entry.grid(row=0, column=1, sticky="ew")
        self.browse_button = ttk.Button(controls, text="Chọn video…", command=self.browse)
        self.browse_button.grid(row=0, column=2, padx=6)
        self.start_button = ttk.Button(controls, text="Bắt đầu", style="Start.TButton", command=self.start)
        self.start_button.grid(row=0, column=3, padx=6)
        self.stop_button = ttk.Button(controls, text="Dừng", command=self.stop, state="disabled")
        self.stop_button.grid(row=0, column=4, padx=6)
        ttk.Button(controls, text="Thử chuông", command=self.test_alarm).grid(row=0, column=5, padx=6)
        ttk.Checkbutton(controls, text="Âm thanh", variable=self.sound,
                        command=self.change_sound).grid(row=0, column=6)
        self.sensor_mode = ttk.Checkbutton(controls, text="Ghép Wokwi trực tiếp vào video (chỉ demo đồng bộ)",
                                           variable=self.video_live_sensor)
        self.sensor_mode.grid(row=1, column=0, columnspan=5, sticky="w", pady=(6, 0))
        controls.columnconfigure(1, weight=1)
        self.source_box.bind("<<ComboboxSelected>>", lambda event: self.source_changed())

        settings = ttk.Frame(r, padding=(16, 0, 16, 8))
        settings.pack(fill="x")
        self.settings_widgets = []
        self.values = {}
        for col, (label, name) in enumerate((("Gia tốc (g)", "accel_threshold"),
                ("Gyro (°/s)", "gyro_threshold"), ("Giữ nằm (s)", "lying_hold"),
                ("Cửa sổ impact (s)", "impact_window"), ("Nhắc nằm lâu (s)", "lying_warning"))):
            box = ttk.Frame(settings)
            box.grid(row=0, column=col, padx=(0, 14), sticky="w")
            ttk.Label(box, text=label).pack(anchor="w")
            value = self.values[name] = tk.StringVar(value=str(getattr(self.initial, name)))
            entry = ttk.Entry(box, textvariable=value, width=11)
            entry.pack(anchor="w")
            self.settings_widgets.append(entry)
        sensor_box = ttk.Frame(settings)
        sensor_box.grid(row=0, column=5, sticky="ew")
        ttk.Label(sensor_box, text="Cổng sensor").pack(anchor="w")
        port_entry = ttk.Entry(sensor_box, textvariable=self.port, width=29)
        port_entry.pack(fill="x")
        self.settings_widgets.append(port_entry)
        camera_box = ttk.Frame(settings)
        camera_box.grid(row=0, column=6, padx=(10, 0))
        ttk.Label(camera_box, text="Camera").pack(anchor="w")
        camera_entry = ttk.Entry(camera_box, textvariable=self.camera, width=4)
        camera_entry.pack()
        self.settings_widgets.append(camera_entry)
        settings.columnconfigure(5, weight=1)

        content = ttk.Frame(r, padding=(16, 0))
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=0, minsize=325)
        content.rowconfigure(0, weight=1)
        self.video = tk.Canvas(content, bg="#0b1220", highlightthickness=0, width=640, height=420)
        self.video.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.video.create_text(320, 200, text="Chọn nguồn hình rồi bấm Bắt đầu\nKhông cần té thật để thử",
                               fill="#cbd5e1", font=("Segoe UI", 15), justify="center", tags="placeholder")
        card = tk.Frame(content, bg="white", padx=16, pady=10, width=325)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_propagate(False)
        self.banner = tk.Label(card, text="SẴN SÀNG", font=("Segoe UI", 17, "bold"),
                               bg="#e2e8f0", fg="#334155", pady=9, wraplength=285)
        self.banner.pack(fill="x", pady=(0, 12))
        self.pose_text = tk.StringVar(value="Tư thế: —")
        self.pose_detail = tk.StringVar(value="Để camera thấy rõ vai, hông và chân.")
        self.sensor_text = tk.StringVar(value="Sensor: chưa kết nối")
        self.sensor_values = tk.StringVar(value="Gia tốc: — g   |   Gyro: — °/s")
        self.impact_text = tk.StringVar(value="Impact: chưa có")
        self.progress_text = tk.StringVar(value="Xác nhận nằm: 0%")
        self.reason = tk.StringVar(value="Mở Wokwi trước khi thử kết hợp sensor.\n\nNằm kéo dài chưa đủ bằng chứng té vẫn có thông báo cần kiểm tra.")
        self.clock_text = tk.StringVar(value="")
        for variable, bold in ((self.pose_text, True), (self.pose_detail, False),
                               (self.sensor_text, True), (self.sensor_values, False),
                               (self.impact_text, False), (self.progress_text, True)):
            tk.Label(card, textvariable=variable, bg="white", fg="#1e293b",
                     font=("Segoe UI", 10, "bold" if bold else "normal"),
                     wraplength=285, justify="left", anchor="w").pack(fill="x", pady=(0, 5))
        self.progress = ttk.Progressbar(card, maximum=100, style="Confirm.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 12))
        tk.Label(card, textvariable=self.reason, bg="#eff6ff", fg="#1e3a8a", padx=8, pady=8,
                 font=("Segoe UI", 10), justify="left", wraplength=270).pack(fill="x")
        tk.Label(card, textvariable=self.clock_text, bg="white", fg="#64748b",
                 font=("Segoe UI", 10), pady=6).pack(anchor="w")

        footer = ttk.Frame(r, padding=(16, 8, 16, 12))
        footer.pack(fill="x")
        self.history = tk.Text(footer, height=4, wrap="word", state="disabled", bg="white",
                               fg="#334155", relief="flat", font=("Segoe UI", 9))
        self.history.pack(fill="x")
        self.status = tk.StringVar(value="Prototype học thuật · Nguồn sensor đang giả lập · Một người trong khung hình")
        ttk.Label(footer, textvariable=self.status).pack(anchor="w", pady=(6, 0))
        self.source_changed()

    def source_changed(self):
        enabled = self.source.get() == "Video"
        self.sensor_mode.configure(state="normal" if enabled else "disabled")
        self.path_entry.configure(state="normal" if enabled else "disabled")
        self.browse_button.configure(state="normal" if enabled else "disabled")

    def browse(self):
        path = filedialog.askopenfilename(parent=self.root, initialdir=PROJECT / "test_videos",
                    filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv"), ("Tất cả", "*.*")])
        if path:
            self.path.set(path)

    def change_sound(self):
        self.notifier.sound_enabled = self.sound.get()
        if not self.sound.get():
            self.notifier.sound.stop()

    def test_alarm(self):
        self.notifier.show("TEST", "Đây chỉ là thử loa và cửa sổ thông báo, không phải sự kiện té ngã. Bấm nút bên dưới để tắt chuông.")

    def _append(self, text):
        self.history.configure(state="normal")
        self.history.insert("end", f"{datetime.now():%H:%M:%S}  {text}\n")
        if int(self.history.index("end-1c").split(".")[0]) > 120:
            self.history.delete("1.0", "20.0")
        self.history.see("end")
        self.history.configure(state="disabled")

    def start(self):
        if self.worker is not None and self.worker.is_alive():
            return
        try:
            args = build_parser().parse_args([])
            args.source = "video" if self.source.get() == "Video" else "webcam"
            args.video_live_sensor = self.video_live_sensor.get()
            args.path, args.port = self.path.get().strip(), self.port.get().strip()
            args.camera = int(self.camera.get())
            args.duration = self.initial.duration
            args.recovery_hold = self.initial.recovery_hold
            args.occlusion_grace = self.initial.occlusion_grace
            for name, value in self.values.items():
                setattr(args, name, float(value.get()))
            validate_args(args)
            if args.source == "video" and not Path(args.path).is_file():
                raise ValueError("Hãy chọn một file video có thật.")
            if not args.port and (args.source != "video" or args.video_live_sensor):
                raise ValueError("Chưa có cổng sensor.")
        except ValueError as exc:
            messagebox.showerror("Thông số chưa hợp lệ", str(exc), parent=self.root)
            return
        self.notifier.acknowledge()
        self.stop_event = threading.Event()
        self.frames = queue.Queue(maxsize=1)
        self.events = queue.SimpleQueue()
        self.frame_count = 0
        self.alert_count = 0
        self.stopping = False
        self.run_error = None
        self.last_update = None
        self.live_sensor = None
        self.sensor_frames = queue.Queue(maxsize=1)
        self.log_path = PROJECT / "results" / f"gui_{datetime.now():%Y%m%d_%H%M%S_%f}.csv"
        args.log = self.log_path
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.source_box.configure(state="disabled")
        self.sensor_mode.configure(state="disabled")
        self.path_entry.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        for entry in self.settings_widgets:
            entry.configure(state="disabled")
        self.status.set("Đang mở nguồn hình và tải model… Giao diện vẫn có thể nhận thao tác Dừng.")
        self.banner.configure(text="ĐANG KHỞI ĐỘNG", bg="#dbeafe", fg="#1e40af")
        self.progress["value"] = 0
        self._append(f"Bắt đầu {args.source}; log: {self.log_path.name}")
        self.worker = threading.Thread(target=self._run, args=(args,), daemon=True, name="vision-worker")
        self.worker.start()

    def _on_sensor(self, sample):
        # Called by the reader, never touches Tk; alarm edges cannot be dropped.
        if sample.risk_event:
            self.events.put(("alert", ("EARLY_WARNING", sample.risk_reason)))
        try:
            self.sensor_frames.get_nowait()
        except queue.Empty:
            pass
        self.sensor_frames.put_nowait(sample)

    def _live_status(self):
        try:
            self.live_sensor = self.sensor_frames.get_nowait()
        except queue.Empty:
            pass
        sensor = self.live_sensor
        running = self.worker is not None and self.worker.is_alive() and not self.stopping
        fresh = sensor is not None and sensor.timestamp is not None and time.monotonic()-sensor.timestamp <= .75
        if running and sensor is not None:
            self.sensor_text.set(f"Sensor: {sensor.status if fresh else 'SENSOR_DISCONNECTED'}")
            if fresh:
                self.sensor_values.set(f"Gia tốc: {sensor.accel_total:.2f} g | Gyro: {sensor.gyro_total:.1f} °/s")
            else:
                self.sensor_values.set("Sensor mất dữ liệu mới — không dùng mẫu cũ")
        if self.run_error or not running:
            return
        final = self.last_update.final if self.last_update is not None else None
        fall = final is not None and final.status == "FALL_DETECTED"
        lying = final is not None and final.lying_seconds >= float(self.values['lying_warning'].get())
        camera_risk = (self.last_update is not None and self.last_update.motion_active
                       and time.monotonic()-self.last_update.produced_at < 1)
        early = (fresh and sensor.risk_active) or camera_risk
        if fall or lying or early:
            lit = int(time.monotonic()/0.4) % 2 == 0
            color = "#b91c1c" if fall else "#c2410c"
            title = "CẢNH BÁO TÉ NGÃ" if fall else "CẦN KIỂM TRA: ĐANG NẰM" if lying else "CẢNH BÁO SỚM\nCHUYỂN ĐỘNG MẠNH"
            self.banner.configure(text=title, bg=color if lit else "#fff7ed", fg="white" if lit else color)
            self.video.configure(highlightthickness=5, highlightbackground=color if lit else "#fed7aa")
            if early and not fall and not lying:
                self.reason.set(self.last_update.motion_reason if camera_risk else sensor.risk_reason)
        else:
            self.video.configure(highlightthickness=0)
            if final is not None:
                bg, fg = ("#dcfce7", "#166534") if final.status == "NORMAL" else ("#fef3c7", "#92400e")
                self.banner.configure(text=final.status, bg=bg, fg=fg)
                self.reason.set(final.reason)
        if self.last_update is not None and self.last_update.produced_at:
            age = time.monotonic()-self.last_update.produced_at
            if age > 1:
                self.clock_text.set(f"Ảnh chưa cập nhật {age:.1f}s" + (" · Sensor theo dõi riêng" if sensor is not None else ""))

    def _run(self, args):
        previous = None
        try:
            for update in monitor_frames(args, self.stop_event, self._on_sensor):
                self.frame_count += 1
                if update.motion_event:
                    self.events.put(("alert", ("EARLY_WARNING", update.motion_reason)))
                # Alarms have a separate queue: dropping old video frames never drops an alarm.
                if update.final.alert or update.final.warning:
                    kind = "FALL" if update.final.alert else "LYING_CHECK"
                    self.events.put(("alert", (kind, update.final.reason)))
                state = (update.final.status, update.sensor.status == "SENSOR_DISCONNECTED")
                if state != previous:
                    self.events.put(("state", f"{update.final.status}: {update.final.reason}"))
                    previous = state
                try:
                    self.frames.put_nowait(update)
                except queue.Full:
                    try:
                        self.frames.get_nowait()
                    except queue.Empty:
                        pass
                    self.frames.put_nowait(update)
        except Exception as exc:
            self.events.put(("error", f"{type(exc).__name__}: {exc}"))
        finally:
            self.events.put(("finished", self.frame_count))

    def _render(self, update):
        self.last_update = update
        final, sensor, posture = update.final, update.sensor, update.posture
        colors = {"NORMAL": ("#dcfce7", "#166534", "BÌNH THƯỜNG"),
                  "SUSPICIOUS": ("#fef3c7", "#92400e", "ĐANG NGHI NGỜ"),
                  "FALL_DETECTED": ("#b91c1c", "white", "CẢNH BÁO TÉ NGÃ")}
        bg, fg, title = colors[final.status]
        self.banner.configure(text=f"{title}\n{final.status}", bg=bg, fg=fg)
        self.pose_text.set(f"Tư thế: {posture.status}")
        self.pose_detail.set(POSE_REASONS.get(posture.reason, posture.reason))
        self.sensor_text.set("Video độc lập — không ghép IMU" if sensor.status == "VIDEO_ONLY" else f"Sensor: {sensor.status}")
        accel = "—" if sensor.accel_total is None else f"{sensor.accel_total:.2f}"
        gyro = "—" if sensor.gyro_total is None else f"{sensor.gyro_total:.1f}"
        self.sensor_values.set(f"Gia tốc: {accel} g   |   Gyro: {gyro} °/s")
        self.impact_text.set("Impact: chưa có" if final.impact_age is None else
                             f"Impact gần nhất: {final.impact_age:.1f} giây trước")
        self.progress_text.set(f"Xác nhận: {final.progress:.0%} · Nằm rõ: {final.lying_seconds:.1f}s")
        self.progress["value"] = final.progress * 100
        self.reason.set(final.reason)
        self.clock_text.set("Webcam trực tiếp" if update.video_seconds is None else
                            f"Video: {update.video_seconds:.1f} giây · {'Phân tích đủ frame' if sensor.status == 'VIDEO_ONLY' else 'Sensor trực tiếp'}")
        self.clock_text.set(self.clock_text.get() + f"\nXử lý ảnh: {update.inference_ms:.0f} ms")
        image = Image.fromarray(update.frame[:, :, ::-1])
        image.thumbnail((max(1, self.video.winfo_width()), max(1, self.video.winfo_height())))
        self._photo = ImageTk.PhotoImage(image, master=self.root)
        self.video.delete("all")
        self.video.create_image(self.video.winfo_width()/2, self.video.winfo_height()/2,
                                image=self._photo, anchor="center")

    def _poll(self):
        while not self.events.empty():
            kind, value = self.events.get()
            if kind == "alert":
                self.alert_count += 1
                self._append(f"THÔNG BÁO {value[0]}: {value[1]}")
                if not self.stopping and not self.closing and not self.initial.no_alerts:
                    self.notifier.show(*value)
            elif kind == "state":
                self._append(value)
                self.status.set("Đang theo dõi. Thông báo sẽ bật lên khi có cảnh báo.")
            elif kind == "error":
                self.run_error = value
                self._append(f"LỖI: {value}")
                self.reason.set(value)
                self.banner.configure(text="KHÔNG CHẠY ĐƯỢC", bg="#fee2e2", fg="#991b1b")
            elif kind == "finished":
                self.video.configure(highlightthickness=0)
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.source_box.configure(state="readonly")
                for entry in self.settings_widgets:
                    entry.configure(state="normal")
                self.source_changed()
                self.status.set(f"Đã dừng / hết video · {value} khung hình · {self.alert_count} cảnh báo · Log: {self.log_path.name}")
                self._append(f"Đã giải phóng camera và sensor; xử lý {value} khung hình.")
        try:
            update = self.frames.get_nowait()
        except queue.Empty:
            pass
        else:
            if not self.stopping and self.run_error is None:
                self._render(update)
        self._live_status()
        if self.closing and (self.worker is None or not self.worker.is_alive()):
            self.notifier.close()
            self.root.destroy()
            return
        self._poll_id = self.root.after(40, self._poll)

    def stop(self):
        self.stopping = True
        self.video.configure(highlightthickness=0)
        self.stop_event.set()
        self.notifier.acknowledge()
        if self.worker is not None and self.worker.is_alive():
            self.status.set("Đang dừng và giải phóng camera/sensor…")
        self.stop_button.configure(state="disabled")

    def close(self):
        self.closing = True
        self.stop()


def main():
    parser = build_parser()
    parser.description = __doc__
    parser.add_argument("--auto-start", action="store_true")
    args = parser.parse_args()
    if args.source == "image":
        parser.error("Ảnh tĩnh dùng main.py --source image; GUI theo dõi webcam/video.")
    root = tk.Tk()
    app = FallDetectionApp(root, args)
    if args.auto_start:
        root.after(200, app.start)
    root.mainloop()


if __name__ == "__main__":
    main()
