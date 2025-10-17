import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from config import DEFAULT_TOL
from services import db
from services.face import face_encode_from_image, match_employee

try:
    import cv2
except Exception:
    cv2 = None


class AttendanceTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # Controls
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Ngưỡng nhận diện (nhỏ = chặt):").pack(side="left")
        self.scale_tol = ttk.Scale(top, from_=0.30, to=0.70, value=DEFAULT_TOL,
                                   orient="horizontal", length=200)
        self.scale_tol.pack(side="left", padx=6)

        ttk.Button(top, text="Bật camera", command=self.start_camera).pack(side="left", padx=4)
        ttk.Button(top, text="Tắt camera", command=self.stop_camera).pack(side="left", padx=4)
        ttk.Button(top, text="Chấm công (chụp)", command=self.scan_and_mark).pack(side="left", padx=4)

        self.video_panel = ttk.Label(self, relief="sunken", anchor="center")
        self.video_panel.pack(fill="both", expand=True, padx=10, pady=10)

        self.att_status = tk.StringVar(value="Chưa có thao tác.")
        ttk.Label(self, textvariable=self.att_status).pack(pady=6)

        # Webcam state
        self.cap = None
        self._video_loop = False
        self._frame_imgtk = None

    # ---------- Camera ----------
    def start_camera(self):
        if cv2 is None:
            messagebox.showerror("Lỗi", "OpenCV (cv2) chưa được cài đặt.")
            return
        if self.cap is not None:
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = None
            messagebox.showerror("Lỗi", "Không mở được webcam.")
            return
        self._video_loop = True
        threading.Thread(target=self._update_video, daemon=True).start()
        self.att_status.set("Camera đã bật.")

    def stop_camera(self):
        self._video_loop = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.video_panel.config(image="", text="")
        self.att_status.set("Camera đã tắt.")

    def _update_video(self):
        while self._video_loop and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                continue
            rgb = frame[:, :, ::-1]  # BGR -> RGB
            img = Image.fromarray(rgb).resize((900, 520))
            imgtk = ImageTk.PhotoImage(image=img)
            self._frame_imgtk = imgtk  # keep reference
            self.video_panel.config(image=imgtk)

    def scan_and_mark(self):
        tol = float(self.scale_tol.get())
        if self.cap is None:
            messagebox.showwarning("Chú ý", "Hãy bật camera trước.")
            return
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Lỗi", "Không đọc được frame từ camera.")
            return
        img = Image.fromarray(frame[:, :, ::-1])  # to RGB
        try:
            enc = face_encode_from_image(img)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý ảnh: {e}")
            return
        if enc is None:
            self.att_status.set("Không phát hiện được khuôn mặt. Thử lại.")
            return
        m = match_employee(enc, tol)
        if m is None:
            self.att_status.set("❌ Không khớp với nhân viên nào (Unknown). Vào tab Nhân viên để thêm.")
        else:
            db.mark_attendance(int(m["id"]))
            self.att_status.set(f"✅ Đã chấm công cho {m['name']} (khoảng cách={m['distance']:.3f}).")

    # ---------- Lifecycle ----------
    def on_close(self):
        self._video_loop = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
