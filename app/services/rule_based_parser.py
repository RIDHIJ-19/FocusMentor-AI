"""Free, offline, dependency-free parser for natural-language daily plans.

Used directly when no AI API key is configured, and as the fallback when
the AI call fails for any reason (offline, bad key, rate limit).

Handles the phrasings idea.txt gives as examples:
    "I want to spend 2 hours on DSA, 3 hours on my AI project, and 1 hour
    reading research papers."
    "I will do graphs in DSA from 8 AM to 10 AM."
"""
import re
from typing import List, Optional, TypedDict

_FILLER_PREFIXES = [
    r"^i want to spend\s+",
    r"^i will do\s+",
    r"^i will\s+",
    r"^i'll do\s+",
    r"^i plan to\s+",
    r"^spend\s+",
    r"^do\s+",
]

_FILLER_PHRASES = [
    r"\bfor the next\b",
    r"\bthe next\b",
]

_HALF_HOUR_RE = re.compile(r"\bhalf(?:\s+an?)?\s+hour\b", re.IGNORECASE)

_NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

_WORD_NUMBER_DURATION_RE = re.compile(
    r"\b(" + "|".join(_NUMBER_WORDS) + r")\b(\s*)(hours?|hrs?|h\b|minutes?|mins?|m\b)",
    re.IGNORECASE,
)

_DURATION_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h\b|minutes?|mins?|m\b)", re.IGNORECASE
)

_TIME_RANGE_RE = re.compile(
    r"from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|–)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
    re.IGNORECASE,
)

_ON_FOR_RE = re.compile(r"\b(on|for|doing)\b", re.IGNORECASE)


class ParsedTask(TypedDict):
    name: str
    goal: Optional[str]
    duration_min: int
    start_time: Optional[str]


def _to_minutes(amount: float, unit: str) -> int:
    unit = unit.lower()
    if unit.startswith("h"):
        return round(amount * 60)
    return round(amount)


def _parse_clock(text: str) -> Optional[str]:
    text = text.strip().lower()
    match = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)
    if meridiem == "pm" and hour != 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    hour = hour % 24
    return f"{hour:02d}:{minute:02d}"


def _numbers_to_digits(text: str) -> str:
    text = _HALF_HOUR_RE.sub("30 minutes", text)

    def repl(match: "re.Match") -> str:
        number = _NUMBER_WORDS[match.group(1).lower()]
        return f"{number}{match.group(2)}{match.group(3)}"

    return _WORD_NUMBER_DURATION_RE.sub(repl, text)


def _split_clauses(text: str) -> List[str]:
    parts = re.split(r",|\band\b", text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


def _clean_name(clause: str) -> str:
    name = clause
    for pattern in _FILLER_PREFIXES:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    name = _DURATION_RE.sub("", name)
    name = _TIME_RANGE_RE.sub("", name)
    for pattern in _FILLER_PHRASES:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    name = _ON_FOR_RE.sub("", name)
    name = re.sub(r"\s{2,}", " ", name).strip(" .")
    if not name:
        return "Task"
    return name[0].upper() + name[1:]


def parse(text: str) -> List[ParsedTask]:
    text = _numbers_to_digits(text)
    tasks: List[ParsedTask] = []
    for clause in _split_clauses(text):
        duration_match = _DURATION_RE.search(clause)
        time_match = _TIME_RANGE_RE.search(clause)

        duration_min = None
        start_time = None

        if time_match:
            start_time = _parse_clock(time_match.group(1))
            end_time = _parse_clock(time_match.group(2))
            if start_time and end_time:
                sh, sm = map(int, start_time.split(":"))
                eh, em = map(int, end_time.split(":"))
                delta = (eh * 60 + em) - (sh * 60 + sm)
                if delta > 0:
                    duration_min = delta

        if duration_match:
            duration_min = _to_minutes(float(duration_match.group(1)), duration_match.group(2))

        if duration_min is None and start_time is None:
            continue  # no time signal in this clause -- skip rather than guess

        name = _clean_name(clause)
        tasks.append(
            ParsedTask(
                name=name,
                goal=None,
                duration_min=duration_min or 30,
                start_time=start_time,
            )
        )

    return tasks
