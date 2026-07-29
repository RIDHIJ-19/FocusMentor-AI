# Using FocusMentor AI

## Starting the app

```powershell
.venv\Scripts\python -m app.main
```

A window opens with three tabs: **🚀 Plan**, **📊 Dashboard**, **⚙️ Settings** —
dark space theme, subtle animated stars around the edges. A tray icon also
appears — the app keeps running there even if you close the window.

If the app was closed uncleanly last time (a crash, force-quit, or Quit
while a session was running), any task left stuck "in progress" past its
own time is automatically cleaned up on the next launch — you'll get a
notification listing what was removed, so it's never silent.

## Planning your day

1. Go to the **Plan** tab.
2. Click **+ Add Task**.
3. Fill in:
   - **Task name** — e.g. `DSA Practice`
   - **Goal** — e.g. `Complete Graph Algorithms` (optional)
   - **Duration** — how long the session should run
   - **Set a start time** — optional, for your own reference (the timer
     itself starts when you click Start, not automatically at that clock time)
4. Click OK. The task appears in today's list as `○ Not Started`.

Repeat for each task in your day's plan (DSA, project work, reading, etc.).

## Planning your day with AI (optional)

Instead of adding tasks one by one, click **Plan with AI** on the Plan tab
and describe your whole day in one go, e.g.:

> "I want to spend 2 hours on DSA, 3 hours on my AI project, and 1 hour
> reading research papers."

Click **Generate Tasks** — a checklist of parsed tasks appears (name,
duration, goal, start time if mentioned). Uncheck anything you don't want,
then click OK to add the rest to your plan.

You can also click **🎤 Record** instead of typing — speak your plan, click
**⏹ Stop**, and the transcribed text is dropped into the textarea for you to
review/edit before generating tasks. (Voice input requires a Groq API key —
see below; without one, typing still works exactly as described above.)

This works two ways:

- **Without a Groq API key configured** (see Settings below), it uses a
  free, fully offline pattern-matching parser — no signup, no internet
  needed, works out of the box.
- **With a Groq API key configured**, it sends your text to Groq's free LLM
  API for better natural-language understanding. If that call ever fails
  (offline, bad key, rate-limited), it automatically falls back to the
  offline parser instead of erroring out — the status message tells you
  exactly why (no key set, the AI request failed, or AI found no tasks).

### Setting up the free Groq API key (optional)

Get a free key at console.groq.com (no credit card required), then use
**one** of these two ways to give it to the app:

- **`.env` file (recommended if you'd rather not type it into the app):**
  copy `.env.example` (in the project folder) to a new file named `.env`,
  and paste your key after `GROQ_API_KEY=`. The app reads this file
  directly on every launch — it's never shown in the UI, never sent
  anywhere except to Groq, and is already excluded from git via
  `.gitignore`.
- **Settings tab:** paste it into **Groq API Key** and click **Save**. It's
  stored locally via Windows' per-user settings store (not in any project
  file).

If both are present, the `.env` file wins. The Settings tab shows which
source is currently active. "Plan with AI", "Get Mentor Insight", and voice
input (🎤 buttons) all use whichever key is active.

## Running a session

1. Select a task in the list.
2. Click **Start Selected**.
3. A live countdown appears below the list (and in the tray tooltip) —
   `MM:SS remaining`.
4. Only one session can run at a time; the task's status becomes `▶ In Progress`.

Finished before the clock runs out? Click **Finish Early** next to the
countdown — it triggers the exact same completion flow as a natural
timeout (sound, the "How did it go?" prompt, AI judging your note, the
matching jingle/buzzer). You don't lose that feedback just because you
beat the clock.

Need to step away mid-session? Click **Pause** — the countdown freezes
exactly where it is (no time lost) and the button becomes **Resume**.
Click it again to pick up right where you left off. Check-in timing isn't
thrown off by a pause either — it just picks up counting from where it
paused.

### Mid-session check-ins

