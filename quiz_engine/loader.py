# quiz_engine/loader.py

import json
import os

def load_question_banks(questions_dir: str) -> dict:
    banks = {}

    for file in os.listdir(questions_dir):
        if not file.endswith(".json"):
            continue

        path = os.path.join(questions_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            banks[file.replace(".json", "")] = json.load(f)

    return banks
