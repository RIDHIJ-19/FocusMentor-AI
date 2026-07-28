"""Groq-backed natural language plan parsing and progress insights.

Free tier, no credit card (console.groq.com). Falls back to fully local,
offline processing whenever no API key is configured or the API call fails
for any reason, so the app never depends on the AI being available.
"""
import json
import logging
import re
from collections import Counter
from typing import List, Optional

import requests

from app.config import STATUS_COMPLETED
from app.models.task import Task
from app.services import rule_based_parser, settings_service

logger = logging.getLogger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_GROQ_MODEL = "llama-3.1-8b-instant"
_GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"
_TIMEOUT_SECONDS = 15

_PARSE_SYSTEM_PROMPT = """You turn a person's spoken-out-loud daily plan into a JSON list of tasks.
Return ONLY a JSON array, no prose, no markdown fences. Each item must have exactly these keys:
"name" (short task title, string), "goal" (a short specific goal for the session, string or null),
"duration_min" (integer minutes), "start_time" ("HH:MM" 24-hour string, or null if not mentioned).
If the input mentions no tasks, return [].

Create ONE task per distinct time block or activity the person describes, not one task per
sub-item within it. A count of problems/pages/reps/chapters inside a single activity (e.g.
"solve 4 DSA questions in one hour") describes ONE task's goal and quantity -- put "solve 4 DSA
questions" in "goal" with duration_min=60, do NOT split it into 4 separate 15-minute tasks. Only
create multiple tasks when the person names multiple distinct activities and/or separate time
allocations (e.g. "2 hours on DSA and 1 hour reading" -> 2 tasks)."""

_INSIGHT_SYSTEM_PROMPT = """You are a supportive but honest personal learning mentor. Given a summary
of someone's recent task sessions (name, goal, status, and their own notes), write 3-5 sentences of
specific, actionable coaching feedback: call out patterns like weak areas, consistency, or
time-estimation accuracy. Be concrete and reference specifics from the notes when possible. Do not
use markdown formatting."""

_ASSESS_SYSTEM_PROMPT = """You judge whether someone hit the goal of a work session, from their own
end-of-session note. You will be given the task name, its goal (if any), and the note they wrote or
spoke about how it went. Reply with EXACTLY ONE WORD, nothing else:
"success" if they clearly completed the goal, "shortfall" if they clearly fell short of it (ran out
of time, only did part of it, didn't get to it, struggled and didn't finish), or "unclear" if the
note doesn't give enough information to tell either way. When genuinely ambiguous, prefer "unclear"
over guessing."""

SUCCESS = "success"
SHORTFALL = "shortfall"
UNCLEAR = "unclear"
_VALID_VERDICTS = {SUCCESS, SHORTFALL, UNCLEAR}

_POSITIVE_MARKERS = (
    "done", "finished", "completed", "solved", "all of it", "all done",
    "nailed it", "crushed it", "finished all", "got through all",
)
_NEGATIVE_MARKERS = (
    "didn't", "did not", "couldn't", "could not", "only", "not able",
    "behind", "ran out of time", "out of time", "failed", "struggled",
    "skip", "skipped", "gave up", "didn't finish", "not much",
)


class AIResult:
    def __init__(self, tasks: List[dict], used_ai: bool, fallback_reason: Optional[str] = None):
        self.tasks = tasks
        self.used_ai = used_ai
        self.fallback_reason = fallback_reason  # None when used_ai is True


