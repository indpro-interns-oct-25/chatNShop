import os
import json

# Path to the keywords folder (adjust if needed)
KEYWORDS_FOLDER = os.path.dirname(__file__)

def load_keywords():
    """
    Load all JSON files in the keywords folder and return a dictionary
    with intent categories and keywords.
    """
    all_keywords = {}

    # Iterate over all .json files in the folder
    for filename in os.listdir(KEYWORDS_FOLDER):
        if filename.endswith(".json"):
            filepath = os.path.join(KEYWORDS_FOLDER, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge into the main dictionary
                    all_keywords.update(data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return all_keywords

# If this file is run directly, print loaded keywords
if __name__ == "__main__":
    keywords = load_keywords()
    print("Loaded keyword intents:")
    for intent, details in keywords.items():
        print(f"{intent} (priority {details.get('priority')}): {len(details.get('keywords', []))} keywords")
