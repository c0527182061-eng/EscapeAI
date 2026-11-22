
from typing import TypedDict


class GameState(TypedDict):
    # Current room and difficulty
    room_number: int
    difficulty: int

    # Current puzzle
    puzzle: str
    correct_answer: str
    player_answer: str

    # Answer evaluation
    attempts: int
    hints_used: int
    is_correct: bool
    feedback: str

    # Game progress
    score: int
    game_finished: bool

    # Dynamic puzzle selection
    total_puzzles: int
    completed_puzzles: int
    used_puzzle_ids: list[str]
    current_puzzle_id: str

    # Adaptive difficulty
    success_streak: int
    struggle_streak: int

    # Performance tracking
    puzzle_start_time: float
    last_solve_time: float
