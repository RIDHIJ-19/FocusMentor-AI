"""Real quotes for notifications/dialogs, shown unattributed (just the line,
no name) -- per explicit request, sourced from well-established, widely-
verified quotes rather than invented. No Hindi lines, per request.
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
        "A year from now you'll wish you had started today.",
        "Procrastination is the thief of time.",
        "Amateurs sit and wait for inspiration; the rest of us just get up and go to work.",
        "Discipline is the bridge between goals and accomplishment.",
        "Don't count on motivation. Count on discipline.",
        "The secret of getting ahead is getting started.",
        "You don't have to see the whole staircase, just take the first step.",
        "Do the hard jobs first. The easy jobs will take care of themselves.",
        "What you do today can improve all your tomorrows.",
        "You have a right to your actions, but never to the fruits of your actions.",
    ],
    CHECKIN: [
        "If you're going through hell, keep going.",
        "It does not matter how slowly you go as long as you do not stop.",
        "Believe you can and you're halfway there.",
        "It always seems impossible until it's done.",
        "Well begun is half done.",
        "Fall seven times, stand up eight.",
        "The pain you feel today will be the strength you feel tomorrow.",
        "Act without attachment to the results, and stay steady through success and failure alike.",
        "A river cuts through rock not by force, but by persistence.",
    ],
    SESSION_COMPLETE: [
        "Well done is better than well said.",
        "Finish what you start and you gain confidence, skill, and a sense of accomplishment.",
        "Do what you can, with what you have, where you are.",
        "You don't have to be great to start, but you have to start to be great.",
        "Nothing is so fatiguing as the eternal hanging on of an uncompleted task.",
    ],
    CELEBRATION: [
        "Success is the sum of small efforts, repeated day in and day out.",
        "Well begun is half done.",
        "You don't have to be great to start, but you have to start to be great.",
        "Do what you can, with what you have, where you are.",
        "Whatever you are, be a good one.",
    ],
    FELL_SHORT: [
        "I can accept failure. Everyone fails at something. But I can't accept not trying.",
        "The only real mistake is the one from which we learn nothing.",
        "Failure is simply the opportunity to begin again, this time more intelligently.",
        "You may encounter many defeats, but you must not be defeated.",
        "I have not failed. I've just found 10,000 ways that won't work.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "You have a right to your actions, but never to the fruits of your actions.",
    ],
}

_last_index: Dict[str, int] = {}


def get_line(category: str) -> str:
    lines = _LINES.get(category)
    if not lines:
        return ""

    index = random.randrange(len(lines))
    # Re-roll until it's different from last time (bounded -- a 1-line
    # category would loop forever otherwise).
    for _ in range(len(lines)):
        if index != _last_index.get(category):
            break
        index = random.randrange(len(lines))

    _last_index[category] = index
    return lines[index]
