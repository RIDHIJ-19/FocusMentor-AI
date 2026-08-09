// FocusMentor AI -- web client. Vanilla JS, no framework/build step.
"use strict";

/* ---------- API helper ---------- */

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.detail || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

/* ---------- Settings (localStorage, client-only) ---------- */

const Settings = {
  get checkinsEnabled() { return localStorage.getItem("checkinsEnabled") !== "false"; },
  set checkinsEnabled(v) { localStorage.setItem("checkinsEnabled", v); },
  get voiceEnabled() { return localStorage.getItem("voiceEnabled") !== "false"; },
  set voiceEnabled(v) { localStorage.setItem("voiceEnabled", v); },
  get notifyEnabled() { return localStorage.getItem("notifyEnabled") === "true"; },
  set notifyEnabled(v) { localStorage.setItem("notifyEnabled", v); },
};

/* ---------- Toasts (fallback when Notification isn't available/granted) ---------- */

function toast(message) {
  const stack = document.getElementById("toast-stack");
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => el.remove(), 8000);
}

/* ---------- Announce: toast/notification + speech ---------- */

// Some motivation lines are Hindi movie dialogues written in Roman script
// (no Devanagari to detect), so language is guessed from common Hindi/
// Hinglish words -- lets the browser pick a Hindi voice for those instead
// of mangling them through a default English one.
const _HINDI_WORD_RE = /\b(hai|hoon|nahi|kar|karo|karna|toh|jo|wahi|isliye|mera|dost|bhaago|kaabil|safalta|taaqat|ghayal|ghatak|jhak|cheez|kaayanat|duniya|sher|genda|tumhare|dil|se|milne|abhi|baaki|picture)\b/i;

let _hindiVoice = null;
function _findHindiVoice() {
  if (!("speechSynthesis" in window)) return null;
  const voices = speechSynthesis.getVoices();
  return voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("hi")) || null;
}
if ("speechSynthesis" in window) {
  _hindiVoice = _findHindiVoice();
  speechSynthesis.onvoiceschanged = () => { _hindiVoice = _findHindiVoice(); };
}

function announce(message) {
  if (Settings.notifyEnabled && "Notification" in window && Notification.permission === "granted") {
    new Notification("FocusMentor AI", { body: message });
  } else {
    toast(message);
  }
  if (Settings.voiceEnabled && "speechSynthesis" in window) {
    const utter = new SpeechSynthesisUtterance(message);
    if (_HINDI_WORD_RE.test(message) && _hindiVoice) {
      utter.voice = _hindiVoice;
      utter.lang = _hindiVoice.lang;
    }
    speechSynthesis.speak(utter);
  }
}

async function motivationLine(category) {
  try {
    const r = await api("GET", `/api/motivation/${category}`);
    return r.line || "";
  } catch {
    return "";
  }
}

/* ---------- Sound cues (Web Audio, no bundled audio files) ---------- */

let audioCtx = null;
function getAudioCtx() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  return audioCtx;
}

function beep(freq, durationMs, startDelayMs = 0, gain = 0.15) {
  const ctx = getAudioCtx();
  const osc = ctx.createOscillator();
  const g = ctx.createGain();
  osc.frequency.value = freq;
  g.gain.value = gain;
  osc.connect(g);
  g.connect(ctx.destination);
  const start = ctx.currentTime + startDelayMs / 1000;
  osc.start(start);
  osc.stop(start + durationMs / 1000);
}

function playAlertSound() {
  beep(880, 150);
}

function playSuccessJingle() {
  [[523, 120, 0], [659, 120, 130], [784, 120, 260], [1047, 220, 390]].forEach(
    ([f, d, delay]) => beep(f, d, delay, 0.18)
  );
}

function playSternAlert() {
  [[220, 260, 0], [165, 380, 280]].forEach(([f, d, delay]) => beep(f, d, delay, 0.2));
}

/* ---------- Voice recording (MediaRecorder -> /api/transcribe) ---------- */

class VoiceRecorder {
  constructor(button, textarea, statusEl) {
    this.button = button;
    this.textarea = textarea;
    this.statusEl = statusEl;
    this.mediaRecorder = null;
    this.chunks = [];
    this.button.addEventListener("click", () => this.toggle());
  }

