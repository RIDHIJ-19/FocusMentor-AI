"""Short, original, punchy aphorisms for notifications/dialogs -- written in
the classic quotable-poster style (like "No pressure, no diamonds"), not
casual pep-talk. Original wording throughout.
"""
import random
from typing import Dict, List

SESSION_START = "session_start"
CHECKIN = "checkin"
SESSION_COMPLETE = "session_complete"
CELEBRATION = "celebration"
FELL_SHORT = "fell_short"

_LINES: Dict[str, List[str]] = {
    SESSION_START: [
        "No pressure, no diamonds.",
        "The best time to start was earlier. The next best time is now.",
        "Discipline is choosing what you want most over what you want now.",
        "Small steps, repeated daily, outrun big leaps taken rarely.",
        "You don't find time. You make it.",
        "Action is the antidote to doubt.",
        "Start before you're ready. Ready rarely comes first.",
        "Every expert was once exactly where you are right now.",
    ],
    CHECKIN: [
        "The middle is where most people quit. Don't.",
        "Persistence turns ordinary into extraordinary.",
        "A little progress each day adds up to big results.",
        "Discomfort today builds strength tomorrow.",
        "Keep going. Slow is still moving.",
        "The obstacle in front of you is also the way through.",
        "What feels hard now is what makes it worth finishing.",
        "Consistency beats intensity.",
    ],
    SESSION_COMPLETE: [
        "Well done is better than well said.",
        "Discipline is the bridge between goals and accomplishment.",
        "Every finished session is a vote for who you're becoming.",
        "Small wins, repeated, become identity.",
        "You showed up. That's how everything is built.",
        "Progress, not perfection — and that's exactly enough.",
        "The best view comes after the hardest climb.",
        "One more proof you keep your word to yourself.",
    ],
    CELEBRATION: [
        "Goal met. That's not luck, that's follow-through.",
        "You said you would, and you did. Remember this feeling.",
        "That's a finished thing. Most people never get here.",
        "Promise made, promise kept. Well earned.",
        "This is what it looks like when discipline pays off.",
        "You closed the loop. That's the whole game.",
        "Full marks. That's exactly how it's done.",
    ],
    FELL_SHORT: [
        "You said you'd finish this. You didn't. Fix that next time.",
        "Short of the goal today. Note it, don't repeat it.",
        "This one's unfinished. That's on the plan, not on your worth — go close it out.",
        "Falling short once is data. Falling short twice is a pattern. Choose.",
        "Not done. Say when it will be, and mean it.",
        "The goal was clear. The result wasn't there. Adjust and go again.",
        "Half a session isn't a finished one. Get back to it.",
        "You know what was promised. It didn't happen. Own it, then move.",
    ],
}

_last_index: Dict[str, int] = {}


def get_line(category: str) -> str:
    lines = _LINES.get(category)
    if not lines:
        return ""
    index = random.randrange(len(lines))
    if len(lines) > 1 and index == _last_index.get(category):
        index = (index + 1) % len(lines)
    _last_index[category] = index
    return lines[index]
