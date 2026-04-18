import json
import sys
from pathlib import Path

ROUTINE_DIR = Path(__file__).parent
TOPICS_FILE = ROUTINE_DIR / "topics.json"


def update_topic_score(slug):
    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))

    if slug not in topics:
        topics[slug] = {"name": slug.replace("-", " ").title(), "type": ["anime"], "weight": 100, "score": 0}
        print(f"Added new topic '{slug}' with default values")

    topics[slug]["score"] += topics[slug]["weight"]
    TOPICS_FILE.write_text(json.dumps(topics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {slug}: score={topics[slug]['score']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: update_topic_score.py <slug>", file=sys.stderr)
        sys.exit(1)
    update_topic_score(sys.argv[1])
