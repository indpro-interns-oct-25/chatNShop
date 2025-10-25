import json
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_DIR = os.path.dirname(__file__)
CONFIG_DATA = {}
_last_reload_time = {}  # 🆕 Track last reload per file


def load_all_configs():
    """Load all JSON configuration files."""
    global CONFIG_DATA
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CONFIG_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8-sig") as f:  # utf-8-sig handles BOM
                    CONFIG_DATA[filename.replace(".json", "")] = json.load(f)
                print(f"✅ Loaded config: {filename}")
            except json.JSONDecodeError as e:
                print(f"⚠️ Skipping invalid JSON file {filename}: {e}")
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    print("✅ Configurations loaded successfully")


class ConfigEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".json"):
            return

        filename = os.path.basename(event.src_path)
        now = time.time()
        last_time = _last_reload_time.get(filename, 0)

        # 🧠 Ignore changes happening within 1 second (debounce)
        if now - last_time < 1:
            return

        _last_reload_time[filename] = now
        print(f"🔁 Config reloaded due to change: {event.src_path}")
        load_all_configs()


def start_config_watcher():
    """Start watching configuration files for changes."""
    event_handler = ConfigEventHandler()
    observer = Observer()
    observer.schedule(event_handler, CONFIG_DIR, recursive=False)
    observer.start()
    print("👀 Watching configuration files for changes...")
