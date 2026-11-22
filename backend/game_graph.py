
import time

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver

from game_state import GameState
from puzzle_selector import select_puzzle, PUZZLES
from adaptive_difficulty import update_difficulty
from answer_evaluator_v2 import evaluate_answer


def load_room(state: GameState) -> dict:
    room_number = state["room_number"]
    difficulty = state["difficulty"]
    used_ids = state["used_puzzle_ids"]

    # First try the requested difficulty
    puzzle = select_puzzle(
        room_number, difficulty, used_ids
    )

    # Fallback to nearby difficulty levels
    if puzzle is None:
        for level in sorted(
            [1, 2, 3],
            key=lambda x: abs(x - difficulty)
        ):
            puzzle = select_puzzle(
                room_number, level, used_ids
            )
            if puzzle is not None:
                break

    if puzzle is None:
        raise ValueError(
            f"No available puzzles in room {room_number}"
        )

    return {
        "current_puzzle_id": puzzle["id"],
        "puzzle": puzzle["question"],
        "correct_answer": puzzle["correct_answer"],
        "used_puzzle_ids": used_ids + [puzzle["id"]],
        "player_answer": "",
        "attempts": 0,
        "hints_used": 0,
        "is_correct": False,
        "puzzle_start_time": time.time(),
        "last_solve_time": 0.0
    }


def wait_for_answer(state: GameState) -> dict:
    answer = interrupt({
        "room_number": state["room_number"],
        "puzzle_id": state["current_puzzle_id"],
        "puzzle": state["puzzle"],
        "message": "מה התשובה שלך?"
    })

    return {"player_answer": str(answer)}


def check_answer(state: GameState) -> dict:
    result = evaluate_answer(
        puzzle=state["puzzle"],
        correct_answer=state["correct_answer"],
        player_answer=state["player_answer"]
    )

    attempts = state["attempts"] + 1

    return {
        "is_correct": result.is_correct,
        "feedback": result.feedback,
        "attempts": attempts,
        "score": (
            state["score"] + 10*state["difficulty"]
            if result.is_correct
            else state["score"]
        )
    }



def route_answer(state: GameState) -> str:
    if state["is_correct"]:
        return "correct"

    puzzle = next(
        p for p in PUZZLES
        if p["id"] == state["current_puzzle_id"]
    )

    total_hints = len(puzzle["hints"])

    if (
        state["attempts"] % 2 == 0
        and state["hints_used"] < total_hints
    ):
        return "hint"

    return "incorrect"




def give_hint(state: GameState) -> dict:
    puzzle = next(
        p for p in PUZZLES
        if p["id"] == state["current_puzzle_id"]
    )

    hints = puzzle["hints"]
    index = state["hints_used"]

    if index >= len(hints):
        return {}

    return {
        "feedback": hints[index],
        "hints_used": index + 1
    }


def next_room(state: GameState) -> dict:
    solve_time = time.time() - state["puzzle_start_time"]

    adaptive = update_difficulty(
        difficulty=state["difficulty"],
        success_streak=state["success_streak"],
        struggle_streak=state["struggle_streak"],
        attempts=state["attempts"],
        hints_used=state["hints_used"],
        solve_time=solve_time
    )

    completed = state["completed_puzzles"] + 1

    if completed >= state["total_puzzles"]:
        return {
            **adaptive,
            "completed_puzzles": completed,
            "last_solve_time": solve_time,
            "game_finished": True
        }

    # Cycle through the five themed rooms
    next_number = (completed % 5) + 1

    return {
        **adaptive,
        "completed_puzzles": completed,
        "last_solve_time": solve_time,
        "room_number": next_number
    }


def route_game(state: GameState) -> str:
    if state["game_finished"]:
        return "finished"
    return "continue"


def build_graph():
    builder = StateGraph(GameState)

    builder.add_node("load_room", load_room)
    builder.add_node("wait_for_answer", wait_for_answer)
    builder.add_node("check_answer", check_answer)
    builder.add_node("next_room", next_room)
    builder.add_node("give_hint", give_hint)

    builder.add_edge(START, "load_room")
    builder.add_edge("load_room", "wait_for_answer")
    builder.add_edge("wait_for_answer", "check_answer")
    builder.add_edge("give_hint", "wait_for_answer")

    builder.add_conditional_edges(
        "check_answer",
        route_answer,
        {
            "correct": "next_room",
            "incorrect": "wait_for_answer",
            "hint": "give_hint"
        }
    )

    builder.add_conditional_edges(
        "next_room",
        route_game,
        {
            "finished": END,
            "continue": "load_room"
        }
    )

    checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)
