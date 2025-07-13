from flask import Flask, request, render_template, jsonify
from collections import Counter
from datetime import datetime, date
import hashlib
import pytz
import random

app = Flask(__name__)

MIN_WORD_LEN = 3
PUZZLE_START_DATE = date(2025, 7, 12)

# Load valid words
with open('wordlist.txt') as f:
    VALID_WORDS = {
        w.strip().lower()
        for w in f
        if w.strip().isalpha() and len(w.strip()) >= MIN_WORD_LEN
    }

# Load all phrases
with open("puzzles.txt") as f:
    PUZZLES = [line.strip().upper() for line in f if line.strip()]

# Give-up message pool
GIVE_UP_MESSAGES = [
    "You gave it your best shot! There’s always tomorrow’s phrase.",
    "No shame in walking away — those last few letters were sneaky.",
    "You bowed out gracefully. Puzzle complete-ish!",
    "The phrase wins this round! But you'll get the next one.",
    "You waved the white flag 🏳️ … still a valiant effort!",
    "Puzzle: 1, You: still awesome.",
    "You surrendered — but we respect your strategic retreat.",
    "You’ve left a few letters on the table. A poetic mystery remains!",
    "Game over… or should we say: *Game, mostly solved?*",
    "Not quite a mic drop, but still a solid run."
]

def get_today():
    tz = pytz.timezone("America/Los_Angeles")
    return datetime.now(tz).date()

def get_today_date_string():
    return get_today().strftime("%A, %B %d, %Y")

def get_puzzle_number():
    return (get_today() - PUZZLE_START_DATE).days + 1

def get_daily_phrase():
    if not PUZZLES:
        return "ONCE IN A BLUE MOON"
    today = get_today()
    index = int(hashlib.sha256(today.isoformat().encode()).hexdigest(), 16) % len(PUZZLES)
    return PUZZLES[index]

DAILY_PHRASE = get_daily_phrase()
PHRASE_LETTERS = Counter(c for c in DAILY_PHRASE.lower() if c.isalpha())
PHRASE_WORDS = set(DAILY_PHRASE.lower().split())

@app.route('/')
def index():
    return render_template(
        'index.html',
        phrase=DAILY_PHRASE,
        date=get_today_date_string(),
        puzzle_number=get_puzzle_number()
    )

@app.route('/submit', methods=['POST'])
def submit_word():
    word = request.json.get('word', '').lower()

    if len(word) < MIN_WORD_LEN:
        return jsonify({'ok': False, 'message': 'Minimum three letters required.'})

    if word not in VALID_WORDS:
        return jsonify({'ok': False, 'message': 'Not a valid word.'})

    if word in PHRASE_WORDS:
        return jsonify({'ok': False, 'message': 'That word is part of the original phrase.'})

    word_letter_counts = Counter(word)
    for letter, count in word_letter_counts.items():
        if count > PHRASE_LETTERS.get(letter, 0):
            return jsonify({'ok': False, 'message': f"Letter '{letter}' not in phrase or overused."})

    return jsonify({'ok': True})

@app.route('/progress', methods=['POST'])
def progress():
    used = Counter()
    words = request.json.get('words', [])

    for w in words:
        used += Counter(w.lower())

    for l, cnt in used.items():
        if cnt > PHRASE_LETTERS.get(l, 0):
            return jsonify({'ok': False, 'message': f"Letter '{l}' overused."})

    total_letters = sum(PHRASE_LETTERS.values())
    used_letters = sum(min(cnt, PHRASE_LETTERS[l]) for l, cnt in used.items())
    percent = int(used_letters / total_letters * 100)

    if request.json.get("gave_up"):
        return jsonify({
            'ok': True,
            'gave_up': True,
            'message': random.choice(GIVE_UP_MESSAGES),
            'percent': percent,
            'used_letters': used_letters,
            'total_letters': total_letters
        })

    return jsonify({
        'ok': True,
        'percent': percent,
        'used_letters': used_letters,
        'total_letters': total_letters
    })