  async toggle() {
    if (this.mediaRecorder && this.mediaRecorder.state === "recording") {
      this.mediaRecorder.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.chunks = [];
      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (e) => this.chunks.push(e.data);
      this.mediaRecorder.onstop = () => this.onStop(stream);
      this.mediaRecorder.start();
      this.button.textContent = "⏹ Stop";
      this.button.classList.add("recording");
      if (this.statusEl) this.statusEl.textContent = "Recording... click Stop when you're done.";
    } catch (exc) {
      if (this.statusEl) this.statusEl.textContent = `Couldn't start recording: ${exc.message}`;
    }
  }

  async onStop(stream) {
    stream.getTracks().forEach((t) => t.stop());
    this.button.disabled = true;
    this.button.textContent = "Transcribing...";
    const blob = new Blob(this.chunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", blob, "recording.webm");
    try {
      const res = await fetch("/api/transcribe", { method: "POST", body: formData });
      const data = await res.json();
      this.button.disabled = false;
      this.button.textContent = "🎤 Record";
      this.button.classList.remove("recording");
      if (data.text) {
        this.textarea.value = (this.textarea.value + " " + data.text).trim();
        if (this.statusEl) this.statusEl.textContent = "Transcribed.";
      } else if (this.statusEl) {
        this.statusEl.textContent = "Couldn't transcribe that -- try again or type instead.";
      }
    } catch {
      this.button.disabled = false;
      this.button.textContent = "🎤 Record";
      this.button.classList.remove("recording");
      if (this.statusEl) this.statusEl.textContent = "Transcription failed -- try again or type instead.";
    }
  }
}

/* ---------- Starfield background ---------- */

function initStarfield() {
  const canvas = document.getElementById("starfield");
  const ctx = canvas.getContext("2d");
  let stars = [];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const count = Math.floor((canvas.width * canvas.height) / 12000);
    stars = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.4 + 0.3,
      phase: Math.random() * Math.PI * 2,
    }));
  }
  window.addEventListener("resize", resize);
  resize();

  let running = true;
  document.addEventListener("visibilitychange", () => {
    running = document.visibilityState === "visible";
    if (running) requestAnimationFrame(draw);
  });

  function draw(t) {
    if (!running) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const s of stars) {
      const alpha = 0.4 + 0.6 * Math.abs(Math.sin(t / 1500 + s.phase));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(232, 236, 247, ${alpha.toFixed(2)})`;
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
}

/* ---------- Global date picker (drives Plan + Dashboard tabs) ---------- */

function updatePlanDateHeadings() {
  const isToday = state.planDate === todayISO();
  document.getElementById("plan-heading").textContent = isToday ? "Today's Plan" : `Plan for ${state.planDate}`;
  document.getElementById("dashboard-heading").textContent = isToday ? "Today's Progress" : `Progress for ${state.planDate}`;
}

function initGlobalDate() {
  state.planDate = todayISO();
  const input = document.getElementById("global-date");
  input.value = state.planDate;
  updatePlanDateHeadings();

  input.addEventListener("change", () => {
    state.planDate = input.value || todayISO();
    updatePlanDateHeadings();
    refreshTasks();
    if (document.getElementById("tab-dashboard").classList.contains("active")) refreshDashboard();
  });

  document.getElementById("global-date-today").addEventListener("click", () => {
    input.value = todayISO();
    input.dispatchEvent(new Event("change"));
  });
}

/* ---------- Tabs ---------- */

function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
      if (btn.dataset.tab === "dashboard") refreshDashboard();
    });
  });
}

/* ---------- Modal helpers ---------- */

function showModal(id) { document.getElementById(id).classList.remove("hidden"); }
function hideModal(id) { document.getElementById(id).classList.add("hidden"); }

/* ---------- App state ---------- */

const state = {
  tasks: [],
  planDate: null, // set from #global-date at init, defaults to today; drives both Plan and Dashboard tabs
  selectedTaskIds: new Set(), // ctrl/cmd-click (or shift-click) toggles membership for bulk delete
  active: null, // { id, name, goal, durationMin, startedAt (ms), pausedSeconds, isPaused, pausedAtMs, checkinIntervalMin, firedCheckinMinutes: Set }
};

/* ---------- Task list (Plan tab) ---------- */

async function refreshTasks() {
  state.tasks = await api("GET", `/api/tasks?date=${state.planDate}`);
  const validIds = new Set(state.tasks.map((t) => t.id));
  for (const id of state.selectedTaskIds) {
    if (!validIds.has(id)) state.selectedTaskIds.delete(id);
  }
  const list = document.getElementById("task-list");
  list.innerHTML = "";
  for (const task of state.tasks) {
    const li = document.createElement("li");
    const mark = task.status === "completed" ? "✓" : task.status === "in_progress" ? "▶" : "○";
    let text = `${mark} ${task.name} (${task.duration_min} min)`;
    if (task.goal) text += ` — ${task.goal}`;
    li.textContent = text;
    li.dataset.id = task.id;
    li.className = `status-${task.status}`;
    if (state.selectedTaskIds.has(task.id)) li.classList.add("selected");
    li.addEventListener("click", (e) => {
      if (e.ctrlKey || e.metaKey || e.shiftKey) {
        if (state.selectedTaskIds.has(task.id)) {
          state.selectedTaskIds.delete(task.id);
        } else {
          state.selectedTaskIds.add(task.id);
        }
      } else {
        state.selectedTaskIds = new Set([task.id]);
      }
      refreshTasks();
    });
    list.appendChild(li);
  }
}

/* ---------- Add Task ---------- */

function initAddTask() {
  const hasStart = document.getElementById("add-has-start-time");
  hasStart.addEventListener("change", () => {
    document.getElementById("add-start-time").disabled = !hasStart.checked;
  });

  document.getElementById("btn-add-task").addEventListener("click", () => {
    document.getElementById("add-name").value = "";
    document.getElementById("add-goal").value = "";
    document.getElementById("add-duration").value = "60";
    document.getElementById("add-task-status").textContent = "";
    hasStart.checked = false;
    document.getElementById("add-start-time").disabled = true;
    showModal("modal-add-task");
  });
  document.getElementById("add-task-cancel").addEventListener("click", () => hideModal("modal-add-task"));
  const addTaskOkBtn = document.getElementById("add-task-ok");
  addTaskOkBtn.addEventListener("click", async () => {
    if (addTaskOkBtn.disabled) return;
    const statusEl = document.getElementById("add-task-status");
    const name = document.getElementById("add-name").value.trim();
    if (!name) {
      statusEl.textContent = "Give the task a name first.";
      return;
    }
    const goal = document.getElementById("add-goal").value.trim() || null;
    const duration_min = parseInt(document.getElementById("add-duration").value, 10) || 30;
    const start_time = hasStart.checked ? document.getElementById("add-start-time").value : null;
    addTaskOkBtn.disabled = true;
    try {
      await api("POST", "/api/tasks", { name, goal, duration_min, start_time, plan_date: state.planDate });
      hideModal("modal-add-task");
      refreshTasks();
    } catch (exc) {
      statusEl.textContent = exc.data?.detail || exc.message;
    } finally {
      addTaskOkBtn.disabled = false;
    }
  });
}

/* ---------- Plan with AI ---------- */

let aiParsedTasks = [];

function initPlanAI() {
  const recorder = new VoiceRecorder(
    document.getElementById("ai-mic"),
    document.getElementById("ai-text"),
    document.getElementById("ai-status")
  );

  document.getElementById("btn-plan-ai").addEventListener("click", () => {
    document.getElementById("ai-text").value = "";
    document.getElementById("ai-status").textContent = "";
    document.getElementById("ai-checklist").innerHTML = "";
    aiParsedTasks = [];
    showModal("modal-plan-ai");
  });
  document.getElementById("ai-cancel").addEventListener("click", () => hideModal("modal-plan-ai"));

  document.getElementById("ai-generate").addEventListener("click", async () => {
    const text = document.getElementById("ai-text").value.trim();
    if (!text) return;
    const btn = document.getElementById("ai-generate");
    btn.disabled = true;
    btn.textContent = "Thinking...";
    try {
      const result = await api("POST", "/api/tasks/parse", { text });
      aiParsedTasks = result.tasks;
      const statusEl = document.getElementById("ai-status");
      statusEl.textContent = result.used_ai ? "Parsed with AI." : "AI unavailable — used basic parsing.";
      const checklist = document.getElementById("ai-checklist");
      checklist.innerHTML = "";
      if (!aiParsedTasks.length) {
        statusEl.textContent += " No tasks could be identified — try rephrasing.";
      }
      aiParsedTasks.forEach((t, i) => {
        let label = `${t.name} — ${t.duration_min} min`;
        if (t.goal) label += ` — ${t.goal}`;
        if (t.start_time) label += ` — starts ${t.start_time}`;
        const row = document.createElement("div");
        row.className = "checklist-item";
        row.innerHTML = `<input type="checkbox" checked data-idx="${i}" style="width:auto;"> <span>${label}</span>`;
        checklist.appendChild(row);
      });
    } finally {
      btn.disabled = false;
      btn.textContent = "Generate Tasks";
    }
  });

  document.getElementById("ai-ok").addEventListener("click", async () => {
    const checked = [...document.querySelectorAll("#ai-checklist input:checked")].map(
      (el) => aiParsedTasks[parseInt(el.dataset.idx, 10)]
    );
    for (const t of checked) {
      await api("POST", "/api/tasks", {
        name: t.name, goal: t.goal, duration_min: t.duration_min, start_time: t.start_time,
        plan_date: state.planDate,
      });
    }
    hideModal("modal-plan-ai");
    refreshTasks();
  });
}

/* ---------- Session control ---------- */

function updateSessionButtons() {
  const active = !!state.active;
  document.getElementById("btn-pause").disabled = !active;
  document.getElementById("btn-finish-early").disabled = !active;
}

async function startSelected() {
  if (state.selectedTaskIds.size === 0) { toast("Select a task first."); return; }
  if (state.selectedTaskIds.size > 1) { toast("Select only one task to start."); return; }
  if (state.active) { toast("A session is already running."); return; }
  const [selectedId] = state.selectedTaskIds;
  const task = state.tasks.find((t) => t.id === selectedId);
  if (!task) return;
  if (task.status === "completed") { toast("This task is already completed."); return; }

  // File the task under whatever calendar day it's actually *started* on,
  // in the user's local time -- an overnight session (start 10pm, finish
  // 2am) should stay under the start date, not roll to the next day.
  const result = await api("POST", `/api/tasks/${task.id}/start`, { local_date: todayISO() });
  if (result.plan_date && result.plan_date !== state.planDate) {
    state.planDate = result.plan_date;
    document.getElementById("global-date").value = state.planDate;
    updatePlanDateHeadings();
  }
  state.active = {
    id: task.id,
    name: task.name,
    goal: task.goal,
    durationMin: result.duration_min,
    startedAtMs: Date.parse(result.started_at),
    pausedSeconds: 0,
    isPaused: false,
    pausedAtMs: null,
    checkinIntervalMin: result.checkin_interval_min,
    firedCheckinMinutes: new Set(),
  };
  updateSessionButtons();
  const flavor = await motivationLine("session_start");
  announce(`Started: ${task.name}. ${flavor}`);
  refreshTasks();
}

async function deleteSelected() {
  if (state.selectedTaskIds.size === 0) return;
  const ids = [...state.selectedTaskIds];
  const failures = [];
  for (const id of ids) {
    try {
      await api("DELETE", `/api/tasks/${id}`);
      state.selectedTaskIds.delete(id);
    } catch (exc) {
      failures.push(exc.message);
    }
  }
  if (failures.length) toast(failures.join(" | "));
  refreshTasks();
}

async function pauseResume() {
  if (!state.active) return;
  if (state.active.isPaused) {
    await api("POST", `/api/tasks/${state.active.id}/resume`);
    state.active.pausedSeconds += Math.floor((Date.now() - state.active.pausedAtMs) / 1000);
    state.active.isPaused = false;
    state.active.pausedAtMs = null;
    document.getElementById("btn-pause").textContent = "Pause";
  } else {
    await api("POST", `/api/tasks/${state.active.id}/pause`);
    state.active.isPaused = true;
    state.active.pausedAtMs = Date.now();
    document.getElementById("btn-pause").textContent = "Resume";
  }
}

function finishEarly() {
  if (!state.active) return;
  triggerSessionEnd();
}

/* ---------- Timer loop ---------- */

function elapsedSeconds() {
  const a = state.active;
  if (!a) return 0;
  const frozenAtMs = a.isPaused ? a.pausedAtMs : Date.now();
  const rawElapsed = Math.floor((frozenAtMs - a.startedAtMs) / 1000);
  return Math.max(0, rawElapsed - a.pausedSeconds);
}

function tick() {
  const a = state.active;
  if (!a) return;

  const elapsed = elapsedSeconds();
  const remaining = a.durationMin * 60 - elapsed;
  const mm = Math.floor(Math.max(0, remaining) / 60).toString().padStart(2, "0");
  const ss = Math.max(0, remaining % 60).toString().padStart(2, "0");
  const label = document.getElementById("session-label");
  label.textContent = `${a.name}: ${mm}:${ss} remaining${a.isPaused ? " (Paused)" : ""}`;
  document.title = a.isPaused ? "FocusMentor AI" : `${mm}:${ss} — FocusMentor AI`;

  if (a.isPaused) return;

  // Check-in thresholds, mirrors the desktop TimerService's duration//4 cadence.
  if (a.checkinIntervalMin > 0) {
    const elapsedMin = Math.floor(elapsed / 60);
    for (let m = a.checkinIntervalMin; m < a.durationMin; m += a.checkinIntervalMin) {
      if (elapsedMin >= m && !a.firedCheckinMinutes.has(m)) {
        a.firedCheckinMinutes.add(m);
        triggerCheckin(m, a.durationMin - m);
      }
    }
  }

  if (remaining <= 0) {
    triggerSessionEnd();
  }
}

setInterval(tick, 1000);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") tick();
});

/* ---------- Check-in modal ---------- */

let checkinRecorder = null;

async function triggerCheckin(elapsedMin, remainingMin) {
  const a = state.active;
  if (!a) return;
  const flavor = await motivationLine("checkin");
  announce(`${a.name}: ${elapsedMin} min in, ${remainingMin} min left. ${flavor}`);

  document.getElementById("checkin-heading").textContent =
    `${a.name}: ${elapsedMin} min in, ${remainingMin} min left. How's it going?`;
  document.getElementById("checkin-flavor").textContent = flavor;
  document.getElementById("checkin-text").value = "";
  document.getElementById("checkin-status").textContent = "";
  showModal("modal-checkin");

  if (!checkinRecorder) {
    checkinRecorder = new VoiceRecorder(
      document.getElementById("checkin-mic"),
      document.getElementById("checkin-text"),
      document.getElementById("checkin-status")
    );
  }

  const okBtn = document.getElementById("checkin-ok");
  okBtn.onclick = async () => {
    if (okBtn.disabled) return;
    okBtn.disabled = true;
    try {
      const note = document.getElementById("checkin-text").value.trim();
      await api("POST", `/api/tasks/${a.id}/checkin`, { note, elapsed_min: elapsedMin, remaining_min: remainingMin });
      hideModal("modal-checkin");
      refreshTasks();
    } finally {
      okBtn.disabled = false;
    }
  };
}

