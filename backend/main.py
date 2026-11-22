
from langgraph.types import Command
from game_graph import build_graph

graph = build_graph()

config = {
    "configurable": {
        "thread_id": "player-1"
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
    "feedback": ""
}

result = graph.invoke(
    initial_state,
    config=config
)

while "__interrupt__" in result:
    request = result["__interrupt__"][0].value

    print("\nחדר:", request["room_number"])
    print("חידה:", request["puzzle"])

    answer = input("התשובה שלך: ")

    previous_room = request["room_number"]

    result = graph.invoke(
        Command(resume=answer),
        config=config
    )

    current_state = graph.get_state(config).values

    print("\nAI:", current_state["feedback"])
    print("ניקוד:", current_state["score"])

    if current_state["is_correct"]:
        print(f"פתרת את חדר {previous_room}!")

print("\nכל הכבוד! הצלחת לברוח מהמעבדה!")
