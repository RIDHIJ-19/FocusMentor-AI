# FocusMentor AI
## Link : https://focusmentor-ai.onrender.com
A personal AI mentor that plans your day, times your focus sessions,
checks in on you while you work, cuts down on drift/distraction, and judges
— using AI on your own words — whether you actually hit your goal. Built
incrementally per [idea.txt](idea.txt) (the original vision doc); see
[PLAN.md](PLAN.md) for the full architecture and phase-by-phase history.

**The web version (`web/`) is the primary, actively developed way to use
this app now.** The original Windows desktop app (`app/`) still exists in
this repo and still works, but is no longer being extended — see
[USAGE.md](USAGE.md) if you want to run it anyway.

## What it does

- **Plan your day in plain English (typed or spoken)** — "I want to spend 2
  hours on DSA, 3 hours on my AI project, and 1 hour reading research
  papers" becomes structured tasks automatically.
- **Times your sessions** with a live countdown, browser notifications, and
  spoken (Web Speech API) announcements.
- **Checks in on you mid-session** — a quick "how's it going?" prompt at a
  cadence that scales with the task length (roughly every quarter of the
  duration), not a fixed annoying interval.
- **Pause/Resume and Finish Early** — pause without losing time, or finish
  ahead of schedule and still get the full completion flow.
- **Need More Time** — didn't finish? Type or say "10 more minutes" instead
  of marking it done.
- **Judges your own completion note with AI** — hit your goal and you get a
  cheerful jingle + an upbeat line; fall short and you get a blunt, honest
  one instead. Works offline too, via a keyword-based fallback.
- **Remembers your session's history** — every check-in and completion
  reply is saved (Dashboard → Recent Updates), not just the last one.
- **Self-heals after a crash/restart** — a task stuck "in progress" past its
  own time gets automatically cleaned up on the next launch.

## Web version — quick start

**Requirements:** Python 3.10+

```powershell
python -m venv .venv
.venv\Scripts\pip install -r web/requirements.txt
.venv\Scripts\uvicorn web.main:app --reload
```

Open `http://127.0.0.1:8000`. AI features (natural-language planning, voice
input, mentor insight, completion judging) are optional and free — get a
key at [console.groq.com](https://console.groq.com) (no credit card), then
set it as the `GROQ_API_KEY` environment variable before starting the
server. Without a key, planning and completion judging fall back to free,
local, offline logic — nothing breaks.

For the full usage guide (check-ins, pause/resume, Need More Time,
Dashboard) see [USAGE.md](USAGE.md). For deploying this to a public URL
(Render, free tier), see the "Deploying" section in USAGE.md.

### Web project layout

- `web/main.py` — FastAPI app, mounts `static/`, wires up the routers
- `web/db.py` / `web/repository.py` — SQLite (session-scoped — see
  PLAN.md for why this resets on redeploy/restart, and why that's fine)
- `web/services/` — AI (Groq + free fallbacks), rule-based plan parser,
  motivation/flavor text — all ported from the desktop app's logic
- `web/routers/` — the JSON API (`/api/tasks/*`, `/api/dashboard`,
  `/api/insight`, `/api/transcribe`, `/api/motivation/*`)
- `web/static/` — the frontend: `index.html`, `style.css` (dark space
  theme), `app.js` (vanilla JS, no build step, no framework)

## Desktop app (superseded, still present)

The original Windows desktop app that this was built from — PySide6, system
tray, Windows notifications/TTS, local SQLite. See [USAGE.md](USAGE.md) for
how to run it if you want to.

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m app.main
```

## Data & privacy

**Web version:** data lives in a local SQLite file on the server process
(resets on redeploy/restart by design — see PLAN.md). The only outbound
network calls are to Groq's API, and only when AI features are used with a
key configured.

**Desktop version:** everything stored locally in `data/mentor.db` on your
machine, same network policy as above.
