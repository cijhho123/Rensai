import json
import random
from pathlib import Path

ROUTINE_DIR = Path(__file__).parent
TOPICS_FILE = ROUTINE_DIR / "topics.json"


def get_next_topic():
    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))

    min_score = min(t["score"] for t in topics.values())
    candidates = [slug for slug, t in topics.items() if t["score"] == min_score]

    slug = random.choice(candidates)
    t = topics[slug]
    types = t["type"] if isinstance(t["type"], list) else [t["type"]]

    print(slug)
    print(f"Name: {t['name']}")
    print(f"Types: {', '.join(types)}")


if __name__ == "__main__":
    get_next_topic()
