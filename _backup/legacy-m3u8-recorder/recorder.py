import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)

# Các dấu hiệu trong log ffmpeg cho thấy link chết vì hết hạn / bị từ chối,
# khác với các lỗi cấu hình khác.
EXPIRED_PATTERNS = [
    "403 forbidden",
    "404 not found",
    "server returned 4",
    "connection refused",
    "connection reset",
    "error opening input",
    "invalid data found when processing input",
    "end of file",
    "network is unreachable",
]


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_filename_part(s):
    s = re.sub(r'[\\/:*?"<>|]', "_", s).strip()
    return s or "phong"


def validate_link(link_text):
    text = link_text.strip()
    if not text:
        raise ValueError("Vui lòng dán link .m3u8.")
    if not text.lower().startswith("http"):
        raise ValueError("Link không hợp lệ — phải bắt đầu bằng http:// hoặc https://")
    return text


class RecordingSession:
    """Một phiên quay độc lập, dùng ffmpeg copy luồng .m3u8 sang .mp4."""

    def __init__(self, job_id, room_label, source_url, output_folder, config, part=1):
        self.job_id = job_id
        self.room_label = room_label
        self.source_url = source_url
        self.output_folder = output_folder
        self.config = config
        self.part = part
        self.process = None
        # starting | recording | stalled | stopped | finished | expired | error
        self.status = "starting"
        self.started_at = None
        self.output_file = None
        self.output_prefix = None
        self.log_file = os.path.join(LOG_DIR, f"{job_id}.log")
        self._lock = threading.Lock()

    def _build_output_path(self):
        os.makedirs(self.output_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        label = safe_filename_part(self.room_label)
        suffix = f"_p{self.part}" if self.part > 1 else ""
        self.output_prefix = f"{label}_{timestamp}{suffix}"
        return os.path.join(self.output_folder, f"{self.output_prefix}.mp4")

    def start(self):
        ffmpeg = self.config["ffmpeg_path"]
        out_path = self._build_output_path()
        self.output_file = out_path

        cmd = [
            ffmpeg, "-y",
            "-i", self.source_url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            out_path,
        ]

        log_f = open(self.log_file, "a", encoding="utf-8", errors="ignore")
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self.started_at = datetime.now()
        self.status = "recording"
        threading.Thread(target=self._watch_process, args=(log_f,), daemon=True).start()

    def _watch_process(self, log_f):
        self.process.wait()
        log_f.close()
        with self._lock:
            if self.status == "stopped":
                return
            content = self.get_last_log_lines(30).lower()
            if any(p in content for p in EXPIRED_PATTERNS):
                self.status = "expired"
            elif self.process.returncode == 0:
                self.status = "finished"
            else:
                self.status = "error"

    def stop(self):
        with self._lock:
            self.status = "stopped"
        if self.process and self.process.poll() is None:
            try:
                if self.process.stdin:
                    self.process.stdin.write(b"q")
                    self.process.stdin.flush()
                self.process.wait(timeout=10)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def _find_actual_output_file(self):
        try:
            if not self.output_prefix:
                return None
            candidates = [
                os.path.join(self.output_folder, f)
                for f in os.listdir(self.output_folder)
                if f.startswith(self.output_prefix)
            ]
            if not candidates:
                return None
            return max(candidates, key=os.path.getmtime)
        except Exception:
            return None

    def get_output_size(self):
        path = self._find_actual_output_file() or self.output_file
        if path and os.path.exists(path):
            self.output_file = path
            return os.path.getsize(path)
        return 0

    def get_last_log_lines(self, n=50):
        try:
            with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            return "".join(lines[-n:])
        except Exception:
            return ""

    def _display_status(self):
        if self.status != "recording":
            return self.status
        # Phát hiện "treo": log không cập nhật trong X giây dù process còn sống
        try:
            threshold = self.config.get("stalled_threshold_seconds", 20)
            mtime = os.path.getmtime(self.log_file)
            if time.time() - mtime > threshold:
                return "stalled"
        except Exception:
            pass
        return "recording"

    def to_dict(self):
        size_bytes = self.get_output_size()
        elapsed = None
        if self.started_at:
            elapsed = int((datetime.now() - self.started_at).total_seconds())
        return {
            "job_id": self.job_id,
            "room_label": self.room_label,
            "status": self._display_status(),
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S") if self.started_at else None,
            "elapsed_seconds": elapsed,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "output_file": self.output_file,
            "part": self.part,
        }


class RecorderManager:
    def __init__(self):
        self.sessions = {}
        self._lock = threading.Lock()
        self._counter = 0

    def start_recording(self, room_label, link_text, output_folder):
        config = load_config()
        room_label = room_label.strip()
        if not room_label:
            raise ValueError("Vui lòng nhập Tên/ID phòng để đặt tên file.")

        source_url = validate_link(link_text)

        with self._lock:
            active_parts = [
                s.part for s in self.sessions.values()
                if s.room_label == room_label
            ]
            for s in self.sessions.values():
                if s.room_label == room_label and s.status in ("starting", "recording", "stalled"):
                    raise ValueError(f"'{room_label}' đang được quay rồi. Dừng phiên cũ trước nếu muốn thay link.")

            next_part = (max(active_parts) + 1) if active_parts else 1
            self._counter += 1
            job_id = f"{safe_filename_part(room_label)}_{int(time.time())}_{self._counter}"
            session = RecordingSession(
                job_id, room_label, source_url,
                output_folder or config["default_output_folder"], config,
                part=next_part,
            )
            self.sessions[job_id] = session

        session.start()
        return session.to_dict()

    def stop_recording(self, job_id):
        with self._lock:
            session = self.sessions.get(job_id)
        if not session:
            raise ValueError("Không tìm thấy phiên quay.")
        session.stop()
        return session.to_dict()

    def stop_all(self):
        with self._lock:
            sessions = list(self.sessions.values())
        for s in sessions:
            if s.status in ("starting", "recording", "stalled"):
                s.stop()

    def get_status(self):
        with self._lock:
            sessions = list(self.sessions.values())
        sessions.sort(key=lambda s: s.started_at or datetime.min, reverse=True)
        return [s.to_dict() for s in sessions]

    def get_log(self, job_id):
        with self._lock:
            session = self.sessions.get(job_id)
        if not session:
            return ""
        return session.get_last_log_lines()
