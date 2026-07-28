# FocusMentor AI

A personal desktop AI mentor that plans your day, times your focus sessions,
checks in on you while you work, cuts down on drift/distraction, and judges
— using AI on your own words — whether you actually hit your goal. Built
incrementally per [idea.txt](idea.txt) (the original vision doc); see
[PLAN.md](PLAN.md) for the full architecture and phase-by-phase history.

## What it does

- **Plan your day in plain English (typed or spoken)** — "I want to spend 2
  hours on DSA, 3 hours on my AI project, and 1 hour reading research
  papers" becomes structured tasks automatically.
- **Times your sessions** with a live countdown, tray notifications, and
  spoken (offline TTS) announcements.
- **Checks in on you mid-session** — a quick "how's it going?" prompt at a
  cadence that scales with the task length (roughly every quarter of the
  duration), not a fixed annoying interval.
- **Finish early?** One click triggers the same completion flow as running
  out the clock — you're not penalized for beating the timer.
- **Judges your own completion note with AI** — hit your goal and you get a
  cheerful jingle + an upbeat line; fall short and you get a blunt, honest
  one instead. Works offline too, via a keyword-based fallback.
- **Remembers everything** — every check-in and completion reply is saved
  to a full history (Dashboard → Recent Updates), not just the last one.
- **Self-heals after a crash or force-quit** — a task stuck "in progress"
  past its own time gets automatically cleaned up on the next launch.
- **Runs quietly in the background** — minimizes to the system tray instead
  of closing, optional launch-on-startup.

## Requirements

- Windows 10/11
- Python 3.10+

## Setup

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

AI features (natural-language planning, voice input, mentor insight,
completion judging) are optional and free — get a key at
[console.groq.com](https://console.groq.com) (no credit card), then either:

- copy `.env.example` to `.env` and paste your key there (recommended), or
- paste it into the app's Settings tab instead.

Without a key, the app still works fully — natural-language parsing and
completion judging fall back to free, local, offline logic.

## Running the app

```powershell
.venv\Scripts\python -m app.main
```

The app window opens, and an icon appears in the system tray. Closing the
window (the X button) minimizes it to the tray rather than quitting — use
the tray icon's right-click menu → **Quit** to actually exit.

For the full day-to-day usage guide, see [USAGE.md](USAGE.md).

## Project layout

See [PLAN.md](PLAN.md) for the full architecture writeup. In short:

- `app/main.py` — entry point + logging setup
- `app/db/` — SQLite connection, `TaskRepository`, `UpdateRepository`
- `app/models/` — `Task` and `Update` data models
- `app/services/` — timer, AI (Groq + free fallbacks), voice, notifications,
  motivation/flavor text, settings, autostart
- `app/ui/` — the PySide6 windows/widgets/dialogs, dark space theme
- `data/mentor.db` — your local database (created on first run, gitignored)
- `logs/app.log` — rotating log file (gitignored)

## Data & privacy

Everything is stored locally in `data/mentor.db` on your machine. The only
network calls are to Groq's API, and only when AI features are used with a
key configured — nothing is sent anywhere otherwise.