class AIService:
    def parse_plan_text(self, text: str) -> AIResult:
        api_key = settings_service.get_api_key()
        if not api_key:
            return AIResult(rule_based_parser.parse(text), used_ai=False, fallback_reason="no_key")

        try:
            content = self._call_groq(api_key, _PARSE_SYSTEM_PROMPT, text)
            tasks = self._extract_json_array(content)
            normalized = [self._normalize_task(t) for t in tasks]
            normalized = [t for t in normalized if t is not None]
            if not normalized:
                return AIResult(rule_based_parser.parse(text), used_ai=False, fallback_reason="empty")
            return AIResult(normalized, used_ai=True)
        except Exception as exc:
            logger.warning("Groq parse_plan_text failed, falling back: %s", exc)
            return AIResult(rule_based_parser.parse(text), used_ai=False, fallback_reason=str(exc))

    def generate_insight(self, recent_tasks: List[Task]) -> str:
        api_key = settings_service.get_api_key()
        if not api_key or not recent_tasks:
            return self._local_insight(recent_tasks)

        summary_lines = []
        for t in recent_tasks:
            line = f"- [{t.plan_date}] {t.name} (goal: {t.goal or 'n/a'}) - status: {t.status}"
            if t.notes:
                line += f" - notes: {t.notes}"
            summary_lines.append(line)
        user_content = "Recent sessions:\n" + "\n".join(summary_lines)

        try:
            return self._call_groq(api_key, _INSIGHT_SYSTEM_PROMPT, user_content).strip()
        except Exception as exc:
            logger.warning("Groq generate_insight failed, falling back: %s", exc)
            return self._local_insight(recent_tasks)

    def assess_completion(self, task_name: str, goal: Optional[str], note: str) -> str:
        """Returns SUCCESS, SHORTFALL, or UNCLEAR, judged from the user's own
        end-of-session note. Never guesses off an empty note."""
        note = (note or "").strip()
        if not note:
            return UNCLEAR

        api_key = settings_service.get_api_key()
        if not api_key:
            return self._local_assess(note)

        try:
            user_content = f"Task: {task_name}\nGoal: {goal or 'n/a'}\nNote: {note}"
            verdict = self._call_groq(api_key, _ASSESS_SYSTEM_PROMPT, user_content)
            verdict = verdict.strip().lower()
            return verdict if verdict in _VALID_VERDICTS else UNCLEAR
        except Exception as exc:
            logger.warning("Groq assess_completion failed, falling back: %s", exc)
            return self._local_assess(note)

    def transcribe_audio(self, wav_bytes: bytes) -> Optional[str]:
        """Returns transcribed text, or None if no API key or the call fails."""
        api_key = settings_service.get_api_key()
        if not api_key or not wav_bytes:
            return None
        try:
            response = requests.post(
                _GROQ_TRANSCRIBE_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": ("recording.wav", wav_bytes, "audio/wav")},
                data={"model": _GROQ_WHISPER_MODEL},
                timeout=30,
            )
            response.raise_for_status()
            text = response.json().get("text", "").strip()
            return text or None
        except Exception as exc:
            logger.warning("Groq transcribe_audio failed: %s", exc)
            return None

    # ---------- internals ----------

    def _call_groq(self, api_key: str, system_prompt: str, user_content: str) -> str:
        payload = {
            "model": _GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }
        response = requests.post(
            _GROQ_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _extract_json_array(self, content: str) -> list:
        match = re.search(r"\[.*\]", content, re.DOTALL)
        raw = match.group(0) if match else content
        return json.loads(raw)

    def _normalize_task(self, raw) -> Optional[dict]:
        if not isinstance(raw, dict):
            return None
        name = str(raw.get("name") or "").strip()
        if not name:
            return None
        try:
            duration_min = int(raw.get("duration_min") or 30)
        except (TypeError, ValueError):
            duration_min = 30
        start_time = raw.get("start_time") or None
        goal = raw.get("goal") or None
        return {
            "name": name,
            "goal": goal,
            "duration_min": max(duration_min, 1),
            "start_time": start_time,
        }

    def _local_assess(self, note: str) -> str:
        lowered = note.lower()
        has_positive = any(marker in lowered for marker in _POSITIVE_MARKERS)
        has_negative = any(marker in lowered for marker in _NEGATIVE_MARKERS)
        if has_positive and not has_negative:
            return SUCCESS
        if has_negative and not has_positive:
            return SHORTFALL
        return UNCLEAR

    def _local_insight(self, recent_tasks: List[Task]) -> str:
        if not recent_tasks:
            return "No recent sessions yet -- add and complete a few tasks to get insights."

        total = len(recent_tasks)
        completed = [t for t in recent_tasks if t.status == STATUS_COMPLETED]
        completion_rate = round(len(completed) / total * 100)

        name_counts = Counter(t.name for t in recent_tasks)
        top_task = name_counts.most_common(1)[0][0] if name_counts else "your tasks"

        lines = [
            f"You completed {len(completed)} of {total} recent sessions ({completion_rate}%).",
            f"Your most frequent focus area recently has been '{top_task}'.",
        ]
        notes = [t.notes for t in completed if t.notes]
        if notes:
            lines.append(f"Latest update: \"{notes[-1]}\"")
        lines.append(
            "Add a free Groq API key in Settings for personalized, AI-generated coaching feedback."
        )
        return " ".join(lines)
