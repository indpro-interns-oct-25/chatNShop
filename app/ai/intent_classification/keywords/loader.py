import os
import json

def load_all_keywords(keywords_dir=None):   # ✅ add optional parameter
    if keywords_dir is None:
        keywords_dir = os.path.dirname(__file__)   # default to current folder

    all_keywords = {}

    for file_name in os.listdir(keywords_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(keywords_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        all_keywords.update(data)
                    else:
                        print(f"⚠️ Skipping invalid JSON file: {file_name}")
            except Exception as e:
                print(f"⚠️ Skipping invalid JSON file: {file_name} ({e})")

    return all_keywords




