
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langgraph.types import Command
from fastapi.middleware.cors import CORSMiddleware
from game_graph import build_graph
from puzzle_selector import PUZZLES
from rooms import ROOMS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

PUZZLES_BY_ID = {
    puzzle["id"]: puzzle
    for puzzle in PUZZLES
}


class StartRequest(BaseModel):
    total_puzzles: int = Field(default=5, ge=5, le=15)


class AnswerRequest(BaseModel):
    session_id: str
    answer: str


class SessionRequest(BaseModel):
    session_id: str


def get_config(session_id: str):
    return {
        "configurable": {
            "thread_id": session_id
        }
    }


def get_snapshot(session_id: str):
    snapshot = graph.get_state(get_config(session_id))

    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="המשחק לא נמצא"
        )

    return snapshot


def format_game(
    session_id: str,
    feedback: str = "",
    hint: str = "",
    correct: bool = False
):
    snapshot = get_snapshot(session_id)
    state = snapshot.values

    number = state.get("room_number", 1)
    room = ROOMS.get(number, {})

    puzzle_id = state.get("current_puzzle_id", "")
    puzzle = PUZZLES_BY_ID.get(puzzle_id, {})

    finished = state.get("game_finished", False)

    return {
        "session_id": session_id,
        "finished": finished,
        "room_number": number,
        "room_name": room.get("name", "היציאה"),
        "theme": room.get("theme", "laboratory"),

        "puzzle_id": puzzle_id,
        "puzzle": "" if finished else state.get("puzzle", ""),
        "category": puzzle.get("category", ""),
        "difficulty": state.get("difficulty", 1),
        "puzzle_difficulty": puzzle.get("difficulty", 1),

        "total_rooms": len(ROOMS),
        "total_puzzles": state.get("total_puzzles", 5),
        "completed_puzzles": state.get("completed_puzzles", 0),

        "score": state.get("score", 0),
        "attempts": state.get("attempts", 0),
        "hints_used": state.get("hints_used", 0),

        "feedback": feedback,
        "hint": hint,
        "last_answer_correct": correct,
        "waiting_for_answer": (
            not finished and bool(snapshot.next)
        )
    }


@app.post("/api/game/start")
def start_game(data: StartRequest):
    session_id = str(uuid4())

    initial_state = {
        "room_number": 1,
        "difficulty": 1,

        "puzzle": "",
        "correct_answer": "",
        "player_answer": "",

        "attempts": 0,
        "hints_used": 0,
        "score": 0,
        "is_correct": False,
        "game_finished": False,
        "feedback": "",

        "total_puzzles": data.total_puzzles,
        "completed_puzzles": 0,
        "used_puzzle_ids": [],
        "current_puzzle_id": "",

        "success_streak": 0,
        "struggle_streak": 0,

        "puzzle_start_time": 0.0,
        "last_solve_time": 0.0
    }

    graph.invoke(
        initial_state,
        config=get_config(session_id)
    )

    return format_game(session_id)


@app.post("/api/game/answer")
def answer_game(data: AnswerRequest):
    snapshot = get_snapshot(data.session_id)

    if not snapshot.next:
        raise HTTPException(
            status_code=409,
            detail="המשחק כבר הסתיים"
        )

    if not data.answer.strip():
        raise HTTPException(
            status_code=400,
            detail="יש להזין תשובה"
        )

    old_state = snapshot.values
    old_completed = old_state.get("completed_puzzles", 0)
    old_hints = old_state.get("hints_used", 0)

    graph.invoke(
        Command(resume=data.answer),
        config=get_config(data.session_id)
    )

    state = get_snapshot(data.session_id).values

    correct = (
        state.get("completed_puzzles", 0) > old_completed
    )

    hint = ""

    if not correct and state.get("hints_used", 0) > old_hints:
        hint = state.get("feedback", "")

    return format_game(
        data.session_id,
        feedback=(
        "כל הכבוד! פתרת את החידה בהצלחה."
        if correct
        else state.get("feedback", "")
        ),
        hint=hint,
        correct=correct
    )


@app.post("/api/game/state")
def game_state(data: SessionRequest):
    return format_game(data.session_id)
