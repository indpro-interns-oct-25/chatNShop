# Versions Folder

This folder stores automatically backed-up versions of configuration files.

Whenever a configuration file such as `keywords.json`, `thresholds.json`, or `rules.json` is updated,
a timestamped copy is saved here. This provides **version control** for configuration changes
without requiring Git commits.

Each backup follows the format:

<config_name>_<YYYYMMDD-HHMMSS>.json