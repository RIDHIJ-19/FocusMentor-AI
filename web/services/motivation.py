"""Short, original lines for notifications/dialogs -- sarcastic/witty voice
(dry, a little teasing) rather than earnest pep-talk. Original wording
throughout, no borrowed quotes.
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
        "Look who showed up. Don't let it go to your head.",
        "Starting the timer. Your phone is already plotting its comeback.",
        "Bold of you to commit to this in writing.",
        "Clock's running. Pretend that's motivating.",
        "New session, same you, allegedly improved.",
        "Let's see how long the enthusiasm lasts this time.",
        "You against the timer. The timer isn't nervous.",
        "Officially your problem now. Go.",
    ],
    CHECKIN: [
        "Still here? Suspicious, but I'll allow it.",
        "Checking in — no, that tab you opened doesn't count as progress.",
        "You're not bored, you're 'pacing yourself.' Sure.",
        "Halfway-ish. Heroic. Truly.",
        "This is the part where most people 'just check their phone real quick.' Don't.",
        "Still going? Color me mildly impressed.",
        "Plot twist: the work doesn't finish itself. Carry on.",
        "Statistically, you're closer to done than to giving up. Use that.",
        "No trophy for this check-in. Keep typing anyway.",
        "You've survived worse. Probably. Keep going.",
        "This is your reminder that quitting is more effort than finishing.",
        "The remaining time isn't getting shorter by staring at it.",
    ],
    SESSION_COMPLETE: [
        "Timer's up. Confess: how much of that was actual work?",
        "Done, or 'done'? Be honest with the notes field.",
        "Session over. The couch has been asking about you.",
        "That's a wrap. Try not to sound too surprised you finished.",
        "You survived contact with your own to-do list. Rare.",
        "Session closed. History will remember this modestly.",
        "Time's up — spill it, how'd it actually go.",
    ],
    CELEBRATION: [
        "You actually did the thing. Mark the occasion.",
        "Goal met. Even your future self is a little impressed.",
        "Look at you, following through like it's easy.",
        "Called it done, and it's actually done. Rare combo.",
        "That's a finished thing. Frame it, briefly, then move on.",
        "Receipts secured. You said it, you did it.",
        "Suspiciously competent performance today.",
    ],
    FELL_SHORT: [
        "Didn't quite land it. The goal remains undefeated — for now.",
        "Short of the target. It happens. Fix it, don't narrate it.",
        "Unfinished business. Very dramatic. Also very fixable.",
        "That goal is still out there, mocking you gently.",
        "Not done. Say when, actually mean it this time.",
        "The plan said one thing, reality said another. Reality wins today.",
        "Half a session logged as a win is how habits quietly die. Don't.",
        "It didn't happen. Noted, not judged. Go again.",
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
