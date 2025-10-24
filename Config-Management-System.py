"""
Config Management Service
Single-file implementation for local development.

Features:
- Load configuration from YAML/JSON files or SQLite (file-based DB)
- Hot-reload when files change (watchdog)
- Versioning: each save creates a version entry in SQLite and persists a timestamped file copy
- A/B testing: supports assigning variant based on weights or request header
- Simple FastAPI HTTP API for managing configs and querying

Install dependencies:
    pip install fastapi uvicorn pyyaml watchdog aiofiles sqlalchemy

Run:
    python config-management-system.py

Endpoints:
- GET  /configs/{name} -> returns active config (optionally specify variant via header)
- POST /configs/{name} -> upload config JSON/YAML (body) and create a new version
- GET  /configs/{name}/versions -> list versions
- POST /configs/{name}/activate -> activate a specific version
- GET  /configs/list -> list available configs

This is a compact implementation meant as a starting point.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import yaml
import json
import os
import shutil
import time
from datetime import datetime
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sqlite3
import uuid

# -------------------- Configuration --------------------
CONFIG_DIR = os.path.abspath("./configs")
VERSIONS_DIR = os.path.join(CONFIG_DIR, "_versions")
DB_PATH = os.path.join(CONFIG_DIR, "config_versions.db")
HOT_RELOAD = True
SUPPORTED_EXT = (".yaml", ".yml", ".json")

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(VERSIONS_DIR, exist_ok=True)

# -------------------- Persistence / Versioning --------------------
class VersionStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS versions (
                id TEXT PRIMARY KEY,
                config_name TEXT NOT NULL,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS active (
                config_name TEXT PRIMARY KEY,
                version_id TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def add_version(self, config_name: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        vid = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO versions (id, config_name, filename, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
            (vid, config_name, filename, created_at, json.dumps(metadata or {})),
        )
        conn.commit()
        conn.close()
        return vid

    def list_versions(self, config_name: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, filename, created_at, metadata FROM versions WHERE config_name = ? ORDER BY created_at DESC", (config_name,))
        rows = c.fetchall()
        conn.close()
        return [ {"id": r[0], "filename": r[1], "created_at": r[2], "metadata": json.loads(r[3])} for r in rows ]

    def set_active(self, config_name: str, version_id: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("REPLACE INTO active (config_name, version_id) VALUES (?, ?)", (config_name, version_id))
        conn.commit()
        conn.close()

    def get_active(self, config_name: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT version_id FROM active WHERE config_name = ?", (config_name,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

version_store = VersionStore()

# -------------------- Config Loader & Hot Reload --------------------
class ConfigManager:
    def __init__(self, config_dir=CONFIG_DIR):
        self.config_dir = config_dir
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.load_all()

    def _read_file(self, path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.json'):
                return json.load(f)
            else:
                return yaml.safe_load(f)

    def load_all(self):
        with self.lock:
            self.cache.clear()
            for fname in os.listdir(self.config_dir):
                if fname.startswith('_'):
                    continue
                full = os.path.join(self.config_dir, fname)
                if os.path.isfile(full) and os.path.splitext(fname)[1] in SUPPORTED_EXT:
                    try:
                        name = os.path.splitext(fname)[0]
                        self.cache[name] = self._read_file(full) or {}
                    except Exception as e:
                        print(f"Failed to load {fname}: {e}")

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.cache.get(name)

    def save(self, name: str, content: Dict[str, Any], format: str = 'yaml') -> Dict[str, Any]:
        # persist file
        fname = f"{name}.{ 'yaml' if format in ('yaml','yml') else 'json' }"
        full = os.path.join(self.config_dir, fname)
        # write temp then move for atomicity
        tmp = full + f".tmp.{int(time.time()*1000)}"
        with open(tmp, 'w', encoding='utf-8') as f:
            if fname.endswith('.json'):
                json.dump(content, f, indent=2)
            else:
                yaml.safe_dump(content, f)
        os.replace(tmp, full)
        # versioning copy
        version_fname = f"{name}__{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}__{uuid.uuid4().hex}.yaml"
        vfull = os.path.join(VERSIONS_DIR, version_fname)
        shutil.copyfile(full, vfull)
        vid = version_store.add_version(name, version_fname, metadata={"format": format})
        # update cache
        with self.lock:
            self.cache[name] = content
        return {"version_id": vid, "filename": version_fname}

    def load_version_file(self, version_filename: str) -> Dict[str, Any]:
        path = os.path.join(VERSIONS_DIR, version_filename)
        return self._read_file(path)

config_manager = ConfigManager()

# Watchdog handler for hot reload
class ConfigChangeHandler(FileSystemEventHandler):
    def __init__(self, manager: ConfigManager):
        self.manager = manager

    def on_modified(self, event):
        if event.is_directory:
            return
        fname = os.path.basename(event.src_path)
        if fname.startswith('_'):
            return
        if os.path.splitext(fname)[1] in SUPPORTED_EXT:
            print(f"Detected change: {fname} -> reloading configs")
            self.manager.load_all()

if HOT_RELOAD:
    observer = Observer()
    handler = ConfigChangeHandler(config_manager)
    observer.schedule(handler, CONFIG_DIR, recursive=False)
    observer.daemon = True
    observer.start()

# -------------------- A/B Testing Helper --------------------
import random

def choose_variant(config: Dict[str, Any], header_variant: Optional[str] = None) -> str:
    # config can contain a `variants` section: {"a": 70, "b": 30}
    variants = config.get('variants') if isinstance(config, dict) else None
    if header_variant:
        if variants and header_variant in variants:
            return header_variant
        # allow direct mapping if provided matches
    if not variants:
        return 'default'
    # normalize weights
    items = list(variants.items())
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    upto = 0
    for name, weight in items:
        upto += weight
        if r <= upto:
            return name
    return items[-1][0]

# -------------------- FastAPI endpoints --------------------
app = FastAPI(title="Config Management Service")

class SaveResponse(BaseModel):
    version_id: str
    filename: str

@app.get("/configs/list")
def list_configs():
    return {"configs": list(config_manager.cache.keys())}

@app.get("/configs/{name}")
def get_config(name: str, request: Request, x_variant: Optional[str] = Header(None)):
    cfg = config_manager.get(name)
    if cfg is None:
        raise HTTPException(status_code=404, detail="Config not found")
    variant = choose_variant(cfg, header_variant=x_variant)
    data = cfg.get('variants_data', {}).get(variant) if 'variants_data' in cfg else cfg
    return {"name": name, "variant": variant, "config": data}

@app.post("/configs/{name}", response_model=SaveResponse)
async def upload_config(name: str, file: UploadFile = File(...)):
    content = await file.read()
    
    # Safely decode file content
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = content.decode('utf-16')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding not supported (UTF-8 or UTF-16 expected)")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    
    # Parse content safely
    if ext == '.json':
        try:
            data = json.loads(text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        fmt = 'json'
    else:
        try:
            data = yaml.safe_load(text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
        fmt = 'yaml'
    
    res = config_manager.save(name, data, format=fmt)
    return SaveResponse(**res)


@app.get("/configs/{name}/versions")
def versions(name: str):
    return {"versions": version_store.list_versions(name)}

@app.post("/configs/{name}/activate")
def activate_version(name: str, version_id: str):
    # find version
    versions = version_store.list_versions(name)
    if not any(v['id'] == version_id for v in versions):
        raise HTTPException(status_code=404, detail="Version not found")
    version_store.set_active(name, version_id)
    return {"status": "ok", "version_id": version_id}

@app.get("/configs/{name}/version/{version_id}")
def get_version_file(name: str, version_id: str):
    versions = version_store.list_versions(name)
    match = next((v for v in versions if v['id'] == version_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Version not found")
    filename = match['filename']
    data = config_manager.load_version_file(filename)
    return {"id": version_id, "filename": filename, "config": data}

# health
@app.get("/health")
def health():
    return {"status": "ok", "services": {"configs_files": True}}

# -------------------- CLI utility for seeding and testing --------------------
if __name__ == '__main__':
    import uvicorn
    print("Starting Config Management Service on http://0.0.0.0:9000")
    uvicorn.run(app, host='0.0.0.0', port=9000, log_level='info')
