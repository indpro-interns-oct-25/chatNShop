"""
loader.py
Loads all keyword JSON files and returns them as structured dictionaries
for use in the intent classification pipeline.
"""

import json
import os
from typing import Dict, List

def load_keywords_from_file(file_path: str) -> Dict[str, List[dict]]:
    """Load a single keyword JSON file and return its contents."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Keyword file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid format in {file_path}: expected a dictionary")
    return data


def load_all_keywords(directory_path: str) -> Dict[str, List[dict]]:
    """Load all keyword JSON files (e.g. search, product, cart)."""
    keywords: Dict[str, List[dict]] = {}
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            data = load_keywords_from_file(file_path)
            for intent, patterns in data.items():
                keywords.setdefault(intent, []).extend(patterns)
    return keywords


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    all_keywords = load_all_keywords(base_dir)
    print(all_keywords)
