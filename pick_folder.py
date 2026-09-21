"""Hộp thoại chọn thư mục gốc của Windows.

Được main.py gọi như một tiến trình con để mở hộp thoại chọn thư mục thật
(không phải ô nhập text). In ra stdout đường dẫn người dùng chọn, hoặc
chuỗi rỗng nếu họ bấm Cancel.
"""

import sys
import tkinter as tk
from tkinter import filedialog


def main() -> None:
    initial_dir = sys.argv[1] if len(sys.argv) > 1 else None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    kwargs = {"title": "Chọn thư mục lưu video", "mustexist": False}
    if initial_dir:
        kwargs["initialdir"] = initial_dir

    try:
        folder = filedialog.askdirectory(**kwargs)
    except Exception:
        folder = ""
    finally:
        root.destroy()

    print(folder or "")


if __name__ == "__main__":
    main()
