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

<<<<<<< HEAD



=======
# If this file is run directly, print loaded keywords
if __name__ == "__main__":
    keywords = load_keywords()
    print("Loaded keyword intents:")
    for intent, details in keywords.items():
        print(f"{intent} (priority {details.get('priority')}): {len(details.get('keywords', []))} keywords")
>>>>>>> bb04fb89da1ca2e218e03d0e0a616611a86ba595