/* ---------- Complete / Finish Early modal ---------- */

let completeRecorder = null;
let sessionEnding = false;

async function triggerSessionEnd() {
  const a = state.active;
  if (!a || sessionEnding) return;
  sessionEnding = true;

  playAlertSound();
  announce(`Your ${a.name} session is complete. How did it go?`);

  document.getElementById("complete-heading").textContent = `Your '${a.name}' session is complete.`;
  document.getElementById("complete-text").value = "";
  document.getElementById("complete-status").textContent = "";
  showModal("modal-complete");

  if (!completeRecorder) {
    completeRecorder = new VoiceRecorder(
      document.getElementById("complete-mic"),
      document.getElementById("complete-text"),
      document.getElementById("complete-status")
    );
  }

  const okBtn = document.getElementById("complete-ok");
  const extendBtn = document.getElementById("complete-extend");
  const incompleteBtn = document.getElementById("complete-incomplete");
  const allBtns = [okBtn, extendBtn, incompleteBtn];

  async function finishSession(extraBody) {
    if (okBtn.disabled) return; // guard against a slow/cold-starting server + an impatient double click
    allBtns.forEach((b) => (b.disabled = true));
    try {
      const note = document.getElementById("complete-text").value.trim();
      const result = await api("POST", `/api/tasks/${a.id}/finish`, { note, ...extraBody });
      hideModal("modal-complete");
      state.active = null;
      sessionEnding = false;
      updateSessionButtons();
      document.getElementById("session-label").textContent = "No active session.";
      document.title = "FocusMentor AI";

      if (result.is_success) {
        playSuccessJingle();
        announce(await motivationLine("celebration"));
      } else if (result.is_shortfall) {
        playSternAlert();
        announce(await motivationLine("fell_short"));
      }
      refreshTasks();
    } catch (exc) {
      document.getElementById("complete-status").textContent = exc.data?.detail || exc.message;
    } finally {
      allBtns.forEach((b) => (b.disabled = false));
    }
  }

  okBtn.onclick = () => finishSession({});
  incompleteBtn.onclick = () => finishSession({ mark_incomplete: true });

  extendBtn.onclick = async () => {
    if (extendBtn.disabled) return; // same double-submit guard as okBtn above
    allBtns.forEach((b) => (b.disabled = true));
    try {
      const note = document.getElementById("complete-text").value.trim();
      const result = await api("POST", `/api/tasks/${a.id}/finish`, { note, extend_requested: true });
      hideModal("modal-complete");
      sessionEnding = false;
      a.durationMin += result.extend_minutes;
      a.checkinIntervalMin = result.checkin_interval_min;

      // The new interval is derived from just the (small) extension amount,
      // so replaying it against the full elapsed time would treat every
      // already-past minute mark as a freshly-crossed, never-fired
      // threshold -- flooding triggerCheckin() for all of them in the very
      // next tick. Pre-mark everything up to "now" as already fired so only
      // genuinely future crossings announce.
      const elapsedMinNow = Math.floor(elapsedSeconds() / 60);
      if (a.checkinIntervalMin > 0) {
        for (let m = a.checkinIntervalMin; m <= elapsedMinNow; m += a.checkinIntervalMin) {
          a.firedCheckinMinutes.add(m);
        }
      }

      announce(`Got it — ${result.extend_minutes} more minutes on ${a.name}.`);
      refreshTasks();
    } catch (exc) {
      document.getElementById("complete-status").textContent = exc.data?.detail || exc.message;
    } finally {
      allBtns.forEach((b) => (b.disabled = false));
    }
  };
}

