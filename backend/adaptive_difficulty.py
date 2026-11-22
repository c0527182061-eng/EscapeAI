
def update_difficulty(
    difficulty: int,
    success_streak: int,
    struggle_streak: int,
    attempts: int,
    hints_used: int,
    solve_time: float
) -> dict:

    # Did the player solve this puzzle easily?
    easy_success = (
        attempts == 1
        and hints_used == 0
        and solve_time <= 60
    )

    # Did the player struggle with this puzzle?
    struggled = (
        attempts >= 3
        or hints_used >= 2
    )

    if easy_success:
        success_streak += 1
        struggle_streak = 0

    elif struggled:
        struggle_streak += 1
        success_streak = 0

    else:
        success_streak = 0
        struggle_streak = 0

    # Increase difficulty after 2 easy successes
    if success_streak >= 2:
        difficulty = min(3, difficulty + 1)
        success_streak = 0

    # Decrease difficulty after 2 struggles
    if struggle_streak >= 2:
        difficulty = max(1, difficulty - 1)
        struggle_streak = 0

    return {
        "difficulty": difficulty,
        "success_streak": success_streak,
        "struggle_streak": struggle_streak
    }
