import json
import sys
from pathlib import Path

ROUTINE_DIR = Path(__file__).parent
WEIGHTS_FILE = ROUTINE_DIR / "weights.json"
SCORES_FILE = ROUTINE_DIR / "scores.json"


def update_topic_score(topic):
    weights = json.loads(WEIGHTS_FILE.read_text())
    scores = json.loads(SCORES_FILE.read_text()) if SCORES_FILE.exists() else {}

    if topic not in weights:
        print(f"Warning: '{topic}' not in weights.json", file=sys.stderr)
        return

    scores[topic] = scores.get(topic, 0) + weights[topic]
    SCORES_FILE.write_text(json.dumps(scores, indent=2))
    print(f"Updated {topic}: {scores[topic]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: update_topic_score.py <topic>", file=sys.stderr)
        sys.exit(1)
    update_topic_score(sys.argv[1])
