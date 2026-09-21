import sys
import tkinter as tk
from tkinter import filedialog


def main():
    initial_dir = sys.argv[1] if len(sys.argv) > 1 else None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    kwargs = {}
    if initial_dir:
        kwargs["initialdir"] = initial_dir

    folder = filedialog.askdirectory(title="Chọn thư mục lưu video", **kwargs)
    root.destroy()
    print(folder)


if __name__ == "__main__":
    main()
