"""Real, attributed quotes for notifications/dialogs -- per explicit request,
swapped out from AI-generated lines. Each entry is "quote text" — source;
sourced from well-established, widely-verified attributions (classic
figures, and a couple of Bhagavad Gita verses) rather than invented.
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
        "A year from now you'll wish you had started today. — Karen Lamb",
        "Never do tomorrow what you can do today; procrastination is the thief of time. — Charles Dickens",
        "Amateurs sit and wait for inspiration; the rest of us just get up and go to work. — Stephen King",
        "Discipline is the bridge between goals and accomplishment. — Jim Rohn",
        "Don't count on motivation. Count on discipline. — Jocko Willink",
        "The secret of getting ahead is getting started. — Mark Twain",
        "You don't have to see the whole staircase, just take the first step. — Martin Luther King Jr.",
        "You have a right to perform your prescribed duty, but you are not entitled to the fruits of your actions. — Bhagavad Gita, 2.47",
    ],
    CHECKIN: [
        "If you are going through hell, keep going. — Winston Churchill",
        "It does not matter how slowly you go as long as you do not stop. — Confucius",
        "Believe you can and you're halfway there. — Theodore Roosevelt",
        "It always seems impossible until it's done. — Nelson Mandela",
        "Perform your duty equipoised, abandoning all attachment to success or failure. Such evenness of mind is called yoga. — Bhagavad Gita, 2.48",
        "Well begun is half done. — Aristotle",
        "Fall seven times, stand up eight. — Japanese proverb",
    ],
    SESSION_COMPLETE: [
        "Well done is better than well said. — Benjamin Franklin",
        "Finish what you start and you will gain confidence, skills, and a sense of accomplishment. — Tony Robbins",
        "Do what you can, with what you have, where you are. — Theodore Roosevelt",
        "You don't have to be great to start, but you have to start to be great. — Zig Ziglar",
        "Nothing is so fatiguing as the eternal hanging on of an uncompleted task. — William James",
    ],
    CELEBRATION: [
        "Success is the sum of small efforts, repeated day in and day out. — Robert Collier",
        "Finish what you start and you will gain confidence, skills, and a sense of accomplishment. — Tony Robbins",
        "Well begun is half done. — Aristotle",
        "You don't have to be great to start, but you have to start to be great. — Zig Ziglar",
        "Do what you can, with what you have, where you are. — Theodore Roosevelt",
    ],
    FELL_SHORT: [
        "I can accept failure. Everyone fails at something. But I can't accept not trying. — Michael Jordan",
        "The only real mistake is the one from which we learn nothing. — Henry Ford",
        "Failure is simply the opportunity to begin again, this time more intelligently. — Henry Ford",
        "You may encounter many defeats, but you must not be defeated. — Maya Angelou",
        "I have not failed. I've just found 10,000 ways that won't work. — Thomas Edison",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. — Winston Churchill",
        "You have a right to perform your prescribed duty, but you are not entitled to the fruits of your actions. — Bhagavad Gita, 2.47",
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
