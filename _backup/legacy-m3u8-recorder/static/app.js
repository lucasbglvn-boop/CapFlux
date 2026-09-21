let selectedJobId = null;
let notifiedJobs = new Set(); // tránh bắn thông báo trùng cho cùng 1 job

const STATUS_LABELS = {
  starting: "Đang khởi động",
  recording: "Đang quay",
  stalled: "Có thể sắp mất kết nối",
  expired: "Link đã hết hạn",
  error: "Lỗi",
  stopped: "Đã dừng",
  finished: "Hoàn tất",
};

const RESUMABLE_STATUSES = ["expired", "error", "stopped"];
const ACTIVE_STATUSES = ["starting", "recording", "stalled"];

function requestNotificationPermission() {
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
}

function notify(title, body) {
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, { body });
  }
}

async function startRecording(prefillPart) {
  const roomLabel = document.getElementById("roomLabel").value.trim();
  const linkText = document.getElementById("linkText").value.trim();
  const outputFolder = document.getElementById("outputFolder").value.trim();
  const errorBox = document.getElementById("formError");
  errorBox.textContent = "";

  if (!roomLabel) { errorBox.textContent = "Vui lòng nhập Tên phòng."; return; }
  if (!linkText) { errorBox.textContent = "Vui lòng dán link .m3u8."; return; }

  const res = await fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ room_label: roomLabel, link_text: linkText, output_folder: outputFolder }),
  });
  const data = await res.json();
  if (!data.ok) { errorBox.textContent = data.error; return; }

  document.getElementById("linkText").value = "";
  if (!prefillPart) document.getElementById("roomLabel").value = "";
  refreshStatus();
}

async function stopRecording(jobId, event) {
  event.stopPropagation();
  await fetch("/api/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });
  refreshStatus();
}

async function stopAll() {
  if (!confirm("Dừng tất cả các phòng đang quay?")) return;
  await fetch("/api/stop-all", { method: "POST" });
  refreshStatus();
}

function resumeRoom(roomLabel, event) {
  event.stopPropagation();
  document.getElementById("roomLabel").value = roomLabel;
  document.getElementById("linkText").focus();
  document.getElementById("formError").textContent = `Dán link .m3u8 mới cho "${roomLabel}" rồi bấm Bắt đầu quay.`;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function formatDuration(seconds) {
  if (seconds == null) return "-";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
}

function renderCard(s) {
  const label = STATUS_LABELS[s.status] || s.status;
  const canStop = ACTIVE_STATUSES.includes(s.status);
  const canResume = RESUMABLE_STATUSES.includes(s.status);
  const partTag = s.part > 1 ? `<span class="part-tag">phần ${s.part}</span>` : "";

  const actions = [];
  if (canStop) {
    actions.push(`<button class="btn btn-sm btn-stop" data-action="stop" data-job="${s.job_id}">Dừng</button>`);
  }
  if (canResume) {
    actions.push(`<button class="btn btn-sm btn-resume" data-action="resume" data-room="${s.room_label}">Dán link mới</button>`);
  }

  const div = document.createElement("div");
  div.className = `session-card status-${s.status}` + (s.job_id === selectedJobId ? " selected" : "");
  div.dataset.job = s.job_id;
  div.innerHTML = `
    <div class="card-main">
      <div class="card-title">
        <span class="room-name">${s.room_label}</span>
        ${partTag}
        <span class="badge badge-${s.status}"><span class="badge-dot"></span>${label}</span>
      </div>
      <div class="card-sub">
        <span>Bắt đầu: <b>${s.started_at || "-"}</b></span>
        <span>Thời lượng: <b>${formatDuration(s.elapsed_seconds)}</b></span>
        <span>Dung lượng: <b>${s.size_mb} MB</b></span>
      </div>
    </div>
    <div class="card-actions">${actions.join("")}</div>
  `;
  div.addEventListener("click", () => selectJob(s.job_id, s.room_label));
  div.querySelectorAll('[data-action="stop"]').forEach((btn) =>
    btn.addEventListener("click", (e) => stopRecording(btn.dataset.job, e))
  );
  div.querySelectorAll('[data-action="resume"]').forEach((btn) =>
    btn.addEventListener("click", (e) => resumeRoom(btn.dataset.room, e))
  );
  return div;
}

async function refreshStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();
  const listEl = document.getElementById("sessionList");
  const emptyEl = document.getElementById("emptyState");

  listEl.innerHTML = "";
  emptyEl.style.display = data.sessions.length ? "none" : "block";

  let activeCount = 0;
  let totalSize = 0;
  let warningCount = 0;

  data.sessions.forEach((s) => {
    listEl.appendChild(renderCard(s));
    if (ACTIVE_STATUSES.includes(s.status)) activeCount++;
    totalSize += s.size_mb;

    if ((s.status === "expired" || s.status === "stalled") && !notifiedJobs.has(s.job_id)) {
      notifiedJobs.add(s.job_id);
      warningCount++;
      const msg = s.status === "expired"
        ? `Link của "${s.room_label}" đã hết hạn — cần dán link mới.`
        : `"${s.room_label}" có dấu hiệu mất kết nối — kiểm tra lại.`;
      notify("Bigo Recorder", msg);
    }
  });

  document.getElementById("statActive").textContent = activeCount;
  document.getElementById("statTotalSize").textContent =
    totalSize >= 1024 ? (totalSize / 1024).toFixed(2) + " GB" : totalSize.toFixed(1) + " MB";

  const warnTotal = data.sessions.filter((s) => s.status === "expired" || s.status === "stalled").length;
  document.title = warnTotal > 0 ? `(${warnTotal}) Bigo Recorder — cần xử lý` : "Bigo Recorder";

  if (selectedJobId) refreshLog();
}

function selectJob(jobId, roomLabel) {
  selectedJobId = jobId;
  document.getElementById("logRoomName").textContent = `— ${roomLabel}`;
  document.querySelectorAll(".session-card").forEach((el) => {
    el.classList.toggle("selected", el.dataset.job === jobId);
  });
  refreshLog();
}

async function refreshLog() {
  if (!selectedJobId) return;
  const res = await fetch(`/api/log/${selectedJobId}`);
  const data = await res.json();
  const logBox = document.getElementById("logBox");
  logBox.textContent = data.log || "(chưa có log)";
  logBox.scrollTop = logBox.scrollHeight;
}

async function browseFolder() {
  const currentFolder = document.getElementById("outputFolder").value.trim();
  const btn = document.getElementById("browseBtn");
  btn.disabled = true;
  btn.textContent = "Đang mở...";
  try {
    const res = await fetch("/api/pick-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_folder: currentFolder }),
    });
    const data = await res.json();
    if (data.ok && data.folder) {
      document.getElementById("outputFolder").value = data.folder;
    }
  } catch (e) {
    document.getElementById("formError").textContent = "Không mở được hộp thoại chọn thư mục.";
  } finally {
    btn.disabled = false;
    btn.textContent = "Duyệt...";
  }
}

document.getElementById("startBtn").addEventListener("click", () => startRecording(false));
document.getElementById("browseBtn").addEventListener("click", browseFolder);
document.getElementById("stopAllBtn").addEventListener("click", stopAll);

requestNotificationPermission();
refreshStatus();
setInterval(refreshStatus, 2000);
