import io
import datetime as dt
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd

import mysql.connector
from mysql.connector import Error

# ---------- Cấu hình MySQL ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",          # đổi theo user MySQL của bạn
    "password": "29092005",    # đổi mật khẩu của bạn
    "database": "face_attendance",  # đảm bảo DB đã được tạo
    "charset": "utf8mb4",
    "use_unicode": True,
}

# ---------- Low-level DB ----------
def get_conn():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        # Để UI bắt lỗi và hiển thị messagebox, ta ném lỗi lên thay vì trả None
        raise RuntimeError(f"Lỗi kết nối MySQL: {e}")

def init_db():
    con = get_conn()
    try:
        cur = con.cursor()
        # employees
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                emp_code VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                department VARCHAR(100),
                phone VARCHAR(20),
                embedding LONGBLOB NOT NULL,
                created_at DATETIME NOT NULL,
                INDEX idx_emp_code (emp_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # attendance
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                emp_id INT NOT NULL,
                ts DATETIME NOT NULL,
                device VARCHAR(50),
                INDEX idx_att_emp (emp_id),
                INDEX idx_att_ts (ts),
                CONSTRAINT fk_att_emp
                    FOREIGN KEY(emp_id) REFERENCES employees(id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
                # users (đơn giản: lưu thẳng password; nếu muốn, bạn có thể băm sau)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # tạo tài khoản mặc định nếu chưa có
        cur.execute("SELECT COUNT(*) FROM users WHERE username=%s", ("admin",))
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO users(username, password) VALUES(%s, %s)", ("admin", "123456"))

        con.commit()
    finally:
        try:
            cur.close()
        except Exception:
            pass
        con.close()

# ---------- Numpy <-> Blob ----------
def np_to_blob(vec: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, vec.astype(np.float32))
    return buf.getvalue()

def blob_to_np(blob: bytes) -> np.ndarray:
    buf = io.BytesIO(blob)
    buf.seek(0)
    return np.load(buf, allow_pickle=False)

# ---------- Queries ----------
def load_all_embeddings() -> pd.DataFrame:
    con = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT id, emp_code, name, department, phone, embedding FROM employees",
            con,
        )
    finally:
        con.close()

    if not df.empty:
        df["embedding_vec"] = df["embedding"].apply(blob_to_np)
    else:
        df["embedding_vec"] = []
    return df

def add_employee(emp_code: str, name: str, department: str, phone: str, embedding: np.ndarray):
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO employees(emp_code, name, department , phone , embedding, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (emp_code, name, department, phone, np_to_blob(embedding), dt.datetime.now()))
        con.commit()
        return True, "Đã thêm nhân viên."
    except mysql.connector.IntegrityError:
        return False, "Mã nhân viên đã tồn tại."
    except Exception as e:
        return False, f"Lỗi: {e}"
    finally:
        try:
            cur.close()
        finally:
            con.close()

def delete_employee(emp_id: int) -> None:
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
        con.commit()
    finally:
        try:
            cur.close()
        finally:
            con.close()

def mark_attendance(emp_id: int, device: str = "desktop") -> None:
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO attendance(emp_id, ts, device) VALUES (%s, %s, %s)
        """, (emp_id, dt.datetime.now(), device))
        con.commit()
    finally:
        try:
            cur.close()
        finally:
            con.close()

def get_attendance(start: Optional[dt.date] = None, end: Optional[dt.date] = None) -> pd.DataFrame:
    """
    Trả về attendance kèm name/department bằng JOIN (gọn & nhanh).
    start/end có thể là date/datetime/chuỗi 'YYYY-MM-DD'.
    """
    con = get_conn()
    try:
        q = """
            SELECT
                a.emp_id,
                e.name,
                e.department,
                a.ts,
                a.device
            FROM attendance a
            JOIN employees e ON e.id = a.emp_id
        """
        params = []
        where = []
        if start and end:
            where.append("DATE(a.ts) BETWEEN %s AND %s")
            # Nếu là datetime.date, mysql-connector tự serialize được
            params += [start, end]
        elif start:
            where.append("DATE(a.ts) >= %s")
            params.append(start)
        elif end:
            where.append("DATE(a.ts) <= %s")
            params.append(end)

        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY a.ts"

        df = pd.read_sql_query(q, con, params=params)
    finally:
        con.close()

    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
    return df

def compute_work_hours(att_df: pd.DataFrame) -> pd.DataFrame:
    if att_df.empty:
        return att_df
    df = att_df.copy()
    df["date"] = df["ts"].dt.date
    agg = (
        df.sort_values(["emp_id", "ts"])
          .groupby(["emp_id", "name", "department", "date"])
          .agg(first_in=("ts", "min"),
               last_out=("ts", "max"),
               scans=("ts", "count"))
          .reset_index()
    )
    agg["hours"] = (agg["last_out"] - agg["first_in"]).dt.total_seconds() / 3600.0
    agg.loc[agg["scans"] <= 1, "hours"] = 0.0
    return agg
def check_login(username: str, password: str) -> bool:
    con = get_conn()
    cur = con.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM users WHERE username=%s AND password=%s LIMIT 1",
            (username, password)
        )
        return cur.fetchone() is not None
    finally:
        try:
            cur.close()
        finally:
            con.close()


