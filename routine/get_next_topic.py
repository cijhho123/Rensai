import json
import random
from pathlib import Path

ROUTINE_DIR = Path(__file__).parent
WEIGHTS_FILE = ROUTINE_DIR / "weights.json"
SCORES_FILE = ROUTINE_DIR / "scores.json"


def get_next_topic():
    weights = json.loads(WEIGHTS_FILE.read_text())
    scores = json.loads(SCORES_FILE.read_text()) if SCORES_FILE.exists() else {}

    effective = {topic: scores.get(topic, 0) for topic in weights}
    min_score = min(effective.values())
    candidates = [t for t, s in effective.items() if s == min_score]

    print(random.choice(candidates))


if __name__ == "__main__":
    get_next_topic()