/* ---------- Dashboard ---------- */

function todayTimeSummary(completedMin, completedCount) {
  if (completedCount === 0) {
    return "No sessions finished yet today — get one done and it'll show up here.";
  }
  const h = Math.floor(completedMin / 60);
  const m = completedMin % 60;
  const time = h > 0 ? `${h}h ${m}m` : `${m}m`;
  const plural = completedCount === 1 ? "session" : "sessions";
  return `You've studied ${time} today across ${completedCount} ${plural}. Keep going.`;
}

async function refreshDashboard() {
  const data = await api("GET", `/api/dashboard?date=${state.planDate}`);
  const total = data.tasks.length;
  const completed = data.tasks.filter((t) => t.status === "completed").length;
  const pct = total ? Math.round((completed / total) * 100) : 0;
  document.getElementById("progress-fill").style.width = `${pct}%`;
  document.getElementById("progress-pct").textContent = `${pct}%`;

  const checklist = document.getElementById("dashboard-checklist");
  checklist.innerHTML = "";
  for (const t of data.tasks) {
    const li = document.createElement("li");
    const mark = t.status === "completed" ? "✓" : "○";
    li.textContent = `${mark} ${t.name} - ${t.status.replace("_", " ")}`;
    checklist.appendChild(li);
  }

  const completedMin = data.tasks
    .filter((t) => t.status === "completed")
    .reduce((sum, t) => sum + t.duration_min, 0);
  document.getElementById("today-time-summary").textContent = todayTimeSummary(completedMin, completed);

  document.getElementById("stat-completed").textContent = `Sessions completed (all time): ${data.completed_all_time}`;
  document.getElementById("stat-days").textContent = `Days with a completed session: ${data.active_days}`;

  const updateList = document.getElementById("update-list");
  updateList.innerHTML = "";
  if (!data.recent_updates.length) {
    const li = document.createElement("li");
    li.textContent = "No check-in or session replies yet.";
    updateList.appendChild(li);
  }
  for (const u of data.recent_updates) {
    const li = document.createElement("li");
    const when = u.created_at.replace("T", " ").slice(0, 16);
    const kindLabel = u.kind === "checkin" ? `checkin, ${u.elapsed_min}m in` : u.kind;
    li.textContent = `[${when}] ${u.task_name} (${kindLabel}): ${u.note || "(no reply)"}`;
    updateList.appendChild(li);
  }
}

