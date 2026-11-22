
from dotenv import load_dotenv
from langsmith import Client, evaluate

from answer_evaluator_v1 import evaluate_answer as evaluate_v1
from answer_evaluator_v2 import evaluate_answer as evaluate_v2

load_dotenv()

DATASET_NAME = "EscapeAI-Answer-Evaluation-V2"
# inputs + expected result
TEST_CASES = [
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "48", True),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "48?", True),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "אולי 48", True),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "נראה לי 48", True),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "התשובה היא 48", True),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "48 או 50", False),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "אולי 48 או 50", False),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "50", False),

    ("מה המספר הבא? 2, 6, 12, 20, 30, ?", "42", "42", True),
    ("מה המספר הבא? 2, 6, 12, 20, 30, ?", "42", "40 או 42", False),

    ("פענחי: DPEF", "CODE", "code?", True),
    ("פענחי: DPEF", "CODE", "CODE או CODD", False),
    ("פענחי: DPEF", "CODE", "CODD", False),

    ("איזה מתג נכון? A=4, B=6, C=7. בחרי מספר ראשוני.",
     "C", "C", True),
    ("איזה מתג נכון? A=4, B=6, C=7. בחרי מספר ראשוני.",
     "C", "A או C", False),

    ("מה הקוד הסופי?", "1342", "1342?", True),
    ("מה הקוד הסופי?", "1342", "1342 או 1242", False),
        # Numbers written as words
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "ארבעים ושמונה", True),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "forty eight", True),
    ("מה המספר הבא? 2, 6, 12, 20, 30, ?", "42", "ארבעים ושתיים", True),

    # Uncertainty with one answer
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "אולי ארבעים ושמונה?", True),

    # Multiple alternatives
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "48/50", False),
    ("מה המספר הבא? 3, 6, 12, 24, ?", "48", "48, 50", False),

    # Mixed Hebrew words and digits
    ("מה הקוד הסופי?", "1342", "אחד שלוש 4 שניים", True),
    ("מה הקוד הסופי?", "1342", "one three 4 two", True),

    # Incomplete or alternative access codes
    ("מה הקוד הסופי?", "1342", "אחד שלוש ארבע", False),
    ("מה הקוד הסופי?", "1342", "1342 או 1234", False),
]


client = Client()


def create_dataset():
    if client.has_dataset(dataset_name=DATASET_NAME):
        print("Dataset already exists.")
        return

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="EscapeAI answer correctness test cases"
    )

    for puzzle, correct_answer, player_answer, expected in TEST_CASES:
        client.create_example(
            dataset_id=dataset.id,
            inputs={
                "puzzle": puzzle,
                "correct_answer": correct_answer,
                "player_answer": player_answer
            },
            outputs={
                "is_correct": expected
            }
        )

    print(f"Created dataset with {len(TEST_CASES)} examples.")


def run_v1(inputs: dict) -> dict:
    result = evaluate_v1(
        puzzle=inputs["puzzle"],
        correct_answer=inputs["correct_answer"],
        player_answer=inputs["player_answer"]
    )
    return {
        "is_correct": result.is_correct,
        "feedback": result.feedback
    }


def run_v2(inputs: dict) -> dict:
    result = evaluate_v2(
        puzzle=inputs["puzzle"],
        correct_answer=inputs["correct_answer"],
        player_answer=inputs["player_answer"]
    )
    return {
        "is_correct": result.is_correct,
        "feedback": result.feedback
    }


def accuracy_evaluator(outputs: dict, reference_outputs: dict) -> dict:
    return {
        "key": "accuracy",
        "score": float(
            outputs["is_correct"] == reference_outputs["is_correct"]
        )
    }


if __name__ == "__main__":
    create_dataset()

    print("\nRunning BEFORE experiment...")
    before = evaluate(
        run_v1,
        data=DATASET_NAME,
        evaluators=[accuracy_evaluator],
        experiment_prefix="EscapeAI-V2-Before"    )

    print("\nRunning AFTER experiment...")
    after = evaluate(
        run_v2,
        data=DATASET_NAME,
        evaluators=[accuracy_evaluator],
        experiment_prefix="EscapeAI-V2-After"
    )

    print("\nBoth experiments completed.")
    print("Open LangSmith > Datasets & Experiments.")
