# FocusMentor AI — Development Plan

This file records the architecture decisions and phased roadmap for this
project, for future reference. It reflects the vision in [idea.txt](idea.txt).

## Development approach

The project is built incrementally, per the phased plan below. **We are
currently on Phase 3.** Do not skip ahead — each phase should be working and
usable before the next is added.

## Phase 1 — Basic Working Application (DONE)

A functional desktop productivity app, no AI yet.

### Technology choices

- **Language:** Python 3.10 (already on this machine; stdlib covers SQLite,
  sound, and Windows registry access — no paid tools anywhere).
- **GUI:** PySide6 (Qt for Python). Chosen over Tkinter/CustomTkinter/Electron
  because it has built-in, free support for exactly what this app needs:
  `QSystemTrayIcon` (minimize-to-tray + native Windows toast notifications),
  `QTimer` (session countdowns), and it's the same ecosystem that Phase 2/3
  (AI + voice) will extend, since Python has the best free tooling for
  speech-to-text (faster-whisper) and local/free LLMs (Ollama, free-tier
  cloud APIs).
- **Database:** SQLite via the stdlib `sqlite3` module — zero setup, a single
  file, free, durable across restarts.
- **Notifications:** `QSystemTrayIcon.showMessage` (native Windows toasts).
- **Sound:** `winsound` (stdlib, Windows-only, free).
- **Autostart:** Windows Registry `HKCU\...\Run` key via stdlib `winreg`
  (no admin rights needed), toggled from a Settings checkbox.

### Project structure

```
FocusMentor AI/
  idea.txt              # original vision doc
  PLAN.md                # this file
  README.md              # setup instructions
  USAGE.md                # day-to-day usage guide
  requirements.txt
  app/
    main.py               # entry point + logging config (logs/app.log)
    config.py             # paths & constants
    db/
      database.py         # connection + schema (tasks, updates)
      repository.py       # TaskRepository (CRUD, stats)
      update_repository.py  # UpdateRepository (checkin/complete reply history)
    models/
      task.py              # Task dataclass
      update.py             # Update dataclass (CHECKIN/COMPLETE kinds)
    services/
      timer_service.py     # QTimer-backed countdown + checkin_due, Qt signals
      notification_service.py  # tray notifications + sound + speak() (TTS)
      autostart_service.py     # winreg Run-key toggle
      settings_service.py      # QSettings-backed API key / feature toggles
      rule_based_parser.py     # free/offline NL plan parser (fallback)
      ai_service.py             # Groq client + fallback to rule_based_parser
      voice_service.py           # VoiceRecorder: mic -> in-memory WAV
      motivation.py               # space/sassy flavor one-liners
    ui/
      main_window.py        # Plan / Dashboard / Settings tabs
      theme.py                # dark space QSS stylesheet (applied globally)
      starfield_widget.py      # animated twinkling-stars background
      dashboard_widget.py       # today's % + checklist + long-term stats + Recent Updates
      task_dialog.py             # Add Task modal
      ai_plan_dialog.py           # "Plan with AI" modal
      mentor_insight_dialog.py    # "Get Mentor Insight" modal
      voice_reply_widget.py        # shared text+🎤 reply input (used by both dialogs below)
      checkin_dialog.py             # mid-session "how's it going?" prompt
      complete_session_dialog.py    # "how did it go?" prompt on session end
      tray_icon.py                 # system tray icon + Show/Quit menu
  data/
    mentor.db              # created at runtime (gitignored)
  logs/
    app.log                # rotating log file (gitignored)
```

### Data model

