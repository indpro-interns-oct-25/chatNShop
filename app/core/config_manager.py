import json
import os
import time
import shutil
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
KEYWORDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'ai', 'intent_classification', 'keywords')
VERSIONS_DIR = os.path.join(CONFIG_DIR, "versions")
os.makedirs(VERSIONS_DIR, exist_ok=True)

# Global variable to store active configs and variant
CONFIG_CACHE = {}
ACTIVE_VARIANT = "A"  # Default variant (can be changed dynamically)

# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def load_json_config(file_path):
    """Safely load a JSON config file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ Skipping invalid JSON file {os.path.basename(file_path)}: {e}")
        return None


def save_version(file_path):
    """Backup old configuration with timestamp for version control."""
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_filename = f"{name}_{timestamp}{ext}"
    backup_path = os.path.join(VERSIONS_DIR, backup_filename)
    shutil.copy(file_path, backup_path)
    print(f"💾 Backup saved: {backup_filename}")


def get_variant_filename(base_name, variant):
    """Return filename for variant (e.g., keywords_A.json)."""
    name, ext = os.path.splitext(base_name)
    return f"{name}_{variant}{ext}"


# ------------------------------------------------------------
# Main Config Loading Logic
# ------------------------------------------------------------

def load_all_configs():
    """Load all configuration files based on the active variant."""
    global CONFIG_CACHE

    print(f"🔄 Loading configuration variant: {ACTIVE_VARIANT}")
    
    # Load rules and other config files from config/ directory
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(".json") and "_" not in filename:  # Base names only
            variant_file = get_variant_filename(filename, ACTIVE_VARIANT)
            variant_path = os.path.join(CONFIG_DIR, variant_file)

            # Fall back to base file if variant doesn't exist
            file_to_load = variant_path if os.path.exists(variant_path) else os.path.join(CONFIG_DIR, filename)

            data = load_json_config(file_to_load)
            if data:
                CONFIG_CACHE[filename.replace(".json", "")] = data
    
    # Load keywords from the actual keywords directory
    if os.path.exists(KEYWORDS_DIR):
        keywords_data = {}
        for filename in os.listdir(KEYWORDS_DIR):
            if filename.endswith(".json") and filename != "loader.py":
                file_path = os.path.join(KEYWORDS_DIR, filename)
                data = load_json_config(file_path)
                if data:
                    # Merge all keyword files into one
                    keywords_data.update(data)
        
        if keywords_data:
            CONFIG_CACHE["keywords"] = keywords_data

    print("✅ Configurations loaded successfully")


# ------------------------------------------------------------
# Hot Reload Handler
# ------------------------------------------------------------

class ConfigChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            save_version(event.src_path)
            load_all_configs()
            print(f"🔁 Config reloaded due to change: {event.src_path}")


def start_config_watcher():
    """Watch config directory for changes."""
    observer = Observer()
    handler = ConfigChangeHandler()
    observer.schedule(handler, CONFIG_DIR, recursive=False)
    observer.start()
    print("👀 Watching config directory for changes...")
    return observer


# ------------------------------------------------------------
# A/B Variant Control
# ------------------------------------------------------------

def switch_variant(variant: str):
    """Switch active configuration variant (A/B)."""
    global ACTIVE_VARIANT
    if variant.upper() not in ["A", "B"]:
        print("❌ Invalid variant. Use 'A' or 'B'.")
        return

    ACTIVE_VARIANT = variant.upper()
    print(f"🔁 Switched to configuration variant: {ACTIVE_VARIANT}")
    load_all_configs()


# ------------------------------------------------------------
# Initialize
# ------------------------------------------------------------

load_all_configs()
