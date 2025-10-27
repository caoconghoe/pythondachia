
# import tkinter as tk
# from tkinter import ttk, messagebox

# from config import APP_TITLE
# from services import db
# from services.face import ensure_face_lib
# from ui.attendance_tab import AttendanceTab
# from ui.employee_tab import EmployeeTab
# from ui.report_tab import ReportTab


# class App(tk.Tk):
#     def __init__(self):
#         super().__init__()

#         # ======= CẤU HÌNH CƠ BẢN =======
#         self.title(APP_TITLE)
#         self.geometry("980x680")
#         self.resizable(True, True)
#         self.configure(bg="#e8f0fe")  # 🌿 màu nền tổng thể (xanh nhạt pastel)

#         # ======= STYLE TOÀN CỤC =======
#         style = ttk.Style(self)
#         style.theme_use("clam")  # dùng theme “clam” để có màu sắc

#         # Tab style
#         style.configure("TNotebook", background="#dbeafe", borderwidth=2)
#         style.configure("TNotebook.Tab", 
#                         background="#bfdbfe", 
#                         foreground="#0f172a", 
#                         padding=[10, 5], 
#                         font=("Segoe UI", 10, "bold"))
#         style.map("TNotebook.Tab",
#                   background=[("selected", "#60a5fa")],
#                   foreground=[("selected", "black")])

#         # Button style
#         style.configure("TButton",
#                         font=("Segoe UI", 10, "bold"),
#                         background="#3b82f6",
#                         foreground="white",
#                         padding=6)
#         style.map("TButton",
#                   background=[("active", "#2563eb"), ("disabled", "#db1919")])

#         # Frame style
#         style.configure("TFrame", background="#e8f0fe")
#         style.configure("TLabelframe", background="#e8f0fe", font=("Segoe UI", 10, "bold"))
#         style.configure("TLabelframe.Label", background="#e8f0fe")

#         # Label style
#         style.configure("TLabel", background="#e8f0fe", font=("Segoe UI", 10))

#         # ======= KHỞI TẠO DATABASE VÀ KIỂM TRA THƯ VIỆN =======
#         try:
#             ensure_face_lib()
#         except Exception as e:
#             messagebox.showerror("Lỗi", f"Không tải được face_recognition: {e}")
#             self.destroy()
#             return

#         db.init_db()

#         # ======= GIAO DIỆN CHÍNH VỚI 3 TAB =======
#         nb = ttk.Notebook(self)
#         self.tab_att = AttendanceTab(nb)
#         self.tab_emp = EmployeeTab(nb)
#         self.tab_rep = ReportTab(nb)

#         nb.add(self.tab_att, text="📸 Chấm công")
#         nb.add(self.tab_emp, text="👥 Nhân viên")
#         nb.add(self.tab_rep, text="📊 Báo cáo")
#         nb.pack(fill="both", expand=True, padx=8, pady=8)

#         # Sự kiện khi đóng cửa sổ
#         self.protocol("WM_DELETE_WINDOW", self.on_close)

#     def on_close(self):
#         """Giải phóng tài nguyên khi tắt ứng dụng"""
#         try:
#             self.tab_att.on_close()
#         except Exception:
#             pass
#         self.destroy()


# def main():
#     app = App()
#     if app.winfo_exists():
#         app.mainloop()


# if __name__ == "__main__":
#     main()
import tkinter as tk
from tkinter import ttk, messagebox

from config import APP_TITLE
from services import db
from services.face import ensure_face_lib
from ui.attendance_tab import AttendanceTab
from ui.employee_tab import EmployeeTab
from ui.report_tab import ReportTab
from ui.login_window import LoginWindow   # cần file ui/login_window.py có class LoginWindow

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # ===== Khởi tạo DB trước (để có bảng users, v.v.) =====
        try:
            db.init_db()
        except Exception as e:
            messagebox.showerror("DB", f"Không khởi tạo được CSDL: {e}")
            self.destroy()
            return

        # ===== Kiểm tra thư viện nhận diện =====
        try:
            ensure_face_lib()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được face_recognition: {e}")
            self.destroy()
            return

        # ===== Cấu hình cơ bản & style =====
        self.title(APP_TITLE)
        self.geometry("980x680")
        self.resizable(True, True)
        self.configure(bg="#e8f0fe")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#dbeafe", borderwidth=2)
        style.configure("TNotebook.Tab",
                        background="#bfdbfe", foreground="#0f172a",
                        padding=[10, 5], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#60a5fa")],
                  foreground=[("selected", "black")])
        style.configure("TButton", font=("Segoe UI", 10, "bold"),
                        background="#3b82f6", foreground="white", padding=6)
        style.map("TButton",
                  background=[("active", "#2563eb"), ("disabled", "#db1919")])
        style.configure("TFrame", background="#e8f0fe")
        style.configure("TLabelframe", background="#e8f0fe", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background="#e8f0fe")
        style.configure("TLabel", background="#e8f0fe", font=("Segoe UI", 10))

        # ===== Notebook & Tabs =====
        self.nb = ttk.Notebook(self)
        self.tab_att = AttendanceTab(self.nb)
        self.tab_emp = EmployeeTab(self.nb)
        self.tab_rep = ReportTab(self.nb)

        self.nb.add(self.tab_att, text="📸 Chấm công")
        self.nb.add(self.tab_emp, text="👥 Nhân viên")
        self.nb.add(self.tab_rep, text="📊 Báo cáo")
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        # ===== Trạng thái đăng nhập & chặn khi chuyển tab =====
        self.is_logged_in = False
        self._last_allowed_tab = 0   # luôn cho phép tab 0 (Chấm công)
        self._pending_tab = None     # tab người dùng định vào
        self.nb.select(0)
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ===== Đóng cửa sổ =====
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_tab_changed(self, _evt):
        """Nếu chưa đăng nhập mà bấm sang tab 1/2 -> bật LoginWindow."""
        idx = self.nb.index(self.nb.select())
        if idx == 0:
            self._last_allowed_tab = 0
            return

        if not self.is_logged_in and idx in (1, 2):
            self._pending_tab = idx                    # nhớ tab muốn vào
            self.nb.select(self._last_allowed_tab)     # quay lại Chấm công
            LoginWindow(self, on_success=self._unlock_tabs)
        else:
            self._last_allowed_tab = idx

    def _unlock_tabs(self, username: str):
        """Gọi sau khi đăng nhập thành công."""
        self.is_logged_in = True
        # chuyển đến tab mà người dùng vừa chọn trước đó (nếu có)
        if self._pending_tab in (1, 2):
            self.nb.select(self._pending_tab)
        else:
            self.nb.select(1)  # mặc định đưa sang Nhân viên
        self._pending_tab = None

    def on_close(self):
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