`tasks` table (SQLite): `id, name, goal, plan_date, start_time,
duration_min, status, notes, created_at, started_at`. `status` is one of
`not_started`, `in_progress`, `completed`. `plan_date` makes history
queryable per day, `notes` holds the latest/final note against a task, and
`started_at` (set when a session actually starts, `app/db/repository.py`'s
`update_status(..., started_at=...)`) is what lets the app tell a genuinely
overdue session apart from one that just hasn't finished yet -- see
"Crash/force-quit self-healing" below. Existing databases get this column
via a one-line `ALTER TABLE` migration in `app/db/database.py`'s `_migrate()`
(checked via `PRAGMA table_info`, so it's a no-op on fresh installs).

`updates` table: `id, task_id, kind ('checkin'|'complete'), elapsed_min,
remaining_min, note, created_at` — a full timestamped history of every
check-in and completion reply per task (unlike `tasks.notes`, which only
ever holds one value). This is what Phase 4's pattern analysis will read
from for weak-area/consistency insights.

### What works today

- Add a task (name, goal, duration, optional start time).
- Start a task → live countdown shown in the window and the tray tooltip.
- **Mid-session check-ins**: while a session runs, `TimerService` (in
  `app/services/timer_service.py`) emits a `checkin_due(elapsed_min,
  remaining_min)` signal at an interval computed as `duration_min // 4` —
  a 1-hour task checks in every ~15 min, a 2-hour task every ~30 min, always
  yielding about 3 check-ins regardless of session length (so longer tasks
  aren't nagged more often), gated by `config.MIN_CHECKIN_DURATION_MIN = 15` —
  tasks shorter than 15 minutes never get check-ins at all. Each firing
  announces via `_announce()` (tray notification + spoken TTS, see below),
  brings the window forward, and opens `app/ui/checkin_dialog.py`
  (`CheckinDialog`) asking "How's it going?" with a text/voice reply — the
  timer keeps running underneath. Toggle check-ins on/off via the Settings
  tab (`settings_service.get/set_checkins_enabled`); the ÷4 cadence itself
  isn't user-configurable by design.
- On completion: sound + announcement + `CompleteSessionDialog` ("how did it
  go?") for a text/voice reply.
- **Reply history**: both the check-in and completion replies are stored as
  rows in a separate `updates` SQLite table (`app/db/update_repository.py`,
  `UpdateRepository`; model in `app/models/update.py`) — `kind` is
  `"checkin"` (with `elapsed_min`/`remaining_min`) or `"complete"`. This is
  in addition to `tasks.notes`, which still holds just the latest/final note
  for backward compatibility with existing Dashboard/insight code. The
  Dashboard's "Recent Updates" section (`dashboard_widget.py`) lists the last
  14 days of these, newest first, so replies aren't just written and
  forgotten. `CheckinDialog` and `CompleteSessionDialog` both embed a shared
  `app/ui/voice_reply_widget.py` (`VoiceReplyWidget`) for the text+🎤 input,
  rather than duplicating the recording state machine.
- **Voice announcements**: session-start, check-in, and session-complete
  messages are spoken aloud via offline TTS (`pyttsx3`/Windows SAPI, free, no
  internet) through `NotificationService.speak()` in
  `app/services/notification_service.py`, in addition to the tray
  notification (`MainWindow._announce()`). Toggle via Settings
  ("Speak notifications aloud" / `settings_service.get/set_voice_enabled`).
- **Logging**: `app/main.py` configures a rotating file handler writing to
  `logs/app.log` (gitignored, 1MB rotation, 3 backups) plus console output,
  at INFO level. Session starts, check-in firings, and notifications are all
  logged — useful for diagnosing "why didn't X happen" without guesswork.
- Closing the window minimizes to tray instead of quitting; tray icon has
  Show/Quit.
- Dashboard tab: today's completion %, a checklist, and simple all-time stats
  (sessions completed, days with at least one completed session).
- Settings tab: toggle "start automatically when Windows starts."
- All data persists in `data/mentor.db` across restarts.

## Phase 2 — AI Integration (DONE)

- **Natural language task creation**: "Plan with AI" button on the Plan tab
  opens `app/ui/ai_plan_dialog.py` — type something like "I want to spend 2
  hours on DSA, 3 hours on my AI project, and 1 hour reading research
  papers," review the parsed tasks (editable checklist), then add the
  checked ones via the existing `TaskRepository.create()`.
- **AI provider**: Groq's free API (`llama-3.1-8b-instant`, OpenAI-compatible
  chat completions, no credit card) via `app/services/ai_service.py`, using
  the `requests` library. (Originally used stdlib `urllib.request` for text
  calls to avoid a new dependency — switched to `requests` after discovering
  urllib's default `Python-urllib/x.x` User-Agent gets blocked by Groq's
  Cloudflare bot protection, error 403 / Cloudflare code 1010. `requests`'
  User-Agent isn't blocked, and it was already a dependency for the audio
  transcription upload, so this removed the inconsistency instead of adding
  a workaround.)
- **API key storage** (`app/services/settings_service.py`), checked in this
  order — first one found wins:
  1. `GROQ_API_KEY` environment variable
  2. `GROQ_API_KEY=...` line in a `.env` file at the project root — copy
     `.env.example` to `.env` and paste the key there. This file is
     git-ignored and read directly by the app; it's the recommended way to
     supply the key without typing it into the UI.
  3. The Settings tab's saved value, via `QSettings` (same per-user registry
     idiom as autostart).
  The Settings tab shows which source is currently active.
- **Free fallback (always available)**: `app/services/rule_based_parser.py`
  is a dependency-free regex parser handling the phrasings idea.txt gives as
  examples ("X hours on Y", "Y from 8 AM to 10 AM"). It's used directly when
  no API key is configured, and automatically as a fallback if the Groq call
  fails for any reason (offline, bad key, rate limit) — the feature never
  hard-depends on an external service, per idea.txt's "free alternative"
  requirement.
- **AI suggestions / basic progress analysis**: "Get Mentor Insight" button
  on the Dashboard tab opens `app/ui/mentor_insight_dialog.py`, which sends a
  summary of the last 14 days of tasks (name, goal, status, notes) to Groq
  for a few sentences of coaching feedback. Without a key (or on failure), it
  falls back to a locally-computed summary (completion rate, most common
  task, latest note) — see `AIService._local_insight`.
- New repository method: `TaskRepository.get_recent(days=14)`.

## Phase 3 — Voice Interaction (DONE)

- **Speech-to-text provider**: Groq's free Whisper endpoint
  (`whisper-large-v3-turbo` via `/openai/v1/audio/transcriptions`) — the same
  Groq key/account already set up in Phase 2, no separate local model
  download. This superseded the originally-sketched local `faster-whisper`
  approach once the user already had a Groq key in hand for text; see
  `AIService.transcribe_audio()` in `app/services/ai_service.py`.
- **Microphone capture**: `app/services/voice_service.py`'s `VoiceRecorder`
  wraps `sounddevice.InputStream` (free, MIT-licensed, PortAudio-backed) to
  record 16kHz mono audio and encode it as an in-memory WAV via stdlib
  `wave` — the exact format Whisper expects.
- **Voice-based plan creation**: a "🎤 Record" button in
  `app/ui/ai_plan_dialog.py` next to the plan textarea — click to record,
  click again to stop and transcribe, and the text is appended into the
  textarea for the user to review/edit before "Generate Tasks" (same
  pipeline as typed input).
- **Voice-based progress updates**: the same "🎤 Record" pattern in
  `app/ui/complete_session_dialog.py`, feeding the `notes` field instead of
  typing (matches idea.txt's example: "I solved two binary search problems
  but struggled with...").
- **No key configured**: clicking Record shows "Voice input needs a Groq API
  key (Settings tab)" rather than attempting to record — voice is additive,
  typing still works everywhere it always has.
- New dependencies: `sounddevice`, `numpy` (mic capture), `requests` (used
  only for the multipart audio upload in `ai_service.py`; the existing
  text-based Groq calls still use stdlib `urllib`).

## UI theme + motivational flavor text (DONE)

A visual overhaul requested after the default Qt look ("gray boxes") wasn't
motivating to actually use — pure presentation layer, no data/logic changes:

- **`app/ui/theme.py`** — a single dark "space" QSS stylesheet (deep navy
  background, cyan primary accent, magenta secondary accent, rounded
  tabs/buttons/fields) applied once via `app.setStyleSheet(...)` in
  `app/main.py`, so it cascades to every existing dialog automatically with
  zero per-dialog changes.
- **`app/ui/starfield_widget.py`** (`StarfieldWidget`) — a light (~12 fps,
  60 stars) animated twinkling starfield painted behind the main window's
  content, visible around its edges. `MainWindow.hideEvent`/`showEvent`
  call `pause()`/`resume()` so it costs nothing while minimized to tray —
  matters for a background app.
- **`app/services/motivation.py`** — original, punchy aphorisms in the
  classic quotable-poster style (e.g. "No pressure, no diamonds"; iterated
  on after early drafts leaned too much on confusing sci-fi jargon), in
  three categories (`SESSION_START`, `CHECKIN`, `SESSION_COMPLETE`).
  `get_line(category)` picks randomly with simple no-immediate-repeat
  tracking. Wired into
  `MainWindow._on_start_selected` / `_on_checkin_due` / `_on_timer_finished`:
  appended to the same sentence used for both the tray notification and the
  spoken TTS announcement (`_announce()`), and also shown as a highlighted
  line inside `CheckinDialog`/`CompleteSessionDialog` (both take an optional
  `flavor_line` param now).
- Tab labels got emoji prefixes ("🚀 Plan", "📊 Dashboard", "⚙️ Settings")
  for a more app-like feel.

## Stability fixes (DONE)

Found via real multi-hour usage, not synthetic testing:

- **TTS crashed the whole app after ~3 hours of use.** `pyttsx3`'s SAPI/COM
  driver, called in-process repeatedly, corrupted COM state badly enough to
  segfault the process (a native crash — no Python exception, nothing to
  catch) right as Qt tried to activate a window immediately after a
  `speak()` call. Fixed in `NotificationService.speak()`
  (`app/services/notification_service.py`) by moving TTS into a short-lived
  child process per announcement (`subprocess.Popen([sys.executable, "-c",
  ...])`) — fully isolates the risky COM state from the main Qt process, and
  as a bonus it's non-blocking now instead of freezing the UI during
  `runAndWait()`.
- **Crash/force-quit self-healing.** A task left `in_progress` when the
  process dies (that TTS crash, or `Quit` from the tray mid-session, which
  bypasses `MainWindow.closeEvent`) used to sit stuck forever — a fresh
  launch always starts with no active timer, so it could never resume or
  finish on its own, and needed manual deletion. `MainWindow.__init__` now
  calls `_cleanup_stale_sessions()` before the first `refresh()`: any
  `in_progress` task whose `started_at + duration_min` has already passed
  gets auto-deleted (logged as a warning, and surfaced as a tray
  notification listing what was removed) — see
  `TaskRepository.delete_overdue_in_progress()`.

## AI-judged completion feedback (DONE)

The session-complete flow now actually uses AI on what you wrote/said, not
just a random flavor line regardless of outcome:

- `AIService.assess_completion(task_name, goal, note)` in
  `app/services/ai_service.py` reads your own end-of-session note and
  returns `SUCCESS`, `SHORTFALL`, or `UNCLEAR`. Empty notes are always
  `UNCLEAR` (never guessed). With a Groq key: one classification call. No
  key / call fails: a keyword-heuristic fallback (`_local_assess` —
  positive markers like "finished"/"done" vs. negative ones like
  "didn't"/"only"/"ran out of time"; both-or-neither present → `UNCLEAR`),
  same free-first-class-citizen pattern as `rule_based_parser.py`.
- `NotificationService` gained `play_success_jingle()` (cheerful ascending
  `winsound.Beep` arpeggio) and `play_stern_alert()` (low descending
  two-tone buzz) — both locally generated, no bundled/copyrighted audio,
  both subprocess-isolated and non-blocking like `speak()` (same crash
  rationale as the TTS fix above).
- `motivation.py` gained two categories: `CELEBRATION` (genuine "you did
  it" payoff) and `FELL_SHORT` (blunt, accountability-focused, not cruel —
  "you said you would, so finish it tomorrow" energy).
- `MainWindow._on_timer_finished` now asks *after* the completion dialog
  closes (needs the note first): the initial announce/dialog stays neutral
  ("How did it go?", no flavor spoiler), then once `assess_completion` has
  a verdict, the matching jingle/buzzer + motivation line plays. `UNCLEAR`
  gets no special audio — it doesn't guess-punish or guess-celebrate
  without real evidence in the note.

## Phase 4 — Intelligent Mentor (not started)

- Long-term memory / pattern analysis over the `tasks` table (e.g. with
  pandas): weak topics, consistency streaks, time-estimation accuracy.
- Personalized recommendations surfaced on the Dashboard or as periodic
  notifications.
- Likely needs a second table for mentor "insights" derived from analysis,
  separate from raw task history.

## Phase 5 — Advanced Features (optional, not started)

- LeetCode / GitHub activity integrations, productivity trend charts,
  AI-generated learning roadmap.

## Evaluation checklist (from idea.txt)

- [x] Runs as an independent desktop application
- [x] Does not require VS Code running
- [x] Runs in the background (tray) and provides notifications
- [x] Tracks tasks and sessions, stores progress permanently (SQLite)
- [x] Simple interface, easy morning planning, clear progress visualization
- [x] Minimal typing / voice interaction (Phase 3 — voice input for plans and progress updates)
- [x] Understands natural language schedules (Phase 2 — "Plan with AI")
- [x] Provides useful feedback ("Get Mentor Insight")
- [ ] Remembers previous progress in a mentor sense / identifies weak areas (deeper version in Phase 4)
- [x] Free/open-source technologies only (Groq free tier + free offline fallback, no paid services)
- [x] Easy to extend (service/module boundaries already in place for Phases 4-5)
