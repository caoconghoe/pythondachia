import tkinter as tk
from tkinter import ttk, messagebox

from config import APP_TITLE
from services import db
from services.face import ensure_face_lib
from ui.attendance_tab import AttendanceTab
from ui.employee_tab import EmployeeTab
from ui.report_tab import ReportTab


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # ======= CẤU HÌNH CƠ BẢN =======
        self.title(APP_TITLE)
        self.geometry("980x680")
        self.resizable(True, True)
        self.configure(bg="#e8f0fe")  # 🌿 màu nền tổng thể (xanh nhạt pastel)

        # ======= STYLE TOÀN CỤC =======
        style = ttk.Style(self)
        style.theme_use("clam")  # dùng theme “clam” để có màu sắc

        # Tab style
        style.configure("TNotebook", background="#dbeafe", borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background="#bfdbfe", 
                        foreground="#0f172a", 
                        padding=[10, 5], 
                        font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#60a5fa")],
                  foreground=[("selected", "white")])

        # Button style
        style.configure("TButton",
                        font=("Segoe UI", 10, "bold"),
                        background="#3b82f6",
                        foreground="white",
                        padding=6)
        style.map("TButton",
                  background=[("active", "#2563eb"), ("disabled", "#a5b4fc")])

        # Frame style
        style.configure("TFrame", background="#e8f0fe")
        style.configure("TLabelframe", background="#e8f0fe", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background="#e8f0fe")

        # Label style
        style.configure("TLabel", background="#e8f0fe", font=("Segoe UI", 10))

        # ======= KHỞI TẠO DATABASE VÀ KIỂM TRA THƯ VIỆN =======
        try:
            ensure_face_lib()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được face_recognition: {e}")
            self.destroy()
            return

        db.init_db()

        # ======= GIAO DIỆN CHÍNH VỚI 3 TAB =======
        nb = ttk.Notebook(self)
        self.tab_att = AttendanceTab(nb)
        self.tab_emp = EmployeeTab(nb)
        self.tab_rep = ReportTab(nb)

        nb.add(self.tab_att, text="📸 Chấm công")
        nb.add(self.tab_emp, text="👥 Nhân viên")
        nb.add(self.tab_rep, text="📊 Báo cáo")
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # Sự kiện khi đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Giải phóng tài nguyên khi tắt ứng dụng"""
        try:
            self.tab_att.on_close()
        except Exception:
            pass
        self.destroy()


def main():
    app = App()
    if app.winfo_exists():
        app.mainloop()


if __name__ == "__main__":
    main()
