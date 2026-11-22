
from uuid import uuid4
from langgraph.types import Command
from game_graph import build_graph

graph = build_graph()

config = {
    "configurable": {
        "thread_id": str(uuid4())
    }
}

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
    "total_puzzles": 10,
    "completed_puzzles": 0,
    "used_puzzle_ids": [],
    "current_puzzle_id": "",
    "success_streak": 0,
    "struggle_streak": 0,
    "puzzle_start_time": 0,
    "last_solve_time": 0
}

print("\n===== ESCAPE AI =====")
print("ברוכה הבאה לחדר הבריחה!\n")

result = graph.invoke(initial_state, config=config)

while "__interrupt__" in result:

    request = result["__interrupt__"][0].value

    state_before = graph.get_state(config).values
    completed_before = state_before.get("completed_puzzles", 0)

    print(f"\nחדר {request['room_number']}")
    print(f"רמת קושי: {state_before['difficulty']}")
    print(f"חידה: {request['puzzle']}")

    answer = input("\nהתשובה שלך: ")

    result = graph.invoke(
        Command(resume=answer),
        config=config
    )

    state = graph.get_state(config).values

    print("\nAI:", state.get("feedback", ""))
    print("ניקוד:", state["score"])

    if state.get("completed_puzzles", 0) > completed_before:
        print("🔓 החידה נפתרה בהצלחה!")
        print(
            f"התקדמות: {state['completed_puzzles']}"
            f"/{state['total_puzzles']}"
        )

print("\n🎉 כל הכבוד! הצלחת לברוח!")
print("ניקוד סופי:", graph.get_state(config).values["score"])
