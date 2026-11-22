
import json
import random
from pathlib import Path

PUZZLES_FILE = Path(__file__).resolve().parent / "puzzles.json"

with open(PUZZLES_FILE, encoding="utf-8") as file:
    PUZZLES = json.load(file)


def select_puzzle(
    room_id: int,
    difficulty: int,
    used_puzzle_ids: list[str]
) -> dict | None:

    available = [
        puzzle
        for puzzle in PUZZLES
        if puzzle["room_id"] == room_id
        and puzzle["difficulty"] == difficulty
        and puzzle["id"] not in used_puzzle_ids
    ]

    if not available:
        return None

    return random.choice(available)