For longer sessions, you'll get an announcement partway through (tray
notification + spoken aloud) — e.g. *"DSA Practice: 15 min in, 45 min left.
Still on track?"* — then the window comes forward with a **Quick Check-in**
prompt where you can type or **🎤 Record** a reply (or just click OK to skip
it). The timer keeps running underneath; nothing about the session is
paused. The cadence scales with the task so it stays useful instead of
annoying: it fires roughly every **quarter of the task's duration**
(duration ÷ 4), so a 1-hour task checks in every ~15 min and a 2-hour task
every ~30 min — always about 3 check-ins, however long the session is. Tasks
under 15 minutes don't get any. Turn check-ins on/off in **Settings**.

Every session-start, check-in, and completion announcement also includes a
short, original, confident one-liner (e.g. *"You're closer than you think.
Don't stop now."*) — spoken aloud along with the factual part, and shown in
magenta text in the popup itself.

## When a session finishes

- You'll hear a sound and get an announcement (tray notification + spoken
  aloud).
- The app window pops back up with **"How did it go?"** — type a quick note
  (e.g. *"Solved two binary search problems but struggled with identifying
  the search space"*), or click **🎤 Record** and speak it instead, then
  click OK.
- The task is marked `✓ Completed` with your note saved against it.
- Right after, the app judges from what you wrote whether you actually hit
  your goal (using AI if you have a Groq key, a keyword-based fallback
  otherwise) and responds accordingly:
  - **Hit your goal** → a cheerful ascending jingle + an upbeat line
    ("Goal met. That's not luck, that's follow-through.")
  - **Fell short** → a low stern buzz + a blunt, direct line ("You said
    you'd finish this. Fix that next time.")
  - **Note too vague to tell** (or left blank) → no special audio, just the
    normal completion sound from above.
  This only happens for the final note, not check-ins.

## Your reply history ("Recent Updates")

Every check-in reply and every session-complete note is saved, not just the
most recent one — go to the **Dashboard** tab's **Recent Updates** section to
see the last 14 days of them, newest first, e.g.:

```
[Jul 26 15:25] DSA Practice (checkin, 15m in): Going well, solved one problem so far.
[Jul 26 15:25] DSA Practice (complete): Finished, solved two graph problems.
```

This is a full timestamped log per task (not overwritten each time), so you
can look back at how a session actually went, not just how it ended.

## Checking your progress

Go to the **Dashboard** tab to see:

- **Today's Progress** — a percentage bar and a checklist of today's tasks.
- **Long-Term Progress** — total sessions completed all-time, and how many
  distinct days you've completed at least one session (a basic consistency
  indicator; richer streak/weak-area analysis comes in Phase 4).
- **Get Mentor Insight** — click this for a few sentences of coaching
  feedback based on your last 14 days of tasks and notes (AI-generated if a
  Groq key is set, otherwise a locally-computed summary of your completion
  rate and most recent update).

## Voice input

Both "Plan with AI" and the session-complete prompt have a **🎤 Record**
button:

1. Click it — it turns into **⏹ Stop** and starts listening.
2. Speak, then click **⏹ Stop**.
3. Your speech is transcribed (via Groq's free Whisper API) and dropped into
   the text box for you to review and edit before continuing.

Voice input requires a Groq API key (see above) — there's no offline speech
recognition in this app, since that would need heavy extra dependencies.
Without a key, the button tells you so instead of failing silently; typing
remains fully functional either way.

## Spoken announcements

Session-start, check-in, and session-complete messages are also **spoken
aloud** (offline text-to-speech, no internet needed) — not just shown as a
tray notification. Toggle this off in **Settings** ("Speak notifications
aloud") if you'd rather have silent tray notifications only.

## Settings

- **Start automatically when Windows starts** — toggle this in the
  **Settings** tab if you want the app to launch on login. It's off by
  default.

## Closing vs. quitting

- Clicking the window's **X** button just hides it to the tray — the app,
  your timer, and notifications keep working in the background.
- To fully quit: right-click the tray icon → **Quit**.

## Your data

All tasks and history live in `data/mentor.db` in the project folder. Nothing
leaves your machine. Deleting that file resets the app to a blank slate.

## Logs

The app writes a running log to `logs/app.log` in the project folder —
session starts, check-in firings, notifications, and any AI/voice errors,
each with a timestamp. Open it in any text editor if something seems off
(e.g. a notification you expected didn't show up); it rotates automatically
so it won't grow unbounded.
