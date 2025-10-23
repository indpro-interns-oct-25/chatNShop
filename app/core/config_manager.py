# app/core/config_manager.py
import os
import yaml

# Resolve project root (folder that contains 'config')
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_MODELS_YAML = os.path.join(_PROJECT_ROOT, "config", "models.yaml")

def _load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def get_model_config(section: str):
    """
    Return a dict from config/models.yaml for the requested section,
    e.g., get_model_config("embedding").
    """
    data = _load_yaml(_MODELS_YAML)
    if section not in data:
        raise KeyError(f"Section '{section}' not found in {_MODELS_YAML}")
    return data[section]
