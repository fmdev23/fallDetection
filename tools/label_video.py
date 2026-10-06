"""Small local interval annotator; no predicted label is accepted automatically."""
import hashlib
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'data'/'reviewed_intervals.json'
ACTIVITIES = ('walking', 'standing', 'sitting', 'bending', 'squatting',
              'lying_down_deliberately', 'falling', 'lying', 'uncertain')


def validate_interval(rows, digest, start, end, count, label, reviewer):
    if not reviewer.strip():
        raise ValueError('Điền tên/người rà soát nhãn trước khi lưu.')
    if label not in ACTIVITIES or not (0 <= start <= end < count):
        raise ValueError('Nhãn hoặc khoảng khung hình không hợp lệ.')
    if any(r['sha256'] == digest and start <= r['end_frame'] and end >= r['start_frame'] for r in rows):
        raise ValueError('Khoảng này chồng lên nhãn đã lưu. Hoàn tác nhãn gần nhất nếu cần sửa.')


class Annotator:
    def __init__(self, root):
        self.root, self.capture, self.playing = root, None, False
        self.timer = None
        self.path, self.digest, self.count, self.index, self.start = None, '', 0, 0, 0
        self.rows = json.loads(OUTPUT.read_text(encoding='utf-8')) if OUTPUT.exists() else []
        root.title('FallDetection — Rà soát nhãn video')
        root.geometry('900x750')
        self.reviewer = tk.StringVar()
        self.activity = tk.StringVar(value='uncertain')
        self.status = tk.StringVar(value='Mở video RGB hoặc clip cá nhân. Chưa xem rõ thì để uncertain.')
        bar = ttk.Frame(root, padding=8); bar.pack(fill='x')
        ttk.Button(bar, text='Mở video', command=self.open).pack(side='left')
        ttk.Button(bar, text='Phát / Dừng', command=self.toggle).pack(side='left', padx=8)
        ttk.Label(bar, text='Người rà soát:').pack(side='left')
        ttk.Entry(bar, textvariable=self.reviewer, width=24).pack(side='left', padx=8)
        self.image = ttk.Label(root, anchor='center'); self.image.pack(fill='both', expand=True)
        self.slider = tk.Scale(root, from_=0, to=0, orient='horizontal', command=self.seek)
        self.slider.pack(fill='x', padx=12)
        actions = ttk.Frame(root, padding=8); actions.pack(fill='x')
        ttk.Button(actions, text='Đánh dấu bắt đầu', command=self.mark).pack(side='left')
        ttk.Combobox(actions, textvariable=self.activity, values=ACTIVITIES, state='readonly', width=25).pack(side='left', padx=8)
        ttk.Button(actions, text='Kết thúc + lưu nhãn', command=self.save).pack(side='left')
        ttk.Button(actions, text='Hoàn tác nhãn cuối clip', command=self.undo).pack(side='left', padx=8)
        ttk.Label(root, textvariable=self.status, wraplength=860, padding=8).pack(fill='x')
        ttk.Label(root, text='← / →: từng frame · Nhãn áp dụng từ bắt đầu đến frame hiện tại (bao gồm hai đầu).\n'
                  'Không gán cả video là falling. Nằm yên = lying; chủ động hạ xuống = lying_down_deliberately.',
                  padding=8).pack(fill='x')
        root.bind('<Left>', lambda e: self.slider.set(max(0, self.index-1)))
        root.bind('<Right>', lambda e: self.slider.set(min(self.count-1, self.index+1)))
        root.protocol('WM_DELETE_WINDOW', self.close)

    def open(self):
        import cv2
        path = filedialog.askopenfilename(initialdir=ROOT/'data'/'urfall'/'rgb',
                                         filetypes=[('Video', '*.mp4 *.avi *.mov *.mkv')])
        if not path:
            return
        self.playing = False
        if self.capture is not None:
            self.capture.release()
        self.capture = cv2.VideoCapture(path)
        self.count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        if not self.capture.isOpened() or self.count < 1 or self.fps <= 0:
            messagebox.showerror('Không mở được', 'Video không đọc được.'); return
        self.path = Path(path).resolve()
        with self.path.open('rb') as source:
            self.digest = hashlib.file_digest(source, 'sha256').hexdigest()
        self.start = 0
        self.slider.configure(to=self.count-1)
        self.slider.set(0)
        self.seek(0)

    def seek(self, value):
        import cv2
        from PIL import Image, ImageTk
        if self.capture is None or self.path is None:
            return
        self.index = int(float(value))
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.index)
        ok, frame = self.capture.read()
        if not ok:
            self.playing = False
            return
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img.thumbnail((860, 500))
        self.photo = ImageTk.PhotoImage(img)
        self.image.configure(image=self.photo)
        self.status.set(f'{self.path.name} · frame {self.index}/{self.count-1} · {self.index/self.fps:.2f}s · '
                        f'bắt đầu: {self.start} · đã lưu {sum(r["sha256"] == self.digest for r in self.rows)} đoạn')

    def toggle(self):
        self.playing = not self.playing
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        if self.playing:
            self.tick()

    def tick(self):
        self.timer = None
        if not self.playing or self.capture is None:
            return
        if self.index >= self.count-1:
            self.playing = False; return
        self.slider.set(self.index+1)
        self.timer = self.root.after(max(10, round(1000/self.fps)), self.tick)

    def mark(self):
        self.start = self.index
        self.status.set(f'Bắt đầu tại frame {self.start}. Chuyển tới cuối hành động, chọn nhãn rồi lưu.')

    def persist(self):
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temp = OUTPUT.with_suffix('.tmp')
        temp.write_text(json.dumps(self.rows, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(OUTPUT)

    def save(self):
        if self.path is None:
            return
        self.playing = False
        try:
            validate_interval(self.rows, self.digest, self.start, self.index, self.count,
                              self.activity.get(), self.reviewer.get())
            self.rows.append(dict(video=str(self.path), sha256=self.digest,
                                  start_frame=self.start, end_frame=self.index, fps=self.fps,
                                  label=self.activity.get(), reviewer=self.reviewer.get().strip(),
                                  origin='manual_video_review', frame_index_base=0))
            self.persist()
            self.status.set(f'Đã lưu: {self.start}–{self.index}, {self.activity.get()}. {OUTPUT.name}')
        except (ValueError, OSError) as exc:
            messagebox.showerror('Chưa lưu được', str(exc))

    def undo(self):
        for i in range(len(self.rows)-1, -1, -1):
            if self.rows[i]['sha256'] == self.digest:
                removed = self.rows.pop(i)
                self.persist()
                self.status.set(f'Đã bỏ nhãn {removed["start_frame"]}–{removed["end_frame"]}.')
                break

    def close(self):
        self.playing = False
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        if self.capture is not None:
            self.capture.release()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    Annotator(root)
    root.mainloop()
