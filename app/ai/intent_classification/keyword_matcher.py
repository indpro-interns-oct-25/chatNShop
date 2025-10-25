from .config_manager import ConfigManager

config = ConfigManager()
KEYWORDS = config.get_keywords()
def match_keywords(text):
    for intent, words in KEYWORDS.items():
        for word in words:
            if word in text.lower():
                return intent
    return "unknown"