function initInsight() {
  document.getElementById("btn-insight").addEventListener("click", async () => {
    const btn = document.getElementById("btn-insight");
    btn.disabled = true;
    btn.textContent = "Thinking...";
    try {
      const result = await api("POST", "/api/insight");
      alert(result.text);
    } finally {
      btn.disabled = false;
      btn.textContent = "Get Mentor Insight";
    }
  });
}

/* ---------- Settings tab ---------- */

function initSettings() {
  const checkins = document.getElementById("setting-checkins");
  const voice = document.getElementById("setting-voice");
  const notify = document.getElementById("setting-notify");
  checkins.checked = Settings.checkinsEnabled;
  voice.checked = Settings.voiceEnabled;
  notify.checked = Settings.notifyEnabled;

  checkins.addEventListener("change", () => (Settings.checkinsEnabled = checkins.checked));
  voice.addEventListener("change", () => (Settings.voiceEnabled = voice.checked));
  notify.addEventListener("change", async () => {
    if (notify.checked && "Notification" in window) {
      const perm = await Notification.requestPermission();
      Settings.notifyEnabled = perm === "granted";
      notify.checked = perm === "granted";
    } else {
      Settings.notifyEnabled = false;
    }
  });
}

/* ---------- Sidebar to-dos (sticky note) ---------- */

function todayISO() {
  const d = new Date();
  const offset = d.getTimezoneOffset();
  return new Date(d.getTime() - offset * 60000).toISOString().slice(0, 10);
}

async function refreshTodos() {
  const date = document.getElementById("todo-date").value || todayISO();
  const todos = await api("GET", `/api/todos?date=${encodeURIComponent(date)}`);
  const list = document.getElementById("todo-list");
  list.innerHTML = "";
  if (!todos.length) {
    const li = document.createElement("li");
    li.className = "todo-empty";
    li.textContent = "Nothing jotted down for this day yet.";
    list.appendChild(li);
    return;
  }
  for (const todo of todos) {
    const li = document.createElement("li");
    li.className = "todo-item" + (todo.done ? " done" : "");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = !!todo.done;
    checkbox.addEventListener("change", async () => {
      await api("POST", `/api/todos/${todo.id}/toggle`);
      refreshTodos();
    });
    const text = document.createElement("span");
    text.className = "todo-text";
    text.textContent = todo.text;
    const remove = document.createElement("button");
    remove.className = "todo-remove";
    remove.textContent = "×";
    remove.title = "Remove";
    remove.addEventListener("click", async () => {
      await api("DELETE", `/api/todos/${todo.id}`);
      refreshTodos();
    });
    li.append(checkbox, text, remove);
    list.appendChild(li);
  }
}

async function refreshNote() {
  const date = document.getElementById("todo-date").value || todayISO();
  const result = await api("GET", `/api/notes?date=${encodeURIComponent(date)}`);
  document.getElementById("notes-text").value = result.text || "";
  document.getElementById("notes-status").textContent = "";
}

async function saveNote() {
  const date = document.getElementById("todo-date").value || todayISO();
  const text = document.getElementById("notes-text").value;
  await api("POST", "/api/notes", { date, text });
  const status = document.getElementById("notes-status");
  status.textContent = "Saved.";
  setTimeout(() => { if (status.textContent === "Saved.") status.textContent = ""; }, 2500);
}

function initTodos() {
  const dateInput = document.getElementById("todo-date");
  dateInput.value = todayISO();
  dateInput.addEventListener("change", () => {
    refreshTodos();
    refreshNote();
  });

  const textInput = document.getElementById("todo-text");
  async function addTodo() {
    const text = textInput.value.trim();
    if (!text) return;
    await api("POST", "/api/todos", { date: dateInput.value || todayISO(), text });
    textInput.value = "";
    refreshTodos();
  }
  document.getElementById("todo-add").addEventListener("click", addTodo);
  textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") addTodo();
  });

  document.getElementById("notes-save").addEventListener("click", saveNote);
  document.getElementById("notes-text").addEventListener("blur", saveNote);

  refreshTodos();
  refreshNote();
}

/* ---------- Init ---------- */

document.getElementById("btn-start").addEventListener("click", startSelected);
document.getElementById("btn-delete").addEventListener("click", deleteSelected);
document.getElementById("btn-pause").addEventListener("click", pauseResume);
document.getElementById("btn-finish-early").addEventListener("click", finishEarly);

initStarfield();
initGlobalDate();
initTabs();
initAddTask();
initPlanAI();
initInsight();
initSettings();
initTodos();
refreshTasks();
