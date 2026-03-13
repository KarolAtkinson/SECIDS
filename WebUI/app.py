#!/usr/bin/env python3
"""SecIDS-CNN Web UI backend."""

from __future__ import annotations

import json
import base64
import os
import re
import ipaddress
import shlex
import select
import signal
import subprocess
import shutil
import threading
import time
import uuid
import hashlib
import hmac
import secrets
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Any, Deque, Dict, List, Tuple

from flask import Flask, jsonify, redirect, render_template, request, session

try:
    from .menu_actions import get_menu_actions
    from .model_registry_db import ModelRegistryDB
except ImportError:
    from menu_actions import get_menu_actions
    from model_registry_db import ModelRegistryDB


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UI_CONFIG_FILE = PROJECT_ROOT / "UI" / "ui_config.json"
COMMAND_HISTORY_FILE = PROJECT_ROOT / "Config" / "command_history.json"
WEBUI_USERS_FILE = PROJECT_ROOT / "Config" / "webui_users.json"
AUDIT_LOG_FILE = PROJECT_ROOT / "Logs" / "webui_audit.jsonl"
WEBUI_RUNTIME_FILE = PROJECT_ROOT / "Config" / "webui_runtime.json"
SERVER_DB_ENV = os.getenv("SECIDS_SERVER_DB_ROOT", "").strip()
if SERVER_DB_ENV:
    server_db_candidate = Path(SERVER_DB_ENV).expanduser()
    SERVER_DB_ROOT = server_db_candidate if server_db_candidate.is_absolute() else (PROJECT_ROOT / server_db_candidate)
else:
    SERVER_DB_ROOT = PROJECT_ROOT / "ServerDB"
MODEL_REGISTRY_DB_FILE = SERVER_DB_ROOT / "modelDB" / "model_registry.db"
LEGACY_MODEL_REGISTRY_DB_FILE = PROJECT_ROOT / "WebUI" / "model_registry.db"
TRASH_DUMP_DIR = PROJECT_ROOT / "TrashDump"
VENV_PYTHON = PROJECT_ROOT / ".venv_test" / "bin" / "python"
VENV_PIP = PROJECT_ROOT / ".venv_test" / "bin" / "pip"

DEFAULT_JOB_TIMEOUT_SECONDS = int(os.getenv("SECIDS_JOB_TIMEOUT_SECONDS", "1800"))
DEFAULT_MAX_CONCURRENT_JOBS = int(os.getenv("SECIDS_MAX_CONCURRENT_JOBS", "2"))
API_TOKEN = os.getenv("SECIDS_WEB_TOKEN", "").strip()
TOKEN_ROLE = os.getenv("SECIDS_TOKEN_ROLE", "admin").strip() or "admin"
APP_SECRET = os.getenv("SECIDS_WEB_SECRET", "secids-dev-secret")
MAX_LOGIN_ATTEMPTS = int(os.getenv("SECIDS_AUTH_MAX_ATTEMPTS", "5"))
LOCKOUT_SECONDS = int(os.getenv("SECIDS_AUTH_LOCKOUT_SECONDS", "900"))
PASSWORD_MIN_LENGTH = int(os.getenv("SECIDS_AUTH_MIN_PASSWORD_LENGTH", "10"))
PASSWORD_MAX_AGE_DAYS = int(os.getenv("SECIDS_AUTH_MAX_AGE_DAYS", "90"))
SESSION_TIMEOUT_SECONDS = int(os.getenv("SECIDS_SESSION_TIMEOUT_SECONDS", "1800"))
ACCESS_PATH_PREFIX = os.getenv("SECIDS_WEB_ACCESS_PREFIX", "/portal").strip() or "/portal"
ACCESS_PATH_PREFIX = ACCESS_PATH_PREFIX if ACCESS_PATH_PREFIX.startswith("/") else f"/{ACCESS_PATH_PREFIX}"
ACCESS_PATH_PREFIX = ACCESS_PATH_PREFIX.rstrip("/")

ROLE_ORDER = {"guest": 20, "viewer": 10, "operator": 20, "admin": 30}
SINGLE_ADMIN_MODE = os.getenv("SECIDS_SINGLE_ADMIN_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}
SINGLE_ADMIN_USERNAME = os.getenv("SECIDS_SINGLE_ADMIN_USERNAME", "kali").strip() or "kali"
SINGLE_ADMIN_PASSWORD = os.getenv("SECIDS_SINGLE_ADMIN_PASSWORD", "uclb()w1V").strip() or "uclb()w1V"
DEFAULT_USERS = {
    "guest": {"password": "guest123", "role": "guest"},
    "admin": {"password": "admin123", "role": "admin"},
    "operator": {"password": "operator123", "role": "operator"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}

sys.path.insert(0, str(PROJECT_ROOT))


def read_json_file(file_path: Path, fallback):
    if not file_path.exists():
        return fallback
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return fallback


def write_json_file(file_path: Path, payload) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def hash_password(password: str, salt_b64: str | None = None, iterations: int = 200_000) -> Dict:
    salt = base64.b64decode(salt_b64) if salt_b64 else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return {
        "password_hash": base64.b64encode(digest).decode("utf-8"),
        "password_salt": base64.b64encode(salt).decode("utf-8"),
        "password_iterations": iterations,
    }


def verify_password_record(password: str, record: Dict) -> bool:
    if "password_hash" in record and "password_salt" in record:
        iterations = int(record.get("password_iterations", 200_000))
        expected = hash_password(password, record.get("password_salt"), iterations)
        return hmac.compare_digest(expected["password_hash"], str(record.get("password_hash", "")))

    if "password" in record:
        return hmac.compare_digest(str(record.get("password", "")), password)

    return False


def normalize_user_record(record: Dict) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {"role": str(record.get("role", "viewer"))}

    if "password_hash" in record and "password_salt" in record:
        normalized["password_hash"] = str(record.get("password_hash", ""))
        normalized["password_salt"] = str(record.get("password_salt", ""))
        normalized["password_iterations"] = int(record.get("password_iterations", 200_000))
    elif "password" in record:
        normalized["password"] = str(record.get("password", ""))
    else:
        normalized.update(hash_password("changeme123"))
        normalized["must_change_password"] = True

    normalized["must_change_password"] = bool(record.get("must_change_password", "password" in normalized))
    normalized["active"] = bool(record.get("active", True))
    if "password_changed_at" in record:
        normalized["password_changed_at"] = record.get("password_changed_at")
    return normalized


def get_default_settings() -> Dict:
    return {
        "last_interface": "eth0",
        "last_duration": 60,
        "last_window": 5,
        "last_interval": 2,
        "countermeasure_mode": "active",
        "live_model_mode": "auto",
        "live_model_path": "",
        "live_backend": "",
        "theme": "default",
        "ws_theme": "Default",
        "ws_language": "en-US",
        "ws_layout_profile": "Wireshark Classic",
        "ws_packet_list_visible": True,
        "ws_packet_details_visible": True,
        "ws_packet_bytes_visible": True,
        "ws_show_column_number": True,
        "ws_show_column_time": True,
        "ws_show_column_source": True,
        "ws_show_column_destination": True,
        "ws_show_column_protocol": True,
        "ws_show_column_length": True,
        "ws_show_column_info": True,
        "ws_font_family": "Monospace",
        "ws_font_size": 12,
        "ws_colorize_packet_list": True,
        "ws_resolve_mac": True,
        "ws_resolve_network": False,
        "ws_resolve_transport": False,
        "ws_capture_promisc_mode": True,
        "ws_capture_monitor_mode": False,
        "ws_capture_update_realtime": True,
        "ws_enable_filter_buttons": True,
        "ws_filter_profile": "Default",
        "ws_protocols_enabled_profile": "All",
        "ws_expert_custom_enabled": False,
        "ws_expert_severity_policy": "Default",
        "ws_rsa_keys_profile": "Default",
        "ws_advanced_show_changed_only": False,
        "ws_advanced_search_text": "",
        "ws_statistics_auto_update": True,
        "ws_statistics_interval": 2,
        "history": [],
    }


def load_webui_users() -> Dict[str, Dict]:
    payload = read_json_file(WEBUI_USERS_FILE, {})

    if isinstance(payload, dict) and "users" in payload and isinstance(payload["users"], list):
        users = {}
        for item in payload["users"]:
            username = str(item.get("username", "")).strip()
            role = str(item.get("role", "viewer")).strip()
            if username and role in ROLE_ORDER:
                users[username] = normalize_user_record(item)
        if users:
            return users

    if isinstance(payload, dict) and payload:
        users = {}
        for username, item in payload.items():
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "viewer")).strip()
            if role not in ROLE_ORDER:
                continue
            users[str(username).strip()] = normalize_user_record(item)
        if users:
            return users

    return {user: normalize_user_record(config) for user, config in DEFAULT_USERS.items()}


def save_webui_users(users: Dict[str, Dict]) -> None:
    payload = {username: normalize_user_record(record) for username, record in users.items()}
    write_json_file(WEBUI_USERS_FILE, payload)


def load_runtime_settings() -> Dict[str, str]:
    payload = read_json_file(WEBUI_RUNTIME_FILE, {})
    saved_path = str(payload.get("access_path", "")).strip() if isinstance(payload, dict) else ""

    if saved_path and re.fullmatch(r"/[A-Za-z0-9/_-]{4,128}", saved_path):
        return {"access_path": saved_path.rstrip("/")}

    slug = secrets.token_urlsafe(7).replace("-", "").replace("_", "")[:10].lower()
    access_path = f"{ACCESS_PATH_PREFIX}/{slug}"
    runtime = {"access_path": access_path}
    write_json_file(WEBUI_RUNTIME_FILE, runtime)
    return runtime


def load_ui_settings() -> Dict:
    defaults = get_default_settings()
    persisted = read_json_file(UI_CONFIG_FILE, defaults.copy())
    defaults.update({key: value for key, value in persisted.items() if key in defaults or key == "history"})
    if "history" not in defaults or not isinstance(defaults["history"], list):
        defaults["history"] = []
    return defaults


def save_ui_settings(settings: Dict) -> None:
    write_json_file(UI_CONFIG_FILE, settings)


def load_command_history() -> List[Dict]:
    return read_json_file(COMMAND_HISTORY_FILE, [])


def save_command_history(history: List[Dict]) -> None:
    write_json_file(COMMAND_HISTORY_FILE, history[-200:])


def append_ui_history(command: str) -> None:
    settings = load_ui_settings()
    settings.setdefault("history", [])
    settings["history"].append({"command": command, "timestamp": datetime.utcnow().isoformat()})
    settings["history"] = settings["history"][-200:]
    save_ui_settings(settings)


def build_action_index(menu: List[Dict]) -> Dict[str, Dict]:
    index: Dict[str, Dict] = {}
    for section in menu:
        for action in section.get("actions", []):
            index[action["id"]] = action
    return index


def quote_params(params: Dict[str, str]) -> Dict[str, str]:
    return {key: shlex.quote(str(value)) for key, value in params.items()}


def resolve_shortcut_command(shortcut: str) -> Tuple[str, bool]:
    from Tools.command_library import CommandLibrary

    library = CommandLibrary()
    if shortcut not in library.commands:
        raise ValueError(f"Shortcut '{shortcut}' not found in command library")

    cmd_info = library.commands[shortcut]
    return cmd_info["cmd"], bool(cmd_info.get("sudo", False))


def build_command(action: Dict, params: Dict[str, str]) -> str:
    executor = action["executor"]
    cmd_template = ""
    require_sudo = False

    if executor["kind"] == "shortcut":
        cmd_template, require_sudo = resolve_shortcut_command(executor["value"])
    elif executor["kind"] == "shell":
        cmd_template = executor["value"]
        require_sudo = cmd_template.strip().startswith("sudo ")
    else:
        raise ValueError(f"Unsupported executor kind for shell build: {executor['kind']}")

    expected = {param["name"] for param in action.get("params", [])}
    provided = {key: value for key, value in params.items() if key in expected}
    safe_params = quote_params(provided)

    missing_required = [name for name in expected if f"{{{name}}}" in cmd_template and name not in provided]
    if missing_required:
        raise ValueError(f"Missing required parameters: {', '.join(sorted(missing_required))}")

    command = cmd_template
    for key, value in safe_params.items():
        command = command.replace(f"{{{key}}}", value)

    if require_sudo and not command.startswith("sudo "):
        command = f"sudo {command}"

    command = normalize_command_for_runtime(command)
    return apply_live_model_preferences(command, str(action.get("id", "")))


def infer_backend_from_model_path(model_path: str) -> str:
    suffix = Path(model_path).suffix.lower()
    if suffix in {".pkl", ".pickle", ".joblib"}:
        return "unified"
    return "tf"


def apply_live_model_preferences(command: str, action_id: str) -> str:
    if not action_id.startswith("live-detect"):
        return command

    normalized = command
    settings = load_ui_settings()
    model_mode = str(settings.get("live_model_mode", "auto") or "auto").strip().lower()
    model_path = str(settings.get("live_model_path", "")).strip()
    backend = str(settings.get("live_backend", "")).strip().lower()

    if model_mode != "manual":
        return normalized

    if model_path and " --model " not in f" {normalized} ":
        normalized = f"{normalized} --model {shlex.quote(model_path)}"

    if " --backend " not in f" {normalized} ":
        selected_backend = backend or (infer_backend_from_model_path(model_path) if model_path else "")
        if selected_backend in {"tf", "unified"}:
            normalized = f"{normalized} --backend {selected_backend}"

    return normalized


def normalize_command_for_runtime(command: str) -> str:
    """Normalize shell commands to prefer project virtualenv Python/pip."""
    normalized = command

    if VENV_PYTHON.exists():
        py_exec = shlex.quote(str(VENV_PYTHON))
        normalized = re.sub(r"(^|\s)sudo\s+python3(\s+)", rf"\1sudo {py_exec}\2", normalized)
        normalized = re.sub(r"(^|\s)python3(\s+)", rf"\1{py_exec}\2", normalized)
        normalized = re.sub(r"(^|\s)sudo\s+python(\s+)", rf"\1sudo {py_exec}\2", normalized)
        normalized = re.sub(r"(^|\s)python(\s+)", rf"\1{py_exec}\2", normalized)

    if VENV_PIP.exists():
        pip_exec = shlex.quote(str(VENV_PIP))
        normalized = re.sub(r"(^|\s)sudo\s+pip3(\s+)", rf"\1sudo {pip_exec}\2", normalized)
        normalized = re.sub(r"(^|\s)pip3(\s+)", rf"\1{pip_exec}\2", normalized)
        normalized = re.sub(r"(^|\s)sudo\s+pip(\s+)", rf"\1sudo {pip_exec}\2", normalized)
        normalized = re.sub(r"(^|\s)pip(\s+)", rf"\1{pip_exec}\2", normalized)

    return normalized


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = APP_SECRET

    # Harden session cookies for multi-user safety: each user's session is fully
    # isolated via their own signed cookie; these flags prevent cross-user leakage.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False  # set True when behind HTTPS/TLS

    runtime_settings = load_runtime_settings()
    access_path = runtime_settings["access_path"]
    login_path = f"{access_path}/login"
    app.config["SECIDS_ACCESS_PATH"] = access_path
    app.config["SECIDS_LOGIN_PATH"] = login_path
    app.config["SECIDS_SESSION_TIMEOUT_SECONDS"] = SESSION_TIMEOUT_SECONDS

    menu_model = get_menu_actions()
    action_index = build_action_index(menu_model)

    MODEL_REGISTRY_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MODEL_REGISTRY_DB_FILE.exists() and LEGACY_MODEL_REGISTRY_DB_FILE.exists():
        try:
            shutil.copy2(LEGACY_MODEL_REGISTRY_DB_FILE, MODEL_REGISTRY_DB_FILE)
        except OSError:
            pass

    model_registry = ModelRegistryDB(MODEL_REGISTRY_DB_FILE, PROJECT_ROOT)
    try:
        model_registry.migrate_registry_paths_to_server()
    except Exception:
        pass
    model_registry_dirs = [
        PROJECT_ROOT / "Models",
        PROJECT_ROOT / "Model_Tester" / "models",
        PROJECT_ROOT / "Model_Tester" / "Code" / "models",
        PROJECT_ROOT / "SecIDS-CNN",
        PROJECT_ROOT / "Results",
        PROJECT_ROOT / "Stress_Test_Results",
    ]
    users_db = load_webui_users()
    if SINGLE_ADMIN_MODE:
        users_db = {
            SINGLE_ADMIN_USERNAME: normalize_user_record(
                {
                    "role": "admin",
                    "active": True,
                    "must_change_password": False,
                    "password_changed_at": datetime.utcnow().isoformat(),
                    **hash_password(SINGLE_ADMIN_PASSWORD),
                }
            )
        }
    save_webui_users(users_db)

    jobs: Dict[str, Dict] = {}
    jobs_lock = threading.Lock()
    active_processes: Dict[str, subprocess.Popen] = {}
    queue: Deque[str] = deque()
    queue_paused = False
    max_concurrent_jobs = max(1, DEFAULT_MAX_CONCURRENT_JOBS)
    audit_events: Deque[Dict] = deque(maxlen=500)
    users_lock = threading.Lock()
    sudo_cache_lock = threading.Lock()
    session_sudo_cache: Dict[str, str] = {}
    failed_login_attempts: Dict[str, int] = {}
    lockout_until: Dict[str, float] = {}
    packet_capture_lock = threading.Lock()
    packet_capture_rows: Deque[Dict[str, str]] = deque(maxlen=1500)
    packet_capture_process: subprocess.Popen | None = None
    packet_capture_reader: threading.Thread | None = None
    packet_capture_running = False
    packet_capture_paused = False
    packet_capture_interface = ""
    packet_capture_source = ""
    packet_capture_last_error = ""
    packet_capture_sequence = 1
    packet_capture_last_attempt_at = 0.0
    packet_capture_auto_managed = False
    control_surface_cache_lock = threading.Lock()
    control_surface_cache_payload: Dict[str, Any] = {}
    control_surface_cache_timestamp = 0.0
    guest_presence_lock = threading.Lock()
    guest_presence_sessions: Dict[str, Dict[str, Any]] = {}
    guest_presence_ttl_seconds = int(os.getenv("SECIDS_GUEST_PRESENCE_TTL_SECONDS", "7200"))
    server_db_lock = threading.Lock()
    server_db_folders = {
        "settings": SERVER_DB_ROOT / "settingsDB",
        "history": SERVER_DB_ROOT / "historyDB",
        "audit": SERVER_DB_ROOT / "auditDB",
        "users": SERVER_DB_ROOT / "userDB",
        "models": SERVER_DB_ROOT / "modelDB",
        "action_logs": SERVER_DB_ROOT / "actionDB",
        "packet_logs": SERVER_DB_ROOT / "packetDB",
        "webui_versions": SERVER_DB_ROOT / "webuiVersionsDB",
        "nist_csw": SERVER_DB_ROOT / "NIST-CSW",
    }
    server_db_data_folders = {
        "NIST-CSW": SERVER_DB_ROOT / "NIST-CSW",
        "modelDB": SERVER_DB_ROOT / "modelDB",
        "datasetDB": SERVER_DB_ROOT / "datasetDB",
        "captureDB": SERVER_DB_ROOT / "captureDB",
        "resultDB": SERVER_DB_ROOT / "resultDB",
        "reportDB": SERVER_DB_ROOT / "reportDB",
        "settingsDB": SERVER_DB_ROOT / "settingsDB",
        "userDB": SERVER_DB_ROOT / "userDB",
        "auditDB": SERVER_DB_ROOT / "auditDB",
        "actionDB": SERVER_DB_ROOT / "actionDB",
        "packetDB": SERVER_DB_ROOT / "packetDB",
        "historyDB": SERVER_DB_ROOT / "historyDB",
        "webuiVersionsDB": SERVER_DB_ROOT / "webuiVersionsDB",
        "profileDB": SERVER_DB_ROOT / "profileDB",
        "logDB": SERVER_DB_ROOT / "logDB",
        "miscDB": SERVER_DB_ROOT / "miscDB",
    }
    server_db_custom_root = SERVER_DB_ROOT / "custom"
    retention_folder_keys = {"packet_logs", "action_logs", "history"}
    retention_prefix_map = {
        "packet_logs": "packet_logs",
        "action_logs": "action_logs",
        "history": "history",
    }
    retention_trash_roots = {
        "packet_logs": TRASH_DUMP_DIR / "packet_logs_retention",
        "action_logs": TRASH_DUMP_DIR / "action_logs_retention",
        "history": TRASH_DUMP_DIR / "history_retention",
    }

    def role_rank(role: str) -> int:
        return ROLE_ORDER.get(role, ROLE_ORDER["viewer"])

    def ensure_server_db_structure() -> None:
        SERVER_DB_ROOT.mkdir(parents=True, exist_ok=True)
        server_db_custom_root.mkdir(parents=True, exist_ok=True)
        for trash_root in retention_trash_roots.values():
            trash_root.mkdir(parents=True, exist_ok=True)
        for folder_path in server_db_folders.values():
            folder_path.mkdir(parents=True, exist_ok=True)
        for folder_path in server_db_data_folders.values():
            folder_path.mkdir(parents=True, exist_ok=True)

    def sanitize_server_folder_name(raw: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", str(raw or "").strip())
        cleaned = cleaned.strip("._")
        return cleaned[:64]

    def enforce_retention_for_folder(folder_key: str, now: datetime | None = None) -> None:
        if folder_key not in retention_folder_keys:
            return
        ensure_server_db_structure()
        reference = now or datetime.utcnow()
        cutoff = reference - timedelta(days=30)
        folder_path = server_db_folders[folder_key]
        prefix = retention_prefix_map[folder_key]
        trash_root = retention_trash_roots[folder_key]

        for file_path in folder_path.glob(f"{prefix}_*.jsonl"):
            stem = file_path.stem
            date_token = stem.replace(f"{prefix}_", "")
            try:
                file_day = datetime.strptime(date_token, "%Y%m%d")
            except ValueError:
                continue
            if file_day > cutoff:
                continue

            destination = trash_root / file_path.name
            suffix = 1
            while destination.exists():
                destination = trash_root / f"{file_path.stem}_{suffix}{file_path.suffix}"
                suffix += 1
            shutil.move(str(file_path), str(destination))

    def append_server_snapshot(folder_key: str, flag: str, payload: Any) -> None:
        ensure_server_db_structure()
        timestamp = datetime.utcnow()
        folder_path = server_db_folders.get(folder_key)
        if folder_path is None:
            return

        if folder_key in retention_folder_keys:
            file_name = f"{retention_prefix_map[folder_key]}_{timestamp.strftime('%Y%m%d')}.jsonl"
        else:
            file_name = f"{folder_key}.jsonl"

        record = {
            "stored_at": timestamp.isoformat(),
            "flag": flag,
            "folder": folder_key,
            "payload": payload,
        }
        line = json.dumps(record, ensure_ascii=False)

        with server_db_lock:
            target = folder_path / file_name
            with open(target, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")

        if folder_key in retention_folder_keys:
            enforce_retention_for_folder(folder_key, timestamp)

    def read_last_jsonl_payload(file_path: Path) -> Dict[str, Any] | None:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                lines = [line.strip() for line in handle if line.strip()]
            for line in reversed(lines):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict):
                    return record
        except OSError:
            return None
        return None

    def latest_snapshot_payload(folder_key: str) -> Dict[str, Any] | None:
        folder_path = server_db_folders.get(folder_key)
        if folder_path is None or not folder_path.exists():
            return None

        files = sorted(
            [item for item in folder_path.iterdir() if item.is_file()],
            key=lambda item: (item.stat().st_mtime, item.name),
            reverse=True,
        )
        for file_path in files:
            record = read_last_jsonl_payload(file_path)
            if record:
                payload = record.get("payload")
                return payload if isinstance(payload, dict) else {"payload": payload}
        return None

    def classify_server_data_tag(relative_path: Path) -> str:
        parts = relative_path.parts
        top = parts[0] if parts else ""
        suffix = relative_path.suffix.lower()
        lower_text = str(relative_path).lower()

        if "nist" in lower_text or "csw" in lower_text or "simulation_ddos" in lower_text:
            return "NIST-CSW"

        model_ext = {".h5", ".keras", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".tflite"}
        if suffix in model_ext or top in {"Models"}:
            return "modelDB"
        if suffix in {".pcap", ".pcapng"} or top in {"Captures"}:
            return "captureDB"
        if suffix in {".csv", ".parquet"} or top in {"Archives"}:
            return "datasetDB"
        if top in {"Results", "Stress_Test_Results"}:
            return "resultDB"
        if top in {"WebUI", "Backups"}:
            return "webuiVersionsDB"
        if top in {"Reports"}:
            return "reportDB"
        if top in {"Logs"}:
            return "logDB"
        if top in {"Config"}:
            if "users" in lower_text:
                return "userDB"
            return "settingsDB"
        if "audit" in lower_text:
            return "auditDB"
        if "packet" in lower_text:
            return "packetDB"
        if "action" in lower_text:
            return "actionDB"
        if "history" in lower_text:
            return "historyDB"
        if top in {"Device_Profile"}:
            return "profileDB"
        return "miscDB"

    def normalize_project_relative_path(path_text: str) -> str:
        cleaned = str(path_text or "").strip()
        if not cleaned:
            return ""
        candidate = Path(cleaned)
        if candidate.is_absolute():
            try:
                return str(candidate.resolve().relative_to(PROJECT_ROOT.resolve()))
            except ValueError:
                return ""
        return str(candidate)

    def parse_simulation_artifact_paths(logs: List[str]) -> Dict[str, str]:
        dataset = ""
        report = ""
        for line in logs:
            if "Synthetic dataset saved:" in line:
                dataset = normalize_project_relative_path(line.split("Synthetic dataset saved:", 1)[1].strip())
            elif "Report written:" in line:
                report = normalize_project_relative_path(line.split("Report written:", 1)[1].strip())
        return {"dataset": dataset, "report": report}

    def stage_nist_csw_file(relative_path: str, stage: str) -> str:
        if not relative_path:
            return ""
        ensure_server_db_structure()
        source = (PROJECT_ROOT / relative_path).resolve()
        if not source.exists() or not source.is_file():
            return ""

        nist_root = server_db_folders["nist_csw"]
        nist_root.mkdir(parents=True, exist_ok=True)
        safe_stage = re.sub(r"[^A-Za-z0-9_-]", "_", stage or "data")
        target = nist_root / f"{safe_stage}__{source.name}"
        if target.exists():
            target = nist_root / f"{target.stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{target.suffix}"
        shutil.copy2(source, target)
        return str(target.relative_to(PROJECT_ROOT))

    def sync_project_data_to_server_db(execute: bool = True) -> Dict[str, Any]:
        ensure_server_db_structure()
        scan_roots = [
            PROJECT_ROOT / "Archives",
            PROJECT_ROOT / "Captures",
            PROJECT_ROOT / "Backups",
            PROJECT_ROOT / "Results",
            PROJECT_ROOT / "Reports",
            PROJECT_ROOT / "Logs",
            PROJECT_ROOT / "Stress_Test_Results",
            PROJECT_ROOT / "Config",
            PROJECT_ROOT / "Models",
            PROJECT_ROOT / "Device_Profile",
        ]
        excluded_suffixes = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".css",
            ".html",
            ".sh",
            ".md",
            ".db",
        }

        summary: Dict[str, Any] = {
            "started_at": datetime.utcnow().isoformat(),
            "execute": execute,
            "scanned": 0,
            "synced": 0,
            "skipped": 0,
            "errors": 0,
            "by_tag": {},
            "error_samples": [],
        }

        for root in scan_roots:
            if not root.exists() or not root.is_dir():
                continue

            for source_path in root.rglob("*"):
                if not source_path.is_file():
                    continue

                relative = source_path.relative_to(PROJECT_ROOT)
                if relative.suffix.lower() in excluded_suffixes:
                    continue

                summary["scanned"] += 1
                tag = classify_server_data_tag(relative)
                target_root = server_db_data_folders.get(tag, server_db_data_folders["miscDB"])
                target_path = target_root / relative
                target_path.parent.mkdir(parents=True, exist_ok=True)

                tag_stats = summary["by_tag"].setdefault(tag, {"synced": 0, "skipped": 0})

                if target_path.exists():
                    src_stat = source_path.stat()
                    dst_stat = target_path.stat()
                    if int(src_stat.st_mtime) == int(dst_stat.st_mtime) and src_stat.st_size == dst_stat.st_size:
                        summary["skipped"] += 1
                        tag_stats["skipped"] += 1
                        continue

                if not execute:
                    summary["synced"] += 1
                    tag_stats["synced"] += 1
                    continue

                try:
                    if target_path.exists():
                        target_path.unlink()
                    try:
                        os.link(source_path, target_path)
                    except OSError:
                        shutil.copy2(source_path, target_path)
                    summary["synced"] += 1
                    tag_stats["synced"] += 1
                except OSError as exc:
                    summary["errors"] += 1
                    if len(summary["error_samples"]) < 20:
                        summary["error_samples"].append({"file": str(relative), "error": str(exc)})

        summary["finished_at"] = datetime.utcnow().isoformat()
        summary["db_root"] = str(SERVER_DB_ROOT.relative_to(PROJECT_ROOT))
        append_server_snapshot("audit", "PROJECT_DATA_SYNC", summary)
        return summary

    def run_nist_csw_feed_update(feeds: List[str] | None = None) -> Dict[str, Any]:
        script_path = PROJECT_ROOT / "Scripts" / "update_nist_csw_sources.py"
        if not script_path.exists():
            return {"ok": False, "error": "update script not found", "script": str(script_path.relative_to(PROJECT_ROOT))}

        command = [str(VENV_PYTHON if VENV_PYTHON.exists() else Path("python3")), str(script_path)]
        if feeds:
            command.extend(["--feeds", *feeds])

        try:
            result = subprocess.run(
                command,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            payload = {"ok": False, "error": "NIST-CSW feed update timed out"}
            append_server_snapshot("nist_csw", "NIST_CSW_UPDATE_FAILED", payload)
            return payload
        except Exception as exc:
            payload = {"ok": False, "error": str(exc)}
            append_server_snapshot("nist_csw", "NIST_CSW_UPDATE_FAILED", payload)
            return payload

        parsed: Dict[str, Any]
        try:
            parsed = json.loads((result.stdout or "").strip() or "{}")
        except json.JSONDecodeError:
            parsed = {
                "ok": result.returncode == 0,
                "stdout": (result.stdout or "")[:3000],
                "stderr": (result.stderr or "")[:1000],
            }

        parsed["return_code"] = result.returncode
        parsed["stderr"] = (result.stderr or "")[:1000]
        append_server_snapshot("nist_csw", "NIST_CSW_UPDATE" if parsed.get("ok") else "NIST_CSW_UPDATE_FAILED", parsed)
        return parsed

    def run_nist_csw_converter() -> Dict[str, Any]:
        script_path = PROJECT_ROOT / "Scripts" / "convert_nist_csw_to_model_format.py"
        if not script_path.exists():
            return {"ok": False, "error": "converter script not found", "script": str(script_path.relative_to(PROJECT_ROOT))}

        command = [str(VENV_PYTHON if VENV_PYTHON.exists() else Path("python3")), str(script_path)]
        try:
            result = subprocess.run(
                command,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=240,
            )
        except subprocess.TimeoutExpired:
            payload = {"ok": False, "error": "NIST-CSW conversion timed out"}
            append_server_snapshot("nist_csw", "NIST_CSW_CONVERT_FAILED", payload)
            return payload
        except Exception as exc:
            payload = {"ok": False, "error": str(exc)}
            append_server_snapshot("nist_csw", "NIST_CSW_CONVERT_FAILED", payload)
            return payload

        parsed: Dict[str, Any]
        try:
            parsed = json.loads((result.stdout or "").strip() or "{}")
        except json.JSONDecodeError:
            parsed = {
                "ok": result.returncode == 0,
                "stdout": (result.stdout or "")[:3000],
                "stderr": (result.stderr or "")[:1000],
            }

        parsed["return_code"] = result.returncode
        parsed["stderr"] = (result.stderr or "")[:1000]
        append_server_snapshot("nist_csw", "NIST_CSW_CONVERT" if parsed.get("ok") else "NIST_CSW_CONVERT_FAILED", parsed)
        return parsed

    def get_latest_nist_csw_update_status() -> Dict[str, Any]:
        snapshot = latest_snapshot_payload("nist_csw") or {}
        if not isinstance(snapshot, dict):
            return {"ok": False, "message": "No NIST-CSW updates recorded yet"}
        return snapshot

    def get_server_db_overview() -> Dict[str, Any]:
        ensure_server_db_structure()
        folders = []
        for key, folder_path in server_db_folders.items():
            files = sorted([item.name for item in folder_path.iterdir() if item.is_file()])
            folders.append(
                {
                    "key": key,
                    "path": str(folder_path.relative_to(PROJECT_ROOT)),
                    "file_count": len(files),
                    "files": files[-20:],
                }
            )

        data_folders = []
        for key, folder_path in server_db_data_folders.items():
            file_count = 0
            for _, _, files in os.walk(folder_path):
                file_count += len(files)
            data_folders.append(
                {
                    "key": key,
                    "path": str(folder_path.relative_to(PROJECT_ROOT)),
                    "file_count": file_count,
                }
            )

        custom_folders = sorted([item.name for item in server_db_custom_root.iterdir() if item.is_dir()])
        return {
            "root": str(SERVER_DB_ROOT.relative_to(PROJECT_ROOT)),
            "trash_root": str(retention_trash_roots["packet_logs"].relative_to(PROJECT_ROOT)),
            "retention_trash": {
                key: str(path.relative_to(PROJECT_ROOT))
                for key, path in retention_trash_roots.items()
            },
            "folders": folders,
            "data_folders": data_folders,
            "custom_folders": custom_folders,
        }

    def resolve_server_db_file(folder_key: str, file_name: str) -> Path | None:
        ensure_server_db_structure()
        safe_file = str(file_name or "").strip()
        if not safe_file or "/" in safe_file or "\\" in safe_file or safe_file.startswith("."):
            return None

        if folder_key.startswith("custom/"):
            custom_name = sanitize_server_folder_name(folder_key.split("/", 1)[1])
            if not custom_name:
                return None
            base_folder = server_db_custom_root / custom_name
        else:
            base_folder = server_db_folders.get(folder_key)
            if base_folder is None:
                return None

        file_path = (base_folder / safe_file).resolve()
        base_resolved = base_folder.resolve()
        if file_path.parent != base_resolved:
            return None
        if not file_path.exists() or not file_path.is_file():
            return None
        return file_path

    ensure_server_db_structure()

    def resolve_identity() -> Dict:
        provided = request.headers.get("X-SECIDS-Token", "")
        if API_TOKEN and provided == API_TOKEN:
            role = TOKEN_ROLE if TOKEN_ROLE in ROLE_ORDER else "admin"
            return {
                "username": "token",
                "role": role,
                "authenticated": True,
                "auth_method": "token",
                "must_change_password": False,
            }

        username = session.get("username")
        role = session.get("role")
        if username and role in ROLE_ORDER:
            with users_lock:
                user_record = users_db.get(username)
            if not user_record or not bool(user_record.get("active", True)):
                clear_auth_session()
                return {
                    "username": "anonymous",
                    "role": "viewer",
                    "authenticated": False,
                    "auth_method": "anonymous",
                    "must_change_password": False,
                    "password_rotation_due": False,
                }
            return {
                "username": username,
                "role": role,
                "authenticated": True,
                "auth_method": "session",
                "must_change_password": bool(session.get("must_change_password", False)),
                "password_rotation_due": bool(session.get("password_rotation_due", False)),
            }

        return {
            "username": "anonymous",
            "role": "viewer",
            "authenticated": False,
            "auth_method": "anonymous",
            "must_change_password": False,
            "password_rotation_due": False,
        }

    def resolve_request_role() -> str:
        return resolve_identity()["role"]

    def has_required_role(current_role: str, required_role: str) -> bool:
        return role_rank(current_role) >= role_rank(required_role)

    def is_valid_username(username: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", username))

    def parse_iso_ts(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def password_age_days(record: Dict) -> int | None:
        changed_at = parse_iso_ts(str(record.get("password_changed_at", "")))
        if not changed_at:
            return None
        delta = datetime.utcnow() - changed_at.replace(tzinfo=None)
        return max(0, int(delta.total_seconds() // 86400))

    def is_rotation_due(record: Dict) -> bool:
        if PASSWORD_MAX_AGE_DAYS <= 0:
            return False
        age_days = password_age_days(record)
        if age_days is None:
            return False
        return age_days >= PASSWORD_MAX_AGE_DAYS

    def count_active_admins(exclude_username: str | None = None) -> int:
        total = 0
        for name, record in users_db.items():
            if exclude_username and name == exclude_username:
                continue
            if str(record.get("role", "viewer")) == "admin" and bool(record.get("active", True)):
                total += 1
        return total

    def clear_auth_session() -> None:
        guest_presence_id = str(session.pop("guest_presence_id", "")).strip()
        if guest_presence_id:
            with guest_presence_lock:
                guest_presence_sessions.pop(guest_presence_id, None)
        sudo_cache_id = session.pop("sudo_cache_id", None)
        if sudo_cache_id:
            with sudo_cache_lock:
                session_sudo_cache.pop(str(sudo_cache_id), None)
        session.pop("username", None)
        session.pop("role", None)
        session.pop("must_change_password", None)
        session.pop("password_rotation_due", None)
        session.pop("last_seen_at", None)

    def extract_request_ip() -> str:
        forwarded_for = str(request.headers.get("X-Forwarded-For", "")).strip()
        if forwarded_for:
            first_hop = forwarded_for.split(",")[0].strip()
            normalized = _normalize_ip(first_hop)
            if normalized:
                return normalized

        real_ip = str(request.headers.get("X-Real-IP", "")).strip()
        normalized_real = _normalize_ip(real_ip)
        if normalized_real:
            return normalized_real

        remote_addr = str(request.remote_addr or "").strip()
        normalized_remote = _normalize_ip(remote_addr)
        if normalized_remote:
            return normalized_remote

        return ""

    def register_guest_presence(username: str) -> None:
        client_ip = extract_request_ip()
        if not client_ip:
            return

        presence_id = str(session.get("guest_presence_id", "")).strip() or str(uuid.uuid4())
        session["guest_presence_id"] = presence_id
        now_iso = datetime.utcnow().isoformat()
        with guest_presence_lock:
            guest_presence_sessions[presence_id] = {
                "username": username,
                "ip": client_ip,
                "created_at": now_iso,
                "last_seen_at": now_iso,
            }

    def touch_guest_presence() -> None:
        presence_id = str(session.get("guest_presence_id", "")).strip()
        if not presence_id:
            return
        now_iso = datetime.utcnow().isoformat()
        with guest_presence_lock:
            row = guest_presence_sessions.get(presence_id)
            if not row:
                return
            row["last_seen_at"] = now_iso

    def get_guest_presence_devices() -> List[Dict[str, str]]:
        now = datetime.utcnow()
        output: List[Dict[str, str]] = []
        with guest_presence_lock:
            stale_keys: List[str] = []
            for key, row in guest_presence_sessions.items():
                last_seen = parse_iso_ts(str(row.get("last_seen_at", "")))
                if not last_seen:
                    stale_keys.append(key)
                    continue

                age_seconds = (now - last_seen.replace(tzinfo=None)).total_seconds()
                if guest_presence_ttl_seconds > 0 and age_seconds > guest_presence_ttl_seconds:
                    stale_keys.append(key)
                    continue

                ip_value = _normalize_ip(row.get("ip"))
                if not ip_value:
                    continue

                output.append(
                    {
                        "ip": ip_value,
                        "mac": "",
                        "state": "WEBUI-GUEST",
                        "interface": "webui",
                        "list_status": "whitelist",
                    }
                )

            for key in stale_keys:
                guest_presence_sessions.pop(key, None)

        return output

    def get_or_create_sudo_cache_id() -> str:
        cached_id = str(session.get("sudo_cache_id", "")).strip()
        if cached_id:
            return cached_id
        cached_id = str(uuid.uuid4())
        session["sudo_cache_id"] = cached_id
        return cached_id

    def get_cached_sudo_password() -> str | None:
        cache_id = str(session.get("sudo_cache_id", "")).strip()
        if not cache_id:
            return None
        with sudo_cache_lock:
            return session_sudo_cache.get(cache_id)

    def set_cached_sudo_password(password: str) -> None:
        cache_id = get_or_create_sudo_cache_id()
        with sudo_cache_lock:
            session_sudo_cache[cache_id] = password

    def transform_sudo_command(command: str, sudo_password: str | None) -> Tuple[str, str | None]:
        stripped = command.lstrip()
        leading = command[: len(command) - len(stripped)]

        if not stripped.startswith("sudo "):
            return command, None

        remainder = stripped[len("sudo ") :]
        if sudo_password:
            return f"{leading}sudo -S -p '' {remainder}", f"{sudo_password}\n"

        return f"{leading}sudo -n {remainder}", None

    def should_sync_model_registry(action_id: str) -> bool:
        sync_actions = {
            "train-secids",
            "train-unified",
            "test-model",
            "compare-models",
            "pipeline-train",
            "simulate-ddos-training-loop",
            "view-model-info",
            "list-models",
        }
        return action_id in sync_actions

    def get_public_user_record(username: str, record: Dict) -> Dict:
        age_days = password_age_days(record)
        rotation_due = is_rotation_due(record)
        return {
            "username": username,
            "role": str(record.get("role", "viewer")),
            "active": bool(record.get("active", True)),
            "must_change_password": bool(record.get("must_change_password", False)),
            "password_changed_at": record.get("password_changed_at"),
            "password_age_days": age_days,
            "rotation_due": rotation_due,
        }

    def record_audit(event: str, status: str, details: Dict | None = None) -> None:
        identity = resolve_identity()
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "status": status,
            "role": identity["role"],
            "user": identity["username"],
            "auth_method": identity["auth_method"],
            "details": details or {},
        }
        audit_events.appendleft(payload)
        AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def required_role_for_action(action_id: str, command: str) -> str:
        viewer_actions = {
            "list-results",
            "list-threat-reports",
            "list-deep-scan-reports",
            "view-latest-report",
            "view-system-logs",
            "list-datasets",
            "list-models",
            "list-captures",
            "history-view",
        }

        if action_id in viewer_actions:
            return "viewer"
        if command.strip().startswith("sudo "):
            return "operator"
        return "operator"

    def enforce_role(required_role: str):
        identity = resolve_identity()
        if identity.get("must_change_password"):
            return jsonify({"error": "Password change required before this operation"}), 403
        if has_required_role(identity["role"], required_role):
            return None

        record_audit(
            "authorization",
            "denied",
            {
                "required_role": required_role,
                "current_role": identity["role"],
                "path": request.path,
                "method": request.method,
            },
        )
        return jsonify({"error": f"Forbidden: requires {required_role} role", "current_role": identity["role"]}), 403

    @app.before_request
    def enforce_session_timeout():
        username = session.get("username")
        if not username:
            return None

        now = time.time()
        last_seen = float(session.get("last_seen_at", now))
        timeout_seconds = int(app.config.get("SECIDS_SESSION_TIMEOUT_SECONDS", SESSION_TIMEOUT_SECONDS))

        exempt_paths = {
            "/api/auth/login",
            "/api/auth/logout",
            "/api/auth/session",
        }
        is_static = request.path.startswith("/static/")

        if timeout_seconds > 0 and (now - last_seen) > timeout_seconds:
            clear_auth_session()
            if request.path.startswith("/api"):
                return jsonify({"error": "Session timed out", "code": "SESSION_TIMEOUT"}), 401
            if request.path in exempt_paths or is_static:
                return None
            return redirect(app.config["SECIDS_LOGIN_PATH"])

        session["last_seen_at"] = now
        if str(session.get("role", "")).strip() == "guest":
            touch_guest_presence()
        return None

    @app.before_request
    def enforce_authenticated_api():
        path = request.path
        if not path.startswith("/api"):
            return None

        if path in {
            "/api/auth/login",
            "/api/auth/session",
            "/api/auth/logout",
        }:
            return None

        identity = resolve_identity()
        if not identity.get("authenticated"):
            return jsonify({"error": "Login required"}), 401

        return None

    @app.before_request
    def enforce_password_change_gate():
        path = request.path
        if not path.startswith("/api"):
            return None

        if path in {"/api/auth/login", "/api/auth/session", "/api/auth/logout", "/api/auth/change-password"}:
            return None

        identity = resolve_identity()
        if identity.get("must_change_password"):
            return jsonify({"error": "Password change required", "code": "PASSWORD_CHANGE_REQUIRED"}), 403

        return None

    def append_log(job_id: str, line: str) -> None:
        with jobs_lock:
            if job_id not in jobs:
                return
            jobs[job_id]["logs"].append(line.rstrip("\n"))
            if len(jobs[job_id]["logs"]) > 1200:
                jobs[job_id]["logs"] = jobs[job_id]["logs"][-1200:]

    def running_jobs_count() -> int:
        return len([job for job in jobs.values() if job["status"] == "running"])

    def queue_snapshot() -> List[Dict]:
        snapshot = []
        for job_id in list(queue):
            job = jobs.get(job_id)
            if not job:
                continue
            snapshot.append(
                {
                    "id": job_id,
                    "title": job["title"],
                    "status": job["status"],
                    "timeout_seconds": job["timeout_seconds"],
                    "started_at": job["started_at"],
                }
            )
        return snapshot

    def create_job(action_id: str, title: str, mode: str, command: str | None, timeout_seconds: int) -> str:
        job_id = str(uuid.uuid4())
        identity = resolve_identity()
        sudo_cache_id = str(session.get("sudo_cache_id", "")).strip()
        with jobs_lock:
            jobs[job_id] = {
                "id": job_id,
                "action_id": action_id,
                "title": title,
                "mode": mode,
                "command": command,
                "status": "queued",
                "return_code": None,
                "cancel_requested": False,
                "pause_requested": False,
                "timeout_seconds": timeout_seconds,
                "submitted_by": identity["username"],
                "submitted_role": identity["role"],
                "sudo_cache_id": sudo_cache_id or None,
                "logs": [f"[init] action={action_id}"] + ([f"[command] {command}"] if command else []),
                "started_at": datetime.utcnow().isoformat(),
                "ended_at": None,
            }
        return job_id

    def complete_job(job_id: str, status: str, return_code: int, extra_logs: List[str]) -> None:
        action_id = ""
        job_snapshot: Dict[str, Any] = {}
        with jobs_lock:
            if job_id not in jobs:
                return
            action_id = str(jobs[job_id].get("action_id", ""))
            jobs[job_id]["status"] = status
            jobs[job_id]["return_code"] = return_code
            jobs[job_id]["logs"].extend(extra_logs)
            jobs[job_id]["ended_at"] = datetime.utcnow().isoformat()
            job_snapshot = {
                "id": jobs[job_id].get("id"),
                "title": jobs[job_id].get("title"),
                "action_id": jobs[job_id].get("action_id"),
                "submitted_by": jobs[job_id].get("submitted_by"),
                "submitted_role": jobs[job_id].get("submitted_role"),
                "command": jobs[job_id].get("command"),
                "status": jobs[job_id].get("status"),
                "return_code": jobs[job_id].get("return_code"),
                "started_at": jobs[job_id].get("started_at"),
                "ended_at": jobs[job_id].get("ended_at"),
                "logs_tail": list(jobs[job_id].get("logs", [])[-120:]),
            }

        if status == "completed" and should_sync_model_registry(action_id):
            try:
                sync_result = model_registry.sync_from_directories(model_registry_dirs, source=f"job:{action_id}")
                with jobs_lock:
                    if job_id in jobs:
                        jobs[job_id]["logs"].append(
                            "[model-registry] synced: "
                            f"{sync_result['updated']} updated / {sync_result['scanned']} scanned "
                            f"(total {sync_result['total_models']})"
                        )
            except Exception as exc:
                with jobs_lock:
                    if job_id in jobs:
                        jobs[job_id]["logs"].append(f"[model-registry] sync failed: {exc}")

        if action_id == "simulate-ddos-training-loop" and job_snapshot:
            artifacts = parse_simulation_artifact_paths(job_snapshot.get("logs_tail", []))
            staged_dataset = stage_nist_csw_file(artifacts.get("dataset", ""), "output")
            staged_report = stage_nist_csw_file(artifacts.get("report", ""), "output")
            append_server_snapshot(
                "nist_csw",
                "SIMULATION_OUTPUT",
                {
                    "job": job_snapshot,
                    "artifacts": {
                        "dataset": artifacts.get("dataset", ""),
                        "report": artifacts.get("report", ""),
                        "staged_dataset": staged_dataset,
                        "staged_report": staged_report,
                    },
                },
            )

    def execute_job(job_id: str, command: str, timeout_seconds: int) -> None:
        stdin_payload: str | None = None
        execution_command = command

        with jobs_lock:
            if job_id not in jobs:
                return
            jobs[job_id]["status"] = "running"
            sudo_cache_id = str(jobs[job_id].get("sudo_cache_id") or "").strip()

        if command.strip().startswith("sudo "):
            sudo_password: str | None = None
            if sudo_cache_id:
                with sudo_cache_lock:
                    sudo_password = session_sudo_cache.get(sudo_cache_id)
            execution_command, stdin_payload = transform_sudo_command(command, sudo_password)
            if not sudo_password:
                append_log(
                    job_id,
                    "[auth] No cached sudo password for this session. Using non-interactive sudo (-n).",
                )
                append_log(
                    job_id,
                    "[auth] To avoid sudo prompts, set passwordless sudo or use Execution Logs > Sudo Password Validation panel.",
                )

        append_ui_history(command)
        process = None
        timed_out = False
        graceful_stop_requested = False

        try:
            env_vars = os.environ.copy()
            env_vars.setdefault("PYTHONUNBUFFERED", "1")

            process = subprocess.Popen(
                execution_command,
                shell=True,
                cwd=PROJECT_ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                executable="/bin/bash",
                env=env_vars,
            )

            if stdin_payload is not None and process.stdin:
                process.stdin.write(stdin_payload)
                process.stdin.flush()
                process.stdin.close()
            elif process.stdin:
                process.stdin.close()

            with jobs_lock:
                active_processes[job_id] = process

            start_time = time.monotonic()
            last_progress_note = start_time
            stdout_handle = process.stdout

            while True:
                with jobs_lock:
                    job_state = jobs.get(job_id, {})
                    job_status = str(job_state.get("status", ""))
                    cancel_requested = bool(job_state.get("cancel_requested"))
                    pause_requested = bool(job_state.get("pause_requested"))

                if job_status == "cancelled":
                    break

                if cancel_requested:
                    graceful_stop_requested = True
                    append_log(job_id, "[cancel] Graceful stop requested. Finalizing with currently collected data.")
                    if process and process.poll() is None:
                        try:
                            process.send_signal(signal.SIGCONT)
                        except Exception:
                            pass
                        try:
                            process.terminate()
                        except Exception as exc:
                            append_log(job_id, f"[warn] Failed to terminate process cleanly: {exc}")
                    break

                if pause_requested:
                    with jobs_lock:
                        if job_id in jobs and jobs[job_id].get("status") != "paused":
                            jobs[job_id]["status"] = "paused"
                            jobs[job_id]["logs"].append("[pause] Task paused by user")

                    if process and process.poll() is None:
                        try:
                            process.send_signal(signal.SIGSTOP)
                        except Exception as exc:
                            append_log(job_id, f"[warn] Could not pause process: {exc}")

                    time.sleep(0.25)
                    continue
                else:
                    with jobs_lock:
                        if job_id in jobs and jobs[job_id].get("status") == "paused":
                            jobs[job_id]["status"] = "running"

                if process.poll() is not None:
                    break

                if timeout_seconds > 0 and (time.monotonic() - start_time) > timeout_seconds:
                    timed_out = True
                    append_log(job_id, f"[timeout] Job exceeded {timeout_seconds} seconds")
                    process.terminate()
                    time.sleep(0.5)
                    if process.poll() is None:
                        process.kill()
                    break

                now = time.monotonic()
                if now - last_progress_note >= 10:
                    elapsed = int(now - start_time)
                    append_log(job_id, f"[running] Job active for {elapsed}s; waiting for next output...")
                    last_progress_note = now

                if stdout_handle is not None:
                    ready, _, _ = select.select([stdout_handle], [], [], 0.25)
                    if ready:
                        line = stdout_handle.readline()
                        if line:
                            append_log(job_id, line)

            if process and process.stdout:
                tail = process.stdout.read()
                if tail:
                    for line in tail.splitlines():
                        append_log(job_id, line)

            return_code = process.wait() if process else -1

            with jobs_lock:
                final_status = jobs.get(job_id, {}).get("status")
            if final_status == "cancelled":
                return

            if graceful_stop_requested:
                complete_job(job_id, "completed", 0, ["[complete] Auto-completed using currently collected data"])
                return

            if timed_out:
                complete_job(job_id, "timeout", 124, ["[timeout] Job terminated by timeout policy"])
            else:
                complete_job(job_id, "completed" if return_code == 0 else "failed", return_code, [])
        except Exception as exc:
            complete_job(job_id, "failed", -1, [f"[error] {exc}"])
        finally:
            with jobs_lock:
                active_processes.pop(job_id, None)

    def queue_command_job(action_id: str, title: str, mode: str, command: str, timeout_seconds: int) -> Tuple[str, str]:
        job_id = create_job(action_id, title, mode, command, timeout_seconds)

        if mode == "simulation":
            complete_job(
                job_id,
                "completed",
                0,
                [
                    "[simulation] Command not executed.",
                    "[simulation] Use Realtime mode to run this action on Kali Linux.",
                ],
            )
            return job_id, "completed"

        with jobs_lock:
            queue.append(job_id)
            jobs[job_id]["logs"].append(f"[queue] Added to queue (position {len(queue)})")
        return job_id, "queued"

    def dispatch_loop() -> None:
        nonlocal queue_paused
        while True:
            time.sleep(0.2)
            with jobs_lock:
                if queue_paused:
                    continue

                while queue and running_jobs_count() < max_concurrent_jobs:
                    job_id = queue.popleft()
                    job = jobs.get(job_id)
                    if not job or job["status"] != "queued" or not job.get("command"):
                        continue
                    thread = threading.Thread(
                        target=execute_job,
                        args=(job_id, job["command"], int(job.get("timeout_seconds") or DEFAULT_JOB_TIMEOUT_SECONDS)),
                        daemon=True,
                    )
                    thread.start()

    dispatcher = threading.Thread(target=dispatch_loop, daemon=True)
    dispatcher.start()

    def apply_settings_update(params: Dict[str, str]) -> List[str]:
        settings = load_ui_settings()
        logs = []
        int_keys = {"last_duration", "last_window", "last_interval", "ws_font_size", "ws_statistics_interval"}
        bool_keys = {
            "ws_packet_list_visible",
            "ws_packet_details_visible",
            "ws_packet_bytes_visible",
            "ws_show_column_number",
            "ws_show_column_time",
            "ws_show_column_source",
            "ws_show_column_destination",
            "ws_show_column_protocol",
            "ws_show_column_length",
            "ws_show_column_info",
            "ws_colorize_packet_list",
            "ws_resolve_mac",
            "ws_resolve_network",
            "ws_resolve_transport",
            "ws_capture_promisc_mode",
            "ws_capture_monitor_mode",
            "ws_capture_update_realtime",
            "ws_enable_filter_buttons",
            "ws_expert_custom_enabled",
            "ws_advanced_show_changed_only",
            "ws_statistics_auto_update",
        }
        str_keys = {
            "last_interface",
            "theme",
            "live_model_mode",
            "live_model_path",
            "live_backend",
            "countermeasure_mode",
            "ws_theme",
            "ws_language",
            "ws_layout_profile",
            "ws_font_family",
            "ws_filter_profile",
            "ws_protocols_enabled_profile",
            "ws_expert_severity_policy",
            "ws_rsa_keys_profile",
            "ws_advanced_search_text",
        }
        allowed_keys = int_keys | bool_keys | str_keys

        for key, raw_value in params.items():
            if key not in allowed_keys:
                continue

            if key in int_keys:
                try:
                    settings[key] = int(str(raw_value))
                except ValueError:
                    logs.append(f"[warn] Invalid integer for {key}: {raw_value}")
                    continue
            elif key in bool_keys:
                if isinstance(raw_value, bool):
                    settings[key] = raw_value
                else:
                    settings[key] = str(raw_value).strip().lower() in {"1", "true", "yes", "on"}
            else:
                value = str(raw_value)
                if key == "live_model_mode":
                    candidate = value.strip().lower()
                    if candidate not in {"auto", "manual"}:
                        logs.append(f"[warn] Invalid live model mode for {key}: {raw_value}")
                        continue
                    settings[key] = candidate
                elif key == "live_backend":
                    candidate = value.strip().lower()
                    if candidate not in {"", "tf", "unified"}:
                        logs.append(f"[warn] Invalid backend for {key}: {raw_value}")
                        continue
                    settings[key] = candidate
                elif key == "countermeasure_mode":
                    candidate = value.strip().lower()
                    if candidate not in {"active", "passive"}:
                        logs.append(f"[warn] Invalid countermeasure mode for {key}: {raw_value}")
                        continue
                    settings[key] = candidate
                elif key in str_keys:
                    settings[key] = value.strip()
                else:
                    settings[key] = value

            logs.append(f"[settings] {key}={settings[key]}")

        save_ui_settings(settings)
        ensure_passive_packet_capture(settings, logs)
        if not logs:
            logs.append("[settings] No recognized setting keys provided")
        return logs

    def load_combined_history(limit: int = 50) -> List[Dict]:
        ui_history = load_ui_settings().get("history", [])
        cmd_history = load_command_history()

        merged = []
        for item in ui_history:
            merged.append(
                {
                    "timestamp": item.get("timestamp", ""),
                    "command": item.get("command", ""),
                    "source": "ui",
                    "success": None,
                }
            )
        for item in cmd_history:
            merged.append(
                {
                    "timestamp": item.get("timestamp", ""),
                    "command": item.get("command", item.get("shortcut", "")),
                    "source": "command_library",
                    "success": item.get("success"),
                }
            )

        merged.sort(key=lambda entry: entry.get("timestamp", ""), reverse=True)
        return merged[:limit]

    def get_packet_capture_status() -> Dict[str, str | bool | int]:
        with packet_capture_lock:
            return {
                "running": packet_capture_running,
                "paused": packet_capture_paused,
                "interface": packet_capture_interface or "-",
                "source": packet_capture_source or "-",
                "managed_mode": "auto" if packet_capture_auto_managed else "manual",
                "rows": len(packet_capture_rows),
                "last_error": packet_capture_last_error,
            }

    def parse_tcpdump_line(line: str) -> Dict[str, str]:
        src = "-"
        dst = "-"
        protocol = "-"
        length = "-"
        info = line[:220]

        proto_match = re.search(r"\b(IP6?|ARP|ICMP|UDP|TCP|DNS|TLS|HTTP|HTTPS)\b", line, re.IGNORECASE)
        if proto_match:
            protocol = proto_match.group(1).upper()

        ip_pair = re.search(r"((?:\d{1,3}\.){3}\d{1,3})(?:\.\d+)?\s*>\s*((?:\d{1,3}\.){3}\d{1,3})(?:\.\d+)?", line)
        if ip_pair:
            src = ip_pair.group(1)
            dst = ip_pair.group(2)

        length_match = re.search(r"length\s+(\d+)", line, re.IGNORECASE)
        if length_match:
            length = length_match.group(1)

        flags = extract_standard_packet_flags(line)
        model_flags = extract_model_flags(line, "running")
        return {
            "source": src,
            "destination": dst,
            "protocol": protocol,
            "length": length,
            "flags": ",".join(flags) if flags else "-",
            "model_flags": ",".join(model_flags) if model_flags else "-",
            "info": info,
        }

    def parse_tshark_line(line: str) -> Dict[str, str] | None:
        parts = line.split("\t")
        padded = (parts + [""] * 9)[:9]
        _, src4, dst4, src6, dst6, protocol_raw, length, tcp_flags, info = [part.strip() for part in padded]
        src = src4 or src6
        dst = dst4 or dst6
        protocol = protocol_raw.split(":")[-1].upper() if protocol_raw else "-"
        flags = extract_standard_packet_flags(f"{tcp_flags} {info}")
        model_flags = extract_model_flags(info, "running")

        normalized_info = (info or "-")[:220]
        if not src and not dst and protocol == "-" and normalized_info in {"-", ""}:
            return None

        return {
            "source": src or "-",
            "destination": dst or "-",
            "protocol": protocol,
            "length": length or "-",
            "flags": ",".join(flags) if flags else "-",
            "model_flags": ",".join(model_flags) if model_flags else "-",
            "info": normalized_info,
        }

    def stop_packet_capture(reason: str = "stopped") -> Tuple[bool, str]:
        nonlocal packet_capture_process, packet_capture_running, packet_capture_paused, packet_capture_last_error
        nonlocal packet_capture_auto_managed

        with packet_capture_lock:
            process = packet_capture_process
            was_running = packet_capture_running
            packet_capture_paused = False

        if not was_running and process is None:
            return True, "Packet capture already stopped"

        if process and process.poll() is None:
            process.terminate()
            time.sleep(0.4)
            if process.poll() is None:
                process.kill()

        with packet_capture_lock:
            packet_capture_running = False
            packet_capture_process = None
            packet_capture_auto_managed = False
            packet_capture_last_error = "" if reason == "stopped" else reason

        return True, f"Packet capture {reason}"

    def packet_capture_reader_loop(process: subprocess.Popen, source: str) -> None:
        nonlocal packet_capture_running, packet_capture_process, packet_capture_sequence, packet_capture_last_error

        stdout_handle = process.stdout
        if stdout_handle is None:
            with packet_capture_lock:
                packet_capture_running = False
                packet_capture_process = None
                packet_capture_last_error = "Packet capture stdout unavailable"
            return

        for raw_line in iter(stdout_handle.readline, ""):
            line = str(raw_line or "").strip()
            if not line:
                continue

            with packet_capture_lock:
                paused = packet_capture_paused
            if paused:
                continue

            parsed = parse_tshark_line(line) if source == "tshark" else parse_tcpdump_line(line)
            if parsed is None:
                continue
            with packet_capture_lock:
                packet_capture_rows.appendleft(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "number": str(packet_capture_sequence),
                        "source": parsed["source"],
                        "destination": parsed["destination"],
                        "protocol": parsed["protocol"],
                        "length": parsed["length"],
                        "flags": parsed["flags"],
                        "model_flags": parsed["model_flags"],
                        "info": parsed["info"],
                    }
                )
                packet_capture_sequence += 1

        return_code = process.poll()
        if return_code not in {None, 0}:
            try:
                tail = (process.stdout.read() or "").strip()
            except Exception:
                tail = ""
            with packet_capture_lock:
                packet_capture_last_error = tail[:240] if tail else f"capture process exited with code {return_code}"

        with packet_capture_lock:
            packet_capture_running = False
            if packet_capture_process is process:
                packet_capture_process = None

    def start_packet_capture(interface: str, auto: bool = False) -> Tuple[bool, str]:
        nonlocal packet_capture_process, packet_capture_running, packet_capture_paused
        nonlocal packet_capture_interface, packet_capture_source, packet_capture_last_error, packet_capture_reader
        nonlocal packet_capture_last_attempt_at
        nonlocal packet_capture_auto_managed

        iface = (interface or "eth0").strip() or "eth0"

        with packet_capture_lock:
            if packet_capture_running and packet_capture_process is not None:
                if packet_capture_paused:
                    packet_capture_paused = False
                    if not auto:
                        packet_capture_auto_managed = False
                    return True, "Packet capture resumed"
                if not auto:
                    packet_capture_auto_managed = False
                return True, "Packet capture already running"

        with packet_capture_lock:
            packet_capture_last_attempt_at = time.time()

        candidates = [
            ("tcpdump", f"tcpdump -l -n -i {shlex.quote(iface)} -tttt"),
            ("tcpdump", f"sudo -n tcpdump -l -n -i {shlex.quote(iface)} -tttt"),
            (
                "tshark",
                f"tshark -l -n -i {shlex.quote(iface)} -T fields "
                "-E separator=/t "
                "-e frame.time_epoch -e ip.src -e ip.dst -e ipv6.src -e ipv6.dst -e frame.protocols -e frame.len -e tcp.flags.str -e _ws.col.Info",
            ),
            (
                "tshark",
                f"sudo -n tshark -l -n -i {shlex.quote(iface)} -T fields "
                "-E separator=/t "
                "-e frame.time_epoch -e ip.src -e ip.dst -e ipv6.src -e ipv6.dst -e frame.protocols -e frame.len -e tcp.flags.str -e _ws.col.Info",
            ),
        ]

        last_error = "No packet capture backend available"
        for source, command in candidates:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                executable="/bin/bash",
            )

            time.sleep(0.5)
            if process.poll() is not None:
                try:
                    output, _ = process.communicate(timeout=0.2)
                except Exception:
                    output = ""
                cleaned = (output or "").strip()
                last_error = cleaned[:240] if cleaned else f"{source} exited before capture started"
                continue

            with packet_capture_lock:
                packet_capture_process = process
                packet_capture_running = True
                packet_capture_paused = False
                packet_capture_interface = iface
                packet_capture_source = source
                packet_capture_auto_managed = auto
                packet_capture_last_error = ""

            reader = threading.Thread(target=packet_capture_reader_loop, args=(process, source), daemon=True)
            reader.start()
            with packet_capture_lock:
                packet_capture_reader = reader
            if auto:
                return True, f"Packet capture auto-started on {iface} via {source}"
            return True, f"Packet capture started on {iface} via {source}"

        with packet_capture_lock:
            packet_capture_last_error = last_error
            packet_capture_running = False
            packet_capture_process = None
            packet_capture_auto_managed = False

        return False, f"Packet capture failed: {last_error}"

    def pause_packet_capture() -> Tuple[bool, str]:
        nonlocal packet_capture_paused
        with packet_capture_lock:
            if not packet_capture_running:
                return False, "Packet capture is not running"
            packet_capture_paused = True
        return True, "Packet capture paused"

    def ensure_passive_packet_capture(settings: Dict, logs: List[str] | None = None) -> None:
        nonlocal packet_capture_auto_managed
        mode = str(settings.get("countermeasure_mode", "active") or "active").strip().lower()
        if mode != "passive":
            status = get_packet_capture_status()
            is_auto_managed = bool(status.get("managed_mode") == "auto")
            if status.get("running") and is_auto_managed:
                _, message = stop_packet_capture("stopped")
                if logs is not None:
                    logs.append("[packet-capture] Auto capture stopped in active mode")
                record_audit("packet_capture_auto_stop", "ok", {"message": message, "mode": mode})
            return

        iface = str(settings.get("last_interface", "eth0") or "eth0").strip() or "eth0"
        status = get_packet_capture_status()
        with packet_capture_lock:
            last_attempt_at = packet_capture_last_attempt_at
        if (time.time() - float(last_attempt_at)) < 20:
            return

        if status.get("running") and str(status.get("interface")) == iface:
            return

        if status.get("running"):
            stop_packet_capture("restarting")

        ok, message = start_packet_capture(iface, auto=True)
        if logs is not None:
            logs.append(f"[packet-capture] {message}")
        record_audit("packet_capture_auto_start", "ok" if ok else "failed", {"interface": iface, "message": message})

    def derive_action_activity(log_text: str) -> str:
        normalized = log_text.lower()
        if normalized.startswith("[init]"):
            return "init"
        if normalized.startswith("[command]"):
            return "command"
        if normalized.startswith("[queue]"):
            return "queue"
        if normalized.startswith("[running]"):
            return "running"
        if normalized.startswith("[timeout]"):
            return "timeout"
        if normalized.startswith("[auth]"):
            return "auth"
        if normalized.startswith("[error]"):
            return "error"
        if normalized.startswith("[model-registry]"):
            return "model-registry"
        if "stage " in normalized:
            return "workflow-stage"
        if "capture" in normalized or "packet" in normalized:
            return "capture"
        if "countermeasure" in normalized:
            return "countermeasure"
        return "activity"

    def load_action_log_preview(limit: int = 120) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []

        with jobs_lock:
            ordered_jobs = sorted(jobs.values(), key=lambda item: item.get("started_at", ""), reverse=True)

        for job in ordered_jobs:
            started_at = str(job.get("started_at", ""))
            action_id = str(job.get("action_id", ""))
            status = str(job.get("status", ""))
            operator = str(job.get("submitted_by", "")) or "-"
            mode = str(job.get("mode", "")) or "-"
            job_id = str(job.get("id", ""))
            return_code = job.get("return_code")

            for line in reversed(job.get("logs", [])):
                text = str(line or "").strip()
                if not text:
                    continue

                details = [f"job={job_id[:8]}"]
                if return_code is not None:
                    details.append(f"rc={return_code}")
                ended_at = str(job.get("ended_at", ""))
                if ended_at:
                    details.append(f"ended={ended_at}")

                rows.append(
                    {
                        "timestamp": started_at,
                        "action_id": action_id,
                        "status": status,
                        "operator": operator,
                        "mode": mode,
                        "activity": derive_action_activity(text),
                        "message": text,
                        "details": " | ".join(details),
                    }
                )
                if len(rows) >= limit:
                    return rows
        return rows

    def extract_model_flags(log_text: str, status: str) -> List[str]:
        text = log_text.lower()
        flags: List[str] = []

        keyword_flags = [
            ("malicious", "MALICIOUS"),
            ("benign", "BENIGN"),
            ("anomaly", "ANOMALY"),
            ("ddos", "DDOS"),
            ("threat", "THREAT"),
            ("countermeasure", "COUNTERMEASURE"),
            ("mitigat", "MITIGATED"),
            ("blacklist", "BLACKLIST"),
            ("greylist", "GREYLIST"),
            ("whitelist", "WHITELIST"),
            ("drop", "DROPPED"),
            ("block", "BLOCKED"),
        ]
        for needle, label in keyword_flags:
            if needle in text and label not in flags:
                flags.append(label)

        confidence_match = re.search(r"confidence\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", text)
        if confidence_match:
            flags.append(f"CONF={confidence_match.group(1)}")

        if status.lower() == "failed" and "ERROR" not in flags:
            flags.append("ERROR")

        return flags

    def extract_standard_packet_flags(log_text: str) -> List[str]:
        upper = log_text.upper()
        standard = ["SYN", "ACK", "FIN", "RST", "PSH", "URG", "ECE", "CWR"]
        return [flag for flag in standard if flag in upper]

    def load_packet_flow_preview(limit: int = 120) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []

        with packet_capture_lock:
            live_rows = list(packet_capture_rows)

        for row in live_rows[:limit]:
            rows.append(row)
        if len(rows) >= limit:
            return rows

        with jobs_lock:
            ordered_jobs = sorted(jobs.values(), key=lambda item: item.get("started_at", ""), reverse=True)

        packet_hint = re.compile(
            r"packet|flow|capture|src|dst|tcp|udp|icmp|arp|dns|http|https|syn|ack|fin|rst|psh|urg",
            re.IGNORECASE,
        )
        ip_regex = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")
        proto_regex = re.compile(r"\b(TCP|UDP|ICMP|ARP|DNS|HTTP|HTTPS|TLS)\b", re.IGNORECASE)
        len_regex = re.compile(r"(?:len|length|size)\s*[:=]?\s*(\d{1,6})", re.IGNORECASE)

        sequence_number = len(rows) + 1
        for job in ordered_jobs:
            started_at = str(job.get("started_at", ""))
            status = str(job.get("status", ""))

            for line in reversed(job.get("logs", [])):
                text = str(line or "").strip()
                if not text or not packet_hint.search(text):
                    continue

                ip_matches = ip_regex.findall(text)
                src = ip_matches[0] if len(ip_matches) >= 1 else "-"
                dst = ip_matches[1] if len(ip_matches) >= 2 else "-"

                proto_match = proto_regex.search(text)
                protocol = proto_match.group(1).upper() if proto_match else "-"

                length_match = len_regex.search(text)
                length = length_match.group(1) if length_match else "-"

                standard_flags = extract_standard_packet_flags(text)
                model_flags = extract_model_flags(text, status)

                rows.append(
                    {
                        "timestamp": started_at,
                        "number": str(sequence_number),
                        "source": src,
                        "destination": dst,
                        "protocol": protocol,
                        "length": length,
                        "flags": ",".join(standard_flags) if standard_flags else "-",
                        "model_flags": ",".join(model_flags) if model_flags else "-",
                        "info": text[:220],
                    }
                )
                sequence_number += 1
                if len(rows) >= limit:
                    return rows

        return rows

    def run_internal_action(internal_action: str, params: Dict[str, str]) -> Tuple[bool, List[str], str | None]:
        if internal_action == "settings_update":
            logs = apply_settings_update(params)
            logs.append("[ok] Settings saved")
            return True, logs, None

        if internal_action == "history_view":
            entries = load_combined_history(limit=20)
            if not entries:
                return True, ["[history] No entries"], None
            lines = [f"[history] {entry['timestamp']} | {entry['source']} | {entry['command']}" for entry in entries]
            return True, lines, None

        if internal_action == "history_clear":
            settings = load_ui_settings()
            settings["history"] = []
            save_ui_settings(settings)
            save_command_history([])
            return True, ["[ok] History cleared"], None

        if internal_action == "history_rerun_last":
            requested_command = params.get("command", "").strip()
            if requested_command:
                return True, [f"[history] Rerunning selected command: {requested_command}"], requested_command

            entries = load_combined_history(limit=1)
            if not entries or not entries[0].get("command"):
                return False, ["[error] No history command available to rerun"], None
            command = entries[0]["command"]
            return True, [f"[history] Rerunning: {command}"], command

        return False, [f"[error] Unsupported internal action: {internal_action}"], None

    def get_scheduler_status() -> str:
        scheduler_status = subprocess.run(
            "pgrep -f '[A]uto_Update/task_scheduler.py' >/dev/null && echo running || echo stopped",
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        return scheduler_status.stdout.strip()

    def get_network_interfaces(limit: int = 10) -> List[str]:
        result = subprocess.run(
            "ip -o link show | awk -F': ' '{print $2}' | sed 's/@.*//'",
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []

        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return names[: max(1, limit)]

    list_status_cache: Dict[str, Any] = {
        "signature": (),
        "whitelist": set(),
        "blacklist": set(),
        "greylist": set(),
        "intruder": set(),
        "unidentified": set(),
    }

    IDENTIFICATION_TAGS = ("whitelist", "blacklist", "greylist", "intruder", "unidentified")
    IDENTIFICATION_FILE_MAP = {
        "whitelist": PROJECT_ROOT / "Device_Profile" / "whitelists" / "webui_identification_whitelist.json",
        "blacklist": PROJECT_ROOT / "Device_Profile" / "Blacklist" / "webui_identification_blacklist.json",
        "greylist": PROJECT_ROOT / "Device_Profile" / "greylist" / "webui_identification_greylist.json",
        "intruder": PROJECT_ROOT / "Device_Profile" / "intruder" / "intruder_list.json",
        "unidentified": PROJECT_ROOT / "Device_Profile" / "unidentified" / "unidentified_list.json",
    }

    def _normalize_ip(value: Any) -> str | None:
        if value is None:
            return None
        try:
            return str(ipaddress.ip_address(str(value).strip()))
        except Exception:
            return None

    def _extract_ips_from_json(payload: Any, sink: set[str]) -> None:
        if isinstance(payload, dict):
            for key, value in payload.items():
                key_ip = _normalize_ip(key)
                if key_ip:
                    sink.add(key_ip)

                if isinstance(key, str) and key.lower() in {
                    "ip",
                    "ip_address",
                    "address",
                    "src_ip",
                    "dst_ip",
                    "host",
                }:
                    value_ip = _normalize_ip(value)
                    if value_ip:
                        sink.add(value_ip)

                _extract_ips_from_json(value, sink)
            return

        if isinstance(payload, list):
            for item in payload:
                _extract_ips_from_json(item, sink)
            return

        if isinstance(payload, str):
            value_ip = _normalize_ip(payload)
            if value_ip:
                sink.add(value_ip)

    def _json_files_signature(paths: List[Path]) -> Tuple[Tuple[str, int, int], ...]:
        signature: List[Tuple[str, int, int]] = []
        for path in sorted(paths):
            try:
                stat = path.stat()
                signature.append((str(path), int(stat.st_mtime), int(stat.st_size)))
            except OSError:
                continue
        return tuple(signature)

    def _load_ips_from_json_files(paths: List[Path]) -> set[str]:
        ips: set[str] = set()
        for path in paths:
            if not path.exists() or not path.is_file():
                continue
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                _extract_ips_from_json(payload, ips)
            except Exception:
                continue
        return ips

    def get_device_list_status_sets() -> Dict[str, set[str]]:
        whitelist_files = list((PROJECT_ROOT / "Device_Profile" / "whitelists").glob("*.json"))
        blacklist_files = list((PROJECT_ROOT / "Device_Profile" / "Blacklist").glob("*.json"))
        greylist_files = list((PROJECT_ROOT / "Device_Profile" / "greylist").glob("*.json"))
        intruder_files = list((PROJECT_ROOT / "Device_Profile" / "intruder").glob("*.json"))
        unidentified_files = list((PROJECT_ROOT / "Device_Profile" / "unidentified").glob("*.json"))

        combined_signature = (
            _json_files_signature(whitelist_files),
            _json_files_signature(blacklist_files),
            _json_files_signature(greylist_files),
            _json_files_signature(intruder_files),
            _json_files_signature(unidentified_files),
        )

        if combined_signature != list_status_cache["signature"]:
            list_status_cache["whitelist"] = _load_ips_from_json_files(whitelist_files)
            list_status_cache["blacklist"] = _load_ips_from_json_files(blacklist_files)
            list_status_cache["greylist"] = _load_ips_from_json_files(greylist_files)
            list_status_cache["intruder"] = _load_ips_from_json_files(intruder_files)
            list_status_cache["unidentified"] = _load_ips_from_json_files(unidentified_files)
            list_status_cache["signature"] = combined_signature

        return {
            "whitelist": set(list_status_cache["whitelist"]),
            "blacklist": set(list_status_cache["blacklist"]),
            "greylist": set(list_status_cache["greylist"]),
            "intruder": set(list_status_cache["intruder"]),
            "unidentified": set(list_status_cache["unidentified"]),
        }

    def _normalize_identification_tag(value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized == "graylist":
            normalized = "greylist"
        if normalized in {"attacker", "attackers", "intrusion", "intruder"}:
            normalized = "intruder"
        return normalized if normalized in IDENTIFICATION_TAGS else ""

    def _read_identification_file(path: Path) -> Dict[str, Any]:
        payload = read_json_file(path, {})
        if not isinstance(payload, dict):
            payload = {}
        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            entries = []
        payload["entries"] = entries
        return payload

    def _load_identification_entries() -> Dict[str, Dict[str, Any]]:
        entries: Dict[str, Dict[str, Any]] = {}
        for tag in IDENTIFICATION_TAGS:
            path = IDENTIFICATION_FILE_MAP[tag]
            payload = _read_identification_file(path)

            tagged_rows = payload.get("entries", [])
            if isinstance(tagged_rows, list):
                for row in tagged_rows:
                    if not isinstance(row, dict):
                        continue
                    ip_value = _normalize_ip(row.get("ip"))
                    if not ip_value:
                        continue
                    entries[ip_value] = {
                        "ip": ip_value,
                        "tag": tag,
                        "source": str(row.get("source", "persisted") or "persisted"),
                        "updated_at": str(row.get("updated_at", "") or ""),
                        "notes": str(row.get("notes", "") or ""),
                    }

            direct_ips = _load_ips_from_json_files([path])
            for ip_value in direct_ips:
                if ip_value not in entries:
                    entries[ip_value] = {
                        "ip": ip_value,
                        "tag": tag,
                        "source": "persisted",
                        "updated_at": "",
                        "notes": "",
                    }
        return entries

    def _write_identification_entries(entries: Dict[str, Dict[str, Any]]) -> None:
        grouped: Dict[str, List[Dict[str, Any]]] = {tag: [] for tag in IDENTIFICATION_TAGS}
        now_iso = datetime.utcnow().isoformat()

        for ip_value, row in entries.items():
            normalized_ip = _normalize_ip(ip_value)
            if not normalized_ip:
                continue
            tag = _normalize_identification_tag(row.get("tag"))
            if not tag:
                continue
            grouped[tag].append(
                {
                    "ip": normalized_ip,
                    "source": str(row.get("source", "manual") or "manual"),
                    "updated_at": str(row.get("updated_at", now_iso) or now_iso),
                    "notes": str(row.get("notes", "") or ""),
                }
            )

        for tag in IDENTIFICATION_TAGS:
            file_path = IDENTIFICATION_FILE_MAP[tag]
            rows = sorted(grouped[tag], key=lambda item: item.get("ip", ""))
            payload = {
                "tag": tag,
                "updated_at": now_iso,
                "entries": rows,
            }
            write_json_file(file_path, payload)

        # Invalidate cache after writes to ensure connected-device status is refreshed.
        list_status_cache["signature"] = ()

    def _build_identification_listing(include_runtime: bool = True) -> Dict[str, Any]:
        entries = _load_identification_entries()
        runtime_devices: List[Dict[str, Any]] = []

        if include_runtime:
            settings = load_ui_settings()
            iface = str(settings.get("last_interface", "eth0") or "eth0")
            runtime_devices = get_connected_devices(iface, limit=200)
            for device in runtime_devices:
                ip_value = _normalize_ip(device.get("ip"))
                if not ip_value:
                    continue
                runtime_tag = _normalize_identification_tag(device.get("list_status")) or "unidentified"
                if ip_value not in entries:
                    entries[ip_value] = {
                        "ip": ip_value,
                        "tag": runtime_tag,
                        "source": "runtime",
                        "updated_at": datetime.utcnow().isoformat(),
                        "notes": "",
                    }

        grouped_counts = {tag: 0 for tag in IDENTIFICATION_TAGS}
        grouped_counts["total"] = 0
        output_items: List[Dict[str, Any]] = []
        for ip_value in sorted(entries.keys()):
            row = entries[ip_value]
            tag = _normalize_identification_tag(row.get("tag")) or "unidentified"
            grouped_counts[tag] = grouped_counts.get(tag, 0) + 1
            grouped_counts["total"] += 1
            output_items.append(
                {
                    "ip": ip_value,
                    "tag": tag,
                    "source": str(row.get("source", "runtime") or "runtime"),
                    "updated_at": str(row.get("updated_at", "") or ""),
                    "notes": str(row.get("notes", "") or ""),
                }
            )

        return {
            "items": output_items,
            "counts": grouped_counts,
            "runtime_items": runtime_devices,
        }

    def get_connected_devices(interface: str, limit: int = 12) -> List[Dict[str, str]]:
        iface = str(interface or "").strip()
        if not iface:
            return []

        result = subprocess.run(
            f"ip neigh show dev {shlex.quote(iface)}",
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            executable="/bin/bash",
        )
        if result.returncode != 0:
            return []

        list_status_sets = get_device_list_status_sets()
        devices: List[Dict[str, str]] = []
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) < 4:
                continue

            ip = parts[0]
            mac = ""
            state = parts[-1]
            normalized_ip = _normalize_ip(ip)

            if normalized_ip in list_status_sets["blacklist"]:
                list_status = "blacklist"
            elif normalized_ip in list_status_sets["whitelist"]:
                list_status = "whitelist"
            elif normalized_ip in list_status_sets["greylist"]:
                list_status = "greylist"
            elif normalized_ip in list_status_sets["intruder"]:
                list_status = "intruder"
            elif normalized_ip in list_status_sets["unidentified"]:
                list_status = "unidentified"
            else:
                list_status = "unknown"

            if "lladdr" in parts:
                try:
                    mac = parts[parts.index("lladdr") + 1]
                except Exception:
                    mac = ""

            devices.append(
                {
                    "ip": ip,
                    "mac": mac,
                    "state": state,
                    "interface": iface,
                    "list_status": list_status,
                }
            )
            if len(devices) >= max(1, limit):
                break

        known_ips = {str(item.get("ip", "")).strip() for item in devices}
        for guest_device in get_guest_presence_devices():
            guest_ip = str(guest_device.get("ip", "")).strip()
            if not guest_ip or guest_ip in known_ips:
                continue
            devices.append(guest_device)
            known_ips.add(guest_ip)

        return devices

    BROWSER_HINTS = {
        "firefox",
        "chrome",
        "chromium",
        "brave",
        "edge",
        "opera",
        "vivaldi",
        "safari",
        "tor",
    }
    EMAIL_HINTS = {
        "thunderbird",
        "evolution",
        "kmail",
        "geary",
        "mutt",
        "alpine",
        "mail",
    }
    USB_HINTS = {
        "udisksd",
        "gvfsd-mtp",
        "mtp-probe",
        "usbguardd",
        "usbmuxd",
    }
    WEB_PORTS = {80, 443, 8080, 8443}
    EMAIL_PORTS = {25, 110, 143, 465, 587, 993, 995}
    DDOS_HINTS = ("ddos", "flood", "syn flood", "udp flood", "icmp flood", "botnet")
    ATTACK_HINTS = DDOS_HINTS + ("attack", "malicious", "blacklist", "threat", "anomaly")
    SIMULATION_HINTS = ("simulation", "simulate", "synthetic", "nist-csw", "training-loop", "red-team")
    IFF_FRIEND_TAGS = {"whitelist"}
    IFF_FOE_TAGS = {"blacklist", "intruder"}
    IFF_UNKNOWN_TAGS = {"greylist", "unidentified", "unknown"}

    def _iff_classification_from_status(list_status: Any) -> str:
        tag = str(list_status or "").strip().lower()
        if tag in IFF_FRIEND_TAGS:
            return "friend"
        if tag in IFF_FOE_TAGS:
            return "foe"
        if tag in IFF_UNKNOWN_TAGS:
            return "unknown"
        return "unknown"

    def _is_simulation_subroutine_active() -> bool:
        with jobs_lock:
            for job in jobs.values():
                action_id = str(job.get("action_id", "")).strip().lower()
                status = str(job.get("status", "")).strip().lower()
                if action_id == "simulate-ddos-training-loop" and status in {"queued", "running", "paused"}:
                    return True
        return False

    def classify_process_category(process_name: str, command: str = "") -> str:
        name = str(process_name or "").strip().lower()
        text = f"{name} {str(command or '').lower()}"
        if any(hint in text for hint in BROWSER_HINTS):
            return "browser"
        if any(hint in text for hint in EMAIL_HINTS):
            return "email"
        if any(hint in text for hint in USB_HINTS) or "usb" in text or "mtp" in text:
            return "usb"
        return "system"

    def parse_host_port(value: str) -> Tuple[str, int | None]:
        raw = str(value or "").strip()
        if not raw or raw == "*":
            return "", None

        if raw.startswith("[") and "]" in raw:
            host = raw[1 : raw.find("]")]
            remainder = raw[raw.find("]") + 1 :]
            if remainder.startswith(":"):
                try:
                    return host, int(remainder[1:])
                except ValueError:
                    return host, None
            return host, None

        host, sep, port_text = raw.rpartition(":")
        if not sep:
            return raw, None
        try:
            return host, int(port_text)
        except ValueError:
            return host or raw, None

    def infer_vector(category: str, remote_port: int | None, proc_name: str = "") -> str:
        proc_text = str(proc_name or "").lower()
        if category == "browser" or remote_port in WEB_PORTS:
            return "web"
        if category == "email" or remote_port in EMAIL_PORTS:
            return "email"
        if category == "usb" or "usb" in proc_text or "mtp" in proc_text:
            return "usb"
        return "network"

    def network_scope(remote_host: str) -> str:
        host = str(remote_host or "").strip()
        if not host:
            return "unknown"

        try:
            ip_obj = ipaddress.ip_address(host)
            if ip_obj.is_loopback:
                return "loopback"
            if ip_obj.is_private:
                return "lan"
            return "internet"
        except ValueError:
            return "internet"

    def collect_active_apps(limit: int = 24) -> List[Dict[str, Any]]:
        result = subprocess.run(
            "ps -eo pid=,comm=,args=",
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            executable="/bin/bash",
        )
        if result.returncode != 0:
            return []

        grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for line in result.stdout.splitlines():
            row = line.strip()
            if not row:
                continue

            parts = row.split(None, 2)
            if len(parts) < 2:
                continue

            pid_text = parts[0]
            process_name = parts[1]
            command = parts[2] if len(parts) > 2 else process_name
            try:
                pid_value = int(pid_text)
            except ValueError:
                continue

            category = classify_process_category(process_name, command)
            if category == "system":
                continue

            key = (category, process_name.lower())
            bucket = grouped.setdefault(
                key,
                {
                    "name": process_name,
                    "category": category,
                    "count": 0,
                    "pids": [],
                    "command": command[:180],
                },
            )
            bucket["count"] += 1
            if len(bucket["pids"]) < 6:
                bucket["pids"].append(pid_value)

        apps = list(grouped.values())
        apps.sort(key=lambda item: (0 if item.get("category") == "browser" else 1, -int(item.get("count", 0)), item.get("name", "")))
        return apps[: max(1, limit)]

    def collect_socket_connections(apps: List[Dict[str, Any]], limit: int = 80) -> List[Dict[str, Any]]:
        result = subprocess.run(
            "ss -tunpH",
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            executable="/bin/bash",
        )
        if result.returncode != 0:
            return []

        app_categories = {str(item.get("name", "")).lower(): str(item.get("category", "system")) for item in apps}
        rows: List[Dict[str, Any]] = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue

            proto = parts[0].upper()
            state_name = parts[1].upper()
            local_host, local_port = parse_host_port(parts[3])
            remote_host, remote_port = parse_host_port(parts[4])
            process_blob = " ".join(parts[5:]) if len(parts) > 5 else ""

            process_match = re.search(r'users:\(\("([^\"]+)"\s*,pid=(\d+)', process_blob)
            process_name = process_match.group(1) if process_match else "unknown"
            pid_value = int(process_match.group(2)) if process_match else None
            category = classify_process_category(process_name)
            if category == "system":
                category = app_categories.get(str(process_name).lower(), "system")

            vector = infer_vector(category, remote_port, process_name)
            rows.append(
                {
                    "protocol": proto,
                    "state": state_name,
                    "local": f"{local_host}:{local_port}" if local_host else "-",
                    "remote": f"{remote_host}:{remote_port}" if remote_host else "-",
                    "remote_host": remote_host,
                    "remote_port": remote_port,
                    "scope": network_scope(remote_host),
                    "process": process_name,
                    "pid": pid_value,
                    "category": category,
                    "vector": vector,
                }
            )

            if len(rows) >= max(10, limit):
                break

        return rows

    def summarize_control_surface_state(active_interface: str, connected_devices: List[Dict[str, str]]) -> Dict[str, Any]:
        apps = collect_active_apps(limit=24)
        connections = collect_socket_connections(apps, limit=90)
        packet_rows = load_packet_flow_preview(limit=220)

        vectors = sorted({str(row.get("vector", "network")) for row in connections if row.get("vector")})
        access_paths: List[Dict[str, str]] = []
        for row in connections[:40]:
            process_name = str(row.get("process", "unknown"))
            remote = str(row.get("remote", "-"))
            vector = str(row.get("vector", "network"))
            scope = str(row.get("scope", "unknown"))
            access_paths.append(
                {
                    "path": f"host -> {process_name} -> {remote}",
                    "vector": vector,
                    "scope": scope,
                }
            )

        friend_devices = [item for item in connected_devices if _iff_classification_from_status(item.get("list_status")) == "friend"]
        foe_devices = [item for item in connected_devices if _iff_classification_from_status(item.get("list_status")) == "foe"]
        unknown_devices = [item for item in connected_devices if _iff_classification_from_status(item.get("list_status")) == "unknown"]

        simulation_active = _is_simulation_subroutine_active()
        packet_blob = "\n".join(
            f"{row.get('protocol', '')} {row.get('model_flags', '')} {row.get('info', '')}" for row in packet_rows[:180]
        ).lower()
        ddos_hit = any(hint in packet_blob for hint in DDOS_HINTS)
        attack_hit = any(hint in packet_blob for hint in ATTACK_HINTS)
        simulation_hit = any(hint in packet_blob for hint in SIMULATION_HINTS)

        process_connection_counts: Dict[str, int] = {}
        for row in connections:
            key = str(row.get("process", "unknown")).lower()
            process_connection_counts[key] = process_connection_counts.get(key, 0) + 1

        max_fanout = max(process_connection_counts.values(), default=0)
        high_fanout_process = ""
        if process_connection_counts:
            high_fanout_process = max(process_connection_counts, key=process_connection_counts.get)

        signals: List[str] = []
        if unknown_devices:
            signals.append(f"Unidentified/blocked devices observed: {len(unknown_devices)}")
        if foe_devices:
            signals.append(f"IFF identified hostile devices: {len(foe_devices)}")
        if ddos_hit:
            signals.append("Packet flow contains DDoS-like indicators")
        elif attack_hit:
            signals.append("Packet flow contains threat indicators")
        if simulation_active and (simulation_hit or ddos_hit or attack_hit):
            signals.append("IFF recognized active simulation traffic as friendly training activity")
        if max_fanout >= 20:
            signals.append(f"High outbound fanout from process '{high_fanout_process}' ({max_fanout} sockets)")
        if "web" in vectors:
            signals.append("Web access path active")
        if "email" in vectors:
            signals.append("Email access path active")
        if "usb" in vectors:
            signals.append("USB path activity detected")

        severity = "low"
        if foe_devices:
            severity = "high"
        elif ddos_hit and unknown_devices:
            severity = "high"
        elif ddos_hit or max_fanout >= 20 or any(str(item.get("list_status", "")).lower() == "blacklist" for item in connected_devices):
            severity = "high"
        elif attack_hit or unknown_devices:
            severity = "medium"

        # IFF override: if the simulation subroutine is active and no hostile (foe) devices
        # are present, treat synthetic threat signatures as friendly activity.
        if simulation_active and not foe_devices and (simulation_hit or ddos_hit or attack_hit):
            severity = "low"

        response = "monitor"
        if severity == "high":
            response = "throttle-and-isolate"
        elif severity == "medium":
            response = "inspect-and-rate-limit"
        elif simulation_active:
            response = "monitor-simulation"

        return {
            "observed_at": datetime.utcnow().isoformat(),
            "interval_ms": 1000,
            "active_interface": active_interface,
            "devices": {
                "total": len(connected_devices),
                "unknown_total": len(unknown_devices),
                "items": connected_devices,
            },
            "apps": apps,
            "connections": connections,
            "access_paths": access_paths,
            "vectors": vectors,
            "threat": {
                "severity": severity,
                "signals": signals,
                "suspected_vectors": vectors,
                "recommended_response": response,
            },
            "iff": {
                "simulation_active": simulation_active,
                "friend_total": len(friend_devices),
                "foe_total": len(foe_devices),
                "unknown_total": len(unknown_devices),
            },
        }

    def get_control_surface_realtime_payload(force: bool = False) -> Dict[str, Any]:
        nonlocal control_surface_cache_timestamp, control_surface_cache_payload
        now = time.time()
        with control_surface_cache_lock:
            if not force and control_surface_cache_payload and (now - control_surface_cache_timestamp) < 0.8:
                return control_surface_cache_payload

        settings = load_ui_settings()
        active_interface = str(settings.get("last_interface", "eth0") or "eth0")
        connected_devices = get_connected_devices(active_interface, limit=20)
        payload = summarize_control_surface_state(active_interface, connected_devices)
        with control_surface_cache_lock:
            control_surface_cache_payload = payload
            control_surface_cache_timestamp = now
        return payload

    def _extract_ip_signals_from_packet_rows(limit: int = 320, simulation_active: bool = False) -> Dict[str, Dict[str, Any]]:
        rows = load_packet_flow_preview(limit=max(40, limit))
        signal_by_ip: Dict[str, Dict[str, Any]] = {}

        def ensure(ip_value: str) -> Dict[str, Any]:
            return signal_by_ip.setdefault(ip_value, {"score": 0, "signals": set(), "packets": 0})

        for row in rows:
            source_ip = _normalize_ip(row.get("source"))
            destination_ip = _normalize_ip(row.get("destination"))
            model_flags = str(row.get("model_flags", "")).lower()
            info_text = str(row.get("info", "")).lower()
            combined = f"{model_flags} {info_text}"

            row_score = 0
            row_signals: set[str] = set()
            has_simulation_hint = any(token in combined for token in SIMULATION_HINTS)

            if any(token in combined for token in ("ddos", "malicious", "attack", "blacklist", "threat", "intruder")):
                row_score += 4
                row_signals.add("threat")
            if "anomaly" in combined:
                row_score += 2
                row_signals.add("anomaly")
            if "greylist" in combined or "graylist" in combined:
                row_score += 1
                row_signals.add("greylist")
            if "whitelist" in combined or "benign" in combined:
                row_score -= 1
                row_signals.add("benign")

            if simulation_active and has_simulation_hint:
                row_signals.add("simulation-friendly")
                row_score = min(row_score, 0)
                row_signals.discard("threat")

            for ip_value in (source_ip, destination_ip):
                if not ip_value:
                    continue
                bucket = ensure(ip_value)
                bucket["score"] += row_score
                bucket["packets"] += 1
                bucket["signals"].update(row_signals)

        return signal_by_ip

    def _run_deep_identification_probe() -> Dict[str, Any]:
        model_test_file = PROJECT_ROOT / "Model_Tester" / "Code" / "test_unified_model.py"
        if not model_test_file.exists():
            return {
                "enabled": True,
                "ok": False,
                "reason": "model-test-script-missing",
                "risk_bias": 0,
                "log_tail": [],
            }

        python_exec = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))
        command = [python_exec, str(model_test_file)]
        try:
            process = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=180,
            )
            merged_output = f"{process.stdout}\n{process.stderr}".strip()
            lines = [line for line in merged_output.splitlines() if line.strip()]
            lowered = merged_output.lower()

            risk_bias = 0
            accuracy_match = re.search(r"accuracy\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", lowered)
            if accuracy_match:
                try:
                    accuracy = float(accuracy_match.group(1))
                    if accuracy < 0.75:
                        risk_bias = 1
                    elif accuracy > 0.90:
                        risk_bias = -1
                except ValueError:
                    risk_bias = 0

            # If model testing fails due environment/model-shape mismatch,
            # keep classification neutral instead of forcing higher risk tags.
            if process.returncode != 0:
                risk_bias = 0

            return {
                "enabled": True,
                "ok": process.returncode == 0,
                "return_code": process.returncode,
                "risk_bias": risk_bias,
                "log_tail": lines[-8:],
            }
        except subprocess.TimeoutExpired:
            return {
                "enabled": True,
                "ok": False,
                "reason": "timeout",
                "risk_bias": 0,
                "log_tail": ["deep identify model test timed out after 180s"],
            }
        except Exception as exc:
            return {
                "enabled": True,
                "ok": False,
                "reason": "runtime-error",
                "risk_bias": 0,
                "log_tail": [f"deep identify error: {exc}"],
            }

    def run_identification_auto_classification(deep_test: bool = False) -> Dict[str, Any]:
        realtime_payload = get_control_surface_realtime_payload(force=True)
        existing_entries = _load_identification_entries()
        simulation_active = _is_simulation_subroutine_active()
        packet_signals = _extract_ip_signals_from_packet_rows(limit=360, simulation_active=simulation_active)
        threat_severity = str(realtime_payload.get("threat", {}).get("severity", "low")).lower()
        severity_bonus = 2 if threat_severity == "high" else 1 if threat_severity == "medium" else 0
        deep_result = {
            "enabled": False,
            "ok": True,
            "risk_bias": 0,
            "log_tail": [],
        }
        if deep_test:
            deep_result = _run_deep_identification_probe()

        devices = list(realtime_payload.get("devices", {}).get("items", []))
        normalized_runtime: Dict[str, str] = {}
        for device in devices:
            ip_value = _normalize_ip(device.get("ip"))
            if not ip_value:
                continue
            tag = _normalize_identification_tag(device.get("list_status")) or "unidentified"
            normalized_runtime[ip_value] = tag
            if ip_value not in existing_entries:
                existing_entries[ip_value] = {
                    "ip": ip_value,
                    "tag": tag,
                    "source": "runtime",
                    "updated_at": datetime.utcnow().isoformat(),
                    "notes": "",
                }

        moved: List[Dict[str, str]] = []
        now_iso = datetime.utcnow().isoformat()
        for ip_value, current_tag in normalized_runtime.items():
            if current_tag not in {"unknown", "unidentified"} and _normalize_identification_tag(current_tag):
                continue

            evidence = packet_signals.get(ip_value, {"score": 0, "signals": set(), "packets": 0})
            score = int(evidence.get("score", 0)) + severity_bonus + int(deep_result.get("risk_bias", 0))
            signal_set = set(evidence.get("signals", set()))

            if "threat" in signal_set or score >= 4:
                next_tag = "intruder"
                rationale = "model-threat"
            elif score >= 2 or "anomaly" in signal_set:
                next_tag = "greylist"
                rationale = "model-anomaly"
            else:
                next_tag = "whitelist"
                rationale = "model-benign"

            previous_tag = _normalize_identification_tag(existing_entries.get(ip_value, {}).get("tag")) or "unidentified"
            existing_entries[ip_value] = {
                "ip": ip_value,
                "tag": next_tag,
                "source": "identify",
                "updated_at": now_iso,
                "notes": rationale,
            }
            moved.append({"ip": ip_value, "from": previous_tag, "to": next_tag, "reason": rationale})

        _write_identification_entries(existing_entries)
        listing = _build_identification_listing(include_runtime=True)
        return {
            "moved": moved,
            "threat_severity": threat_severity,
            "counts": listing.get("counts", {}),
            "items": listing.get("items", []),
            "deep_test": deep_result,
        }

    def count_files(path: Path, pattern: str) -> int:
        if not path.exists() or not path.is_dir():
            return 0
        try:
            return sum(1 for _ in path.glob(pattern))
        except Exception:
            return 0

    def start_scheduler() -> Tuple[bool, str]:
        if get_scheduler_status() == "running":
            return True, "Scheduler already running"

        subprocess.Popen(
            "python3 Auto_Update/task_scheduler.py --daemon >/tmp/secids_scheduler_web.log 2>&1",
            shell=True,
            cwd=PROJECT_ROOT,
            executable="/bin/bash",
        )
        status = get_scheduler_status()
        return (status == "running"), f"Scheduler status: {status}"

    def stop_scheduler() -> Tuple[bool, str]:
        subprocess.run(
            "pkill -f 'Auto_Update/task_scheduler.py'",
            shell=True,
            cwd=PROJECT_ROOT,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )
        status = get_scheduler_status()
        return (status == "stopped"), f"Scheduler status: {status}"

    def apply_audit_filters(events: List[Dict], role: str, status: str, event: str, search: str) -> List[Dict]:
        filtered = events

        if role and role != "all":
            filtered = [item for item in filtered if item.get("role") == role]

        if status and status != "all":
            filtered = [item for item in filtered if item.get("status") == status]

        if event and event != "all":
            filtered = [item for item in filtered if item.get("event") == event]

        if search:
            needle = search.lower()
            filtered = [
                item
                for item in filtered
                if needle in json.dumps(item, ensure_ascii=False).lower()
            ]

        return filtered

    @app.get("/Master-Manual.md")
    def serve_master_manual():
        master_manual_path = PROJECT_ROOT / "Master-Manual.md"
        if not master_manual_path.exists():
            return jsonify({"error": "Master-Manual.md not found"}), 404
        
        try:
            content = master_manual_path.read_text(encoding="utf-8")
            return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
        except Exception as exc:
            return jsonify({"error": f"Failed to read Master-Manual.md: {exc}"}), 500

    @app.get("/manual")
    def manual_page():
        """Render the Master-Manual as a formatted HTML page."""
        return render_template("manual.html")

    @app.post("/api/manual/pdf")
    def generate_manual_pdf():
        """Generate PDF from manual HTML content."""
        try:
            from weasyprint import HTML, CSS
            from flask import request as flask_request, make_response
            
            data = flask_request.get_json() or {}
            html_content = data.get("html", "")
            
            if not html_content:
                return jsonify({"error": "No HTML content provided"}), 400
            
            # Create a complete HTML document for PDF
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>SecIDS-CNN Master Manual</title>
                <style>
                    * {{ box-sizing: border-box; }}
                    @page {{ margin: 1.5cm; size: A4; }}
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        color: #1a1a1a;
                        line-height: 1.8;
                        font-size: 11pt;
                    }}
                    h1 {{ font-size: 24pt; margin-top: 24pt; margin-bottom: 12pt; color: #0066cc; border-bottom: 2pt solid #0066cc; padding-bottom: 8pt; }}
                    h2 {{ font-size: 18pt; margin-top: 18pt; margin-bottom: 10pt; color: #0066cc; border-left: 4pt solid #0066cc; padding-left: 10pt; }}
                    h3 {{ font-size: 14pt; margin-top: 14pt; margin-bottom: 8pt; color: #0066cc; }}
                    h4 {{ font-size: 12pt; margin-top: 12pt; margin-bottom: 6pt; color: #004499; }}
                    h5, h6 {{ font-size: 11pt; margin-top: 10pt; margin-bottom: 6pt; color: #004499; }}
                    p {{ margin: 8pt 0; letter-spacing: 0.2px; }}
                    ul, ol {{ margin: 12pt 0; padding-left: 24pt; line-height: 1.8; }}
                    li {{ margin: 6pt 0; }}
                    code {{ 
                        background: #f5f5f5;
                        color: #d73a49;
                        padding: 2pt 6pt;
                        border-radius: 3pt;
                        font-family: 'Monaco', 'Courier New', monospace;
                        font-size: 10pt;
                    }}
                    pre {{
                        background: #f5f5f5;
                        border: 1pt solid #ddd;
                        border-radius: 6pt;
                        padding: 12pt;
                        overflow-x: auto;
                        margin: 12pt 0;
                        font-size: 9pt;
                        line-height: 1.6;
                    }}
                    pre code {{
                        background: none;
                        color: #d73a49;
                        padding: 0;
                        border-radius: 0;
                    }}
                    blockquote {{
                        border-left: 4pt solid #0066cc;
                        margin: 12pt 0;
                        padding-left: 12pt;
                        color: #666;
                        font-style: italic;
                    }}
                    strong {{ color: #0066cc; font-weight: 700; }}
                    em {{ color: #555; }}
                    a {{ color: #0066cc; text-decoration: underline; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # Generate PDF from HTML
            pdf_bytes = HTML(string=full_html).write_pdf()
            
            response = make_response(pdf_bytes)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = "attachment; filename=SecIDS-CNN-Master-Manual.pdf"
            return response
            
        except ImportError:
            return jsonify({"error": "WeasyPrint not installed"}), 500
        except Exception as exc:
            return jsonify({"error": f"PDF generation failed: {str(exc)}"}), 500

    @app.get("/")
    def index():
        if not resolve_identity().get("authenticated"):
            return redirect(app.config["SECIDS_LOGIN_PATH"])
        return render_template("index.html")

    @app.get(access_path)
    def index_alias():
        if not resolve_identity().get("authenticated"):
            return redirect(app.config["SECIDS_LOGIN_PATH"])
        return render_template("index.html")

    @app.get("/server")
    def server_db_page():
        identity = resolve_identity()
        if not identity.get("authenticated"):
            return redirect(app.config["SECIDS_LOGIN_PATH"])
        denied = enforce_role("admin")
        if denied:
            return denied
        return render_template(
            "server.html",
            index_path=app.config["SECIDS_ACCESS_PATH"],
            server_path=f"{app.config['SECIDS_ACCESS_PATH']}/server",
        )

    @app.get(f"{access_path}/server")
    def server_db_page_alias():
        identity = resolve_identity()
        if not identity.get("authenticated"):
            return redirect(app.config["SECIDS_LOGIN_PATH"])
        denied = enforce_role("admin")
        if denied:
            return denied
        return render_template(
            "server.html",
            index_path=app.config["SECIDS_ACCESS_PATH"],
            server_path=f"{app.config['SECIDS_ACCESS_PATH']}/server",
        )

    @app.get("/login")
    def login_page():
        if resolve_identity().get("authenticated"):
            return redirect(app.config["SECIDS_ACCESS_PATH"])
        return render_template(
            "login.html",
            username=SINGLE_ADMIN_USERNAME,
            single_admin_mode=SINGLE_ADMIN_MODE,
            index_path=app.config["SECIDS_ACCESS_PATH"],
        )

    @app.get(login_path)
    def login_page_alias():
        if resolve_identity().get("authenticated"):
            return redirect(app.config["SECIDS_ACCESS_PATH"])
        return render_template(
            "login.html",
            username=SINGLE_ADMIN_USERNAME,
            single_admin_mode=SINGLE_ADMIN_MODE,
            index_path=app.config["SECIDS_ACCESS_PATH"],
        )

    @app.get("/api/auth/session")
    def api_auth_session():
        identity = resolve_identity()
        identity["access_path"] = app.config["SECIDS_ACCESS_PATH"]
        identity["login_path"] = app.config["SECIDS_LOGIN_PATH"]
        identity["session_timeout_seconds"] = int(app.config.get("SECIDS_SESSION_TIMEOUT_SECONDS", SESSION_TIMEOUT_SECONDS))
        return jsonify(identity)

    @app.post("/api/auth/login")
    def api_auth_login():
        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if SINGLE_ADMIN_MODE and username != SINGLE_ADMIN_USERNAME:
            record_audit("login", "failed", {"username": username, "reason": "unknown_user_single_admin_mode"})
            return jsonify({"error": "Invalid username or password"}), 401

        now_ts = time.time()
        lockout_ts = lockout_until.get(username, 0)
        if lockout_ts > now_ts:
            remaining = int(lockout_ts - now_ts)
            record_audit("login", "locked", {"username": username, "remaining_seconds": remaining})
            return jsonify({"error": "Account temporarily locked", "remaining_seconds": remaining}), 429

        with users_lock:
            user_record = users_db.get(username)

        if not user_record or not verify_password_record(password, user_record):
            failed_login_attempts[username] = failed_login_attempts.get(username, 0) + 1
            attempts = failed_login_attempts[username]
            if attempts >= MAX_LOGIN_ATTEMPTS:
                lockout_until[username] = now_ts + LOCKOUT_SECONDS
                failed_login_attempts[username] = 0
                record_audit("login", "locked", {"username": username, "lockout_seconds": LOCKOUT_SECONDS})
                return jsonify({"error": "Too many failed attempts. Account locked.", "remaining_seconds": LOCKOUT_SECONDS}), 429

            record_audit("login", "failed", {"username": username})
            return jsonify({"error": "Invalid username or password", "attempts_remaining": MAX_LOGIN_ATTEMPTS - attempts}), 401

        if not bool(user_record.get("active", True)):
            record_audit("login", "denied", {"username": username, "reason": "inactive"})
            return jsonify({"error": "Account is disabled"}), 403

        failed_login_attempts.pop(username, None)
        lockout_until.pop(username, None)

        role = str(user_record.get("role", "viewer"))
        rotation_due = is_rotation_due(user_record)
        must_change_password = bool(user_record.get("must_change_password", False)) or ("password" in user_record) or rotation_due
        session["username"] = username
        session["role"] = role
        session["must_change_password"] = must_change_password
        session["password_rotation_due"] = rotation_due
        session["last_seen_at"] = time.time()
        if role == "guest":
            register_guest_presence(username)
        set_cached_sudo_password(password)
        record_audit("login", "ok", {"username": username, "role": role})
        return jsonify(
            {
                "ok": True,
                "username": username,
                "role": role,
                "active": bool(user_record.get("active", True)),
                "must_change_password": must_change_password,
                "password_rotation_due": rotation_due,
                "sudo_cached": True,
            }
        )

    @app.post("/api/auth/logout")
    def api_auth_logout():
        identity = resolve_identity()
        clear_auth_session()
        record_audit("logout", "ok", {"username": identity.get("username")})
        return jsonify({"ok": True})

    @app.post("/api/auth/sudo-password")
    def api_auth_set_sudo_password():
        identity = resolve_identity()
        if not identity.get("authenticated"):
            return jsonify({"error": "Login required"}), 401

        payload = request.get_json(silent=True) or {}
        sudo_password = str(payload.get("sudo_password", ""))
        remember = bool(payload.get("remember", True))

        if not sudo_password:
            return jsonify({"error": "sudo_password is required"}), 400

        if remember:
            set_cached_sudo_password(sudo_password)
        else:
            cache_id = str(session.get("sudo_cache_id", "")).strip()
            if cache_id:
                with sudo_cache_lock:
                    session_sudo_cache.pop(cache_id, None)

        record_audit("sudo_password_update", "ok", {"username": identity.get("username")})
        return jsonify({"ok": True, "cached": remember})

    @app.post("/api/auth/change-password")
    def api_auth_change_password():
        if SINGLE_ADMIN_MODE:
            return jsonify({"error": "Password change is disabled in single-admin mode"}), 403

        identity = resolve_identity()
        if not identity.get("authenticated"):
            return jsonify({"error": "Login required"}), 401

        payload = request.get_json(silent=True) or {}
        current_password = str(payload.get("current_password", ""))
        new_password = str(payload.get("new_password", ""))

        if len(new_password) < PASSWORD_MIN_LENGTH:
            return jsonify({"error": f"New password must be at least {PASSWORD_MIN_LENGTH} characters"}), 400

        username = identity["username"]
        with users_lock:
            user_record = users_db.get(username)
        if not user_record:
            return jsonify({"error": "User not found"}), 404

        if not verify_password_record(current_password, user_record):
            record_audit("change_password", "failed", {"username": username, "reason": "invalid_current_password"})
            return jsonify({"error": "Current password is incorrect"}), 401

        secure_fields = hash_password(new_password)
        user_record.pop("password", None)
        user_record.update(secure_fields)
        user_record["must_change_password"] = False
        user_record["password_changed_at"] = datetime.utcnow().isoformat()
        with users_lock:
            users_db[username] = normalize_user_record(user_record)
            save_webui_users(users_db)

        session["must_change_password"] = False
        session["password_rotation_due"] = False
        record_audit("change_password", "ok", {"username": username})
        return jsonify({"ok": True})

    @app.get("/api/auth/users")
    def api_auth_users_list():
        denied = enforce_role("admin")
        if denied:
            return denied

        with users_lock:
            items = [get_public_user_record(username, record) for username, record in users_db.items()]
        if SINGLE_ADMIN_MODE:
            items = [item for item in items if item.get("username") == SINGLE_ADMIN_USERNAME]
        items.sort(key=lambda item: item["username"])
        append_server_snapshot("users", "PANEL_USERS_SNAPSHOT", {"count": len(items), "users": items})
        return jsonify({"users": items, "password_max_age_days": PASSWORD_MAX_AGE_DAYS})

    @app.post("/api/auth/users")
    def api_auth_users_create():
        denied = enforce_role("admin")
        if denied:
            return denied
        if SINGLE_ADMIN_MODE:
            return jsonify({"error": "User creation disabled in single-admin mode"}), 403

        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip()
        role = str(payload.get("role", "viewer")).strip()
        password = str(payload.get("password", ""))

        if not is_valid_username(username):
            return jsonify({"error": "Username must be 3-32 chars: letters, numbers, ., _, -"}), 400
        if role not in ROLE_ORDER:
            return jsonify({"error": "Invalid role"}), 400

        generated = False
        if not password:
            password = secrets.token_urlsafe(12)
            generated = True

        if len(password) < PASSWORD_MIN_LENGTH:
            return jsonify({"error": f"Password must be at least {PASSWORD_MIN_LENGTH} characters"}), 400

        with users_lock:
            if username in users_db:
                return jsonify({"error": "User already exists"}), 409

            users_db[username] = normalize_user_record(
                {
                    "role": role,
                    **hash_password(password),
                    "must_change_password": True,
                    "password_changed_at": datetime.utcnow().isoformat(),
                }
            )
            save_webui_users(users_db)

        record_audit("user_create", "ok", {"username": username, "role": role, "generated": generated})
        return jsonify(
            {
                "ok": True,
                "user": get_public_user_record(username, users_db[username]),
                "temporary_password": password,
                "generated": generated,
            }
        )

    @app.put("/api/auth/users/<username>/role")
    def api_auth_users_update_role(username: str):
        denied = enforce_role("admin")
        if denied:
            return denied
        if SINGLE_ADMIN_MODE:
            return jsonify({"error": "Role changes disabled in single-admin mode"}), 403

        payload = request.get_json(silent=True) or {}
        new_role = str(payload.get("role", "")).strip()
        if new_role not in ROLE_ORDER:
            return jsonify({"error": "Invalid role"}), 400

        username = username.strip()
        current_identity = resolve_identity()

        with users_lock:
            record = users_db.get(username)
            if not record:
                return jsonify({"error": "User not found"}), 404

            old_role = str(record.get("role", "viewer"))
            if old_role == "admin" and new_role != "admin":
                admin_count = sum(1 for item in users_db.values() if str(item.get("role", "viewer")) == "admin")
                if admin_count <= 1:
                    return jsonify({"error": "Cannot demote the last admin"}), 400

            record["role"] = new_role
            users_db[username] = normalize_user_record(record)
            save_webui_users(users_db)

        if current_identity.get("username") == username:
            session["role"] = new_role

        record_audit("user_role_update", "ok", {"username": username, "from": old_role, "to": new_role})
        return jsonify({"ok": True, "user": get_public_user_record(username, users_db[username])})

    @app.post("/api/auth/users/<username>/reset-password")
    def api_auth_users_reset_password(username: str):
        denied = enforce_role("admin")
        if denied:
            return denied
        if SINGLE_ADMIN_MODE:
            return jsonify({"error": "Password reset disabled in single-admin mode"}), 403

        payload = request.get_json(silent=True) or {}
        provided_password = str(payload.get("password", ""))
        generated = False

        if not provided_password:
            provided_password = secrets.token_urlsafe(12)
            generated = True

        if len(provided_password) < PASSWORD_MIN_LENGTH:
            return jsonify({"error": f"Password must be at least {PASSWORD_MIN_LENGTH} characters"}), 400

        username = username.strip()
        with users_lock:
            record = users_db.get(username)
            if not record:
                return jsonify({"error": "User not found"}), 404

            record.pop("password", None)
            record.update(hash_password(provided_password))
            record["must_change_password"] = True
            record["password_changed_at"] = datetime.utcnow().isoformat()
            users_db[username] = normalize_user_record(record)
            save_webui_users(users_db)

        failed_login_attempts.pop(username, None)
        lockout_until.pop(username, None)

        if session.get("username") == username:
            session["must_change_password"] = True
            session["password_rotation_due"] = False

        record_audit("user_password_reset", "ok", {"username": username, "generated": generated})
        return jsonify(
            {
                "ok": True,
                "user": get_public_user_record(username, users_db[username]),
                "temporary_password": provided_password,
                "generated": generated,
            }
        )

    @app.put("/api/auth/users/<username>/active")
    def api_auth_users_set_active(username: str):
        denied = enforce_role("admin")
        if denied:
            return denied
        if SINGLE_ADMIN_MODE:
            return jsonify({"error": "Account toggles disabled in single-admin mode"}), 403

        payload = request.get_json(silent=True) or {}
        if "active" not in payload:
            return jsonify({"error": "Missing active field"}), 400

        active = bool(payload.get("active"))
        username = username.strip()
        current_identity = resolve_identity()

        with users_lock:
            record = users_db.get(username)
            if not record:
                return jsonify({"error": "User not found"}), 404

            role = str(record.get("role", "viewer"))
            if role == "admin" and not active:
                if count_active_admins(exclude_username=username) <= 0:
                    return jsonify({"error": "Cannot disable the last active admin"}), 400

            record["active"] = active
            users_db[username] = normalize_user_record(record)
            save_webui_users(users_db)

        if current_identity.get("username") == username and not active:
            clear_auth_session()

        failed_login_attempts.pop(username, None)
        lockout_until.pop(username, None)
        record_audit("user_active_update", "ok", {"username": username, "active": active})
        return jsonify({"ok": True, "user": get_public_user_record(username, users_db[username])})

    @app.delete("/api/auth/users/<username>")
    def api_auth_users_delete(username: str):
        denied = enforce_role("admin")
        if denied:
            return denied
        if SINGLE_ADMIN_MODE:
            return jsonify({"error": "User deletion disabled in single-admin mode"}), 403

        username = username.strip()
        current_identity = resolve_identity()
        if current_identity.get("username") == username:
            return jsonify({"error": "Cannot delete currently logged-in user"}), 400

        with users_lock:
            record = users_db.get(username)
            if not record:
                return jsonify({"error": "User not found"}), 404

            if str(record.get("role", "viewer")) == "admin":
                if count_active_admins(exclude_username=username) <= 0:
                    return jsonify({"error": "Cannot delete the last admin"}), 400

            users_db.pop(username, None)
            save_webui_users(users_db)

        failed_login_attempts.pop(username, None)
        lockout_until.pop(username, None)
        record_audit("user_delete", "ok", {"username": username})
        return jsonify({"ok": True})

    @app.get("/api/menu")
    def api_menu():
        identity = resolve_identity()
        role = str(identity.get("role", "viewer"))

        if role != "guest":
            return jsonify({"menu": menu_model})

        # Keep guests out of future Admin/Server menu sections by id/title.
        filtered_menu: List[Dict[str, Any]] = []
        for section in menu_model:
            section_id = str(section.get("id", "")).strip().lower()
            section_title = str(section.get("title", "")).strip().lower()
            if "admin" in section_id or "server" in section_id or "admin" in section_title or "server" in section_title:
                continue
            filtered_menu.append(section)

        return jsonify({"menu": filtered_menu})

    @app.get("/api/system")
    def api_system():
        ensure_passive_packet_capture(load_ui_settings())
        with jobs_lock:
            pending_count = len(queue)
            running_count = running_jobs_count()
            paused = queue_paused

        identity = resolve_identity()
        return jsonify(
            {
                "project_root": str(PROJECT_ROOT),
                "scheduler": get_scheduler_status(),
                "queue": {
                    "paused": paused,
                    "pending": pending_count,
                    "running": running_count,
                    "max_concurrent": max_concurrent_jobs,
                },
                "auth_required": bool(API_TOKEN) or True,
                "current_role": identity["role"],
                "current_user": identity["username"],
                "authenticated": identity["authenticated"],
                "access_path": app.config["SECIDS_ACCESS_PATH"],
                "login_path": app.config["SECIDS_LOGIN_PATH"],
                "session_timeout_seconds": int(app.config.get("SECIDS_SESSION_TIMEOUT_SECONDS", SESSION_TIMEOUT_SECONDS)),
                "server_db": {
                    "root": str(SERVER_DB_ROOT.relative_to(PROJECT_ROOT)),
                    "available": True,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "packet_capture": get_packet_capture_status(),
            }
        )

    @app.get("/api/roles")
    def api_roles():
        identity = resolve_identity()
        return jsonify(
            {
                "current_role": identity["role"],
                "current_user": identity["username"],
                "available_roles": ["guest", "viewer", "operator", "admin"],
            }
        )

    @app.get("/api/server-db/overview")
    def api_server_db_overview():
        denied = enforce_role("admin")
        if denied:
            return denied

        payload = get_server_db_overview()
        payload["index_path"] = app.config["SECIDS_ACCESS_PATH"]
        payload["server_path"] = f"{app.config['SECIDS_ACCESS_PATH']}/server"
        return jsonify(payload)

    @app.post("/api/server-db/add")
    def api_server_db_add_folder():
        denied = enforce_role("admin")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        folder_name = sanitize_server_folder_name(payload.get("folder", ""))
        if not folder_name:
            return jsonify({"error": "Folder name is required"}), 400

        target = server_db_custom_root / folder_name
        target.mkdir(parents=True, exist_ok=True)
        record_audit("server_db_add", "ok", {"folder": folder_name})
        return jsonify({"ok": True, "folder": folder_name, "overview": get_server_db_overview()})

    @app.post("/api/server-db/remove")
    def api_server_db_remove_folder():
        denied = enforce_role("admin")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        folder_name = sanitize_server_folder_name(payload.get("folder", ""))
        if not folder_name:
            return jsonify({"error": "Folder name is required"}), 400

        target = server_db_custom_root / folder_name
        if not target.exists() or not target.is_dir():
            return jsonify({"error": "Custom folder not found"}), 404

        shutil.rmtree(target)
        record_audit("server_db_remove", "ok", {"folder": folder_name})
        return jsonify({"ok": True, "folder": folder_name, "overview": get_server_db_overview()})

    @app.post("/api/server-db/import")
    def api_server_db_import():
        denied = enforce_role("admin")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        folder_name = sanitize_server_folder_name(payload.get("folder", ""))
        data = payload.get("data")
        flag = str(payload.get("flag", "SERVER_IMPORT")).strip() or "SERVER_IMPORT"

        if not folder_name:
            return jsonify({"error": "Folder is required"}), 400
        if data is None or data == "":
            return jsonify({"error": "Import data is required"}), 400

        target_folder = server_db_custom_root / folder_name
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / f"import_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"

        record = {
            "stored_at": datetime.utcnow().isoformat(),
            "flag": flag,
            "folder": folder_name,
            "payload": data,
        }
        with open(target_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        record_audit("server_db_import", "ok", {"folder": folder_name, "file": target_file.name})
        return jsonify({"ok": True, "folder": folder_name, "file": target_file.name, "overview": get_server_db_overview()})

    @app.post("/api/server-db/export")
    def api_server_db_export():
        denied = enforce_role("admin")
        if denied:
            return denied

        ensure_server_db_structure()
        export_base = PROJECT_ROOT / "Reports" / f"server_db_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        archive_path = shutil.make_archive(str(export_base), "gztar", root_dir=str(SERVER_DB_ROOT))
        relative_path = str(Path(archive_path).relative_to(PROJECT_ROOT))
        record_audit("server_db_export", "ok", {"path": relative_path})
        return jsonify({"ok": True, "path": relative_path})

    @app.get("/api/server-db/file")
    def api_server_db_file():
        denied = enforce_role("admin")
        if denied:
            return denied

        folder = str(request.args.get("folder", "")).strip()
        name = str(request.args.get("name", "")).strip()
        max_lines = max(20, min(request.args.get("lines", default=300, type=int), 1200))

        file_path = resolve_server_db_file(folder, name)
        if file_path is None:
            return jsonify({"error": "File not found"}), 404

        with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()

        tail = "".join(lines[-max_lines:])
        relative = str(file_path.relative_to(PROJECT_ROOT))
        return jsonify(
            {
                "ok": True,
                "folder": folder,
                "name": name,
                "path": relative,
                "line_count": len(lines),
                "content": tail,
            }
        )

    @app.get("/api/server-db/distribute")
    def api_server_db_distribute():
        denied = enforce_role("admin")
        if denied:
            return denied

        requested = str(request.args.get("keys", "")).strip()
        keys = [key.strip() for key in requested.split(",") if key.strip()] if requested else list(server_db_folders.keys())
        max_files = max(1, min(request.args.get("files", default=5, type=int), 25))
        bundle: Dict[str, Any] = {}

        for key in keys:
            folder_path = server_db_folders.get(key)
            if folder_path is None:
                continue

            files = sorted([item for item in folder_path.iterdir() if item.is_file()], key=lambda item: item.name)
            recent = [item.name for item in files[-max_files:]]
            latest_payload = latest_snapshot_payload(key)
            bundle[key] = {
                "folder": str(folder_path.relative_to(PROJECT_ROOT)),
                "file_count": len(files),
                "recent_files": recent,
                "latest_payload": latest_payload,
            }

        return jsonify(
            {
                "ok": True,
                "distributed_at": datetime.utcnow().isoformat(),
                "index_path": app.config["SECIDS_ACCESS_PATH"],
                "server_path": f"{app.config['SECIDS_ACCESS_PATH']}/server",
                "bundle": bundle,
            }
        )

    @app.post("/api/server-db/sync-project-data")
    def api_server_db_sync_project_data():
        denied = enforce_role("admin")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        execute = bool(payload.get("execute", True))
        summary = sync_project_data_to_server_db(execute=execute)
        record_audit("server_db_sync_project_data", "ok", {"execute": execute, "synced": summary.get("synced", 0)})
        return jsonify({"ok": True, "summary": summary, "overview": get_server_db_overview()})

    @app.post("/api/server-db/nist-csw/update")
    def api_server_db_nist_csw_update():
        denied = enforce_role("admin")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        feeds = payload.get("feeds")
        selected_feeds = [str(item).strip() for item in feeds] if isinstance(feeds, list) else None
        auto_convert = bool(payload.get("auto_convert", True))

        result = run_nist_csw_feed_update(feeds=selected_feeds)
        conversion = None
        if result.get("ok") and auto_convert:
            conversion = run_nist_csw_converter()
        record_audit("nist_csw_update", "ok" if result.get("ok") else "failed", {"feeds": selected_feeds or ["default"]})
        final_ok = bool(result.get("ok")) and (conversion is None or bool(conversion.get("ok")))
        status_code = 200 if final_ok else 500
        return jsonify({"ok": final_ok, "result": result, "conversion": conversion, "overview": get_server_db_overview()}), status_code

    @app.post("/api/server-db/nist-csw/convert")
    def api_server_db_nist_csw_convert():
        denied = enforce_role("admin")
        if denied:
            return denied

        result = run_nist_csw_converter()
        record_audit("nist_csw_convert", "ok" if result.get("ok") else "failed", {"rows": result.get("converted_rows", 0)})
        status_code = 200 if result.get("ok") else 500
        return jsonify({"ok": bool(result.get("ok")), "result": result, "overview": get_server_db_overview()}), status_code

    @app.get("/api/server-db/nist-csw/status")
    def api_server_db_nist_csw_status():
        denied = enforce_role("admin")
        if denied:
            return denied

        latest = get_latest_nist_csw_update_status()
        folder_path = server_db_folders["nist_csw"]
        files = sorted([item.name for item in folder_path.iterdir() if item.is_file()])
        return jsonify(
            {
                "ok": True,
                "folder": str(folder_path.relative_to(PROJECT_ROOT)),
                "file_count": len(files),
                "recent_files": files[-20:],
                "latest": latest,
            }
        )

    @app.get("/api/overview")
    def api_overview():
        interfaces = get_network_interfaces(limit=8)
        settings = load_ui_settings()
        active_interface = str(settings.get("last_interface", "eth0") or "eth0")
        connected_devices = get_connected_devices(active_interface, limit=12)
        return jsonify(
            {
                "interfaces": interfaces,
                "counts": {
                    "captures": count_files(PROJECT_ROOT / "Captures", "*.pcap"),
                    "datasets": count_files(PROJECT_ROOT / "SecIDS-CNN" / "datasets", "*.csv"),
                    "results": count_files(PROJECT_ROOT / "Results", "*.csv"),
                    "models": model_registry.count_models(),
                },
                "scheduler": get_scheduler_status(),
                "selected_live_model_mode": str(settings.get("live_model_mode", "auto")),
                "selected_live_model": str(settings.get("live_model_path", "")),
                "selected_live_backend": str(settings.get("live_backend", "")),
                "selected_countermeasure_mode": str(settings.get("countermeasure_mode", "active")),
                "active_interface": active_interface,
                "connected_devices": connected_devices,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.get("/api/control-surface/realtime")
    def api_control_surface_realtime():
        denied = enforce_role("viewer")
        if denied:
            return denied

        payload = get_control_surface_realtime_payload()
        return jsonify({"ok": True, **payload})

    @app.get("/api/identification-list")
    def api_identification_list():
        denied = enforce_role("viewer")
        if denied:
            return denied

        listing = _build_identification_listing(include_runtime=True)
        return jsonify({"ok": True, **listing})

    @app.post("/api/identification-list/add")
    def api_identification_add():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        ip_value = _normalize_ip(payload.get("ip"))
        if not ip_value:
            return jsonify({"error": "Valid IP is required"}), 400

        tag = _normalize_identification_tag(payload.get("tag"))
        if not tag:
            return jsonify({"error": "Valid tag is required"}), 400

        source = str(payload.get("source", "manual") or "manual")[:40]
        notes = str(payload.get("notes", "") or "")[:200]
        entries = _load_identification_entries()
        entries[ip_value] = {
            "ip": ip_value,
            "tag": tag,
            "source": source,
            "updated_at": datetime.utcnow().isoformat(),
            "notes": notes,
        }
        _write_identification_entries(entries)
        listing = _build_identification_listing(include_runtime=True)
        record_audit("identification_add", "ok", {"ip": ip_value, "tag": tag, "source": source})
        return jsonify({"ok": True, "updated": {"ip": ip_value, "tag": tag}, **listing})

    @app.post("/api/identification-list/remove")
    def api_identification_remove():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        ip_value = _normalize_ip(payload.get("ip"))
        if not ip_value:
            return jsonify({"error": "Valid IP is required"}), 400

        entries = _load_identification_entries()
        removed = entries.pop(ip_value, None) is not None
        _write_identification_entries(entries)
        listing = _build_identification_listing(include_runtime=True)
        record_audit("identification_remove", "ok" if removed else "failed", {"ip": ip_value})
        return jsonify({"ok": True, "removed": removed, "ip": ip_value, **listing})

    @app.post("/api/identification-list/change-tag")
    def api_identification_change_tag():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        ip_value = _normalize_ip(payload.get("ip"))
        if not ip_value:
            return jsonify({"error": "Valid IP is required"}), 400

        new_tag = _normalize_identification_tag(payload.get("tag"))
        if not new_tag:
            return jsonify({"error": "Valid destination tag is required"}), 400

        entries = _load_identification_entries()
        previous = _normalize_identification_tag(entries.get(ip_value, {}).get("tag")) or "unidentified"
        entries[ip_value] = {
            "ip": ip_value,
            "tag": new_tag,
            "source": str(payload.get("source", "manual") or "manual")[:40],
            "updated_at": datetime.utcnow().isoformat(),
            "notes": str(payload.get("notes", "") or "")[:200],
        }
        _write_identification_entries(entries)
        listing = _build_identification_listing(include_runtime=True)
        record_audit("identification_change_tag", "ok", {"ip": ip_value, "from": previous, "to": new_tag})
        return jsonify({"ok": True, "moved": {"ip": ip_value, "from": previous, "to": new_tag}, **listing})

    @app.post("/api/identification-list/identify")
    def api_identification_identify():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        deep_test = bool(payload.get("deep_test", False))
        result = run_identification_auto_classification(deep_test=deep_test)
        moved = result.get("moved", [])
        record_audit("identification_identify", "ok", {"moved": len(moved), "deep_test": deep_test})
        return jsonify({"ok": True, **result})

    @app.get("/api/queue")
    def api_queue_state():
        with jobs_lock:
            return jsonify(
                {
                    "paused": queue_paused,
                    "pending": len(queue),
                    "running": running_jobs_count(),
                    "max_concurrent": max_concurrent_jobs,
                    "items": queue_snapshot(),
                }
            )

    @app.post("/api/queue/pause")
    def api_queue_pause():
        denied = enforce_role("operator")
        if denied:
            return denied

        nonlocal queue_paused
        queue_paused = True
        record_audit("queue_pause", "ok", {})
        return jsonify({"ok": True, "paused": True})

    @app.post("/api/queue/resume")
    def api_queue_resume():
        denied = enforce_role("operator")
        if denied:
            return denied

        nonlocal queue_paused
        queue_paused = False
        record_audit("queue_resume", "ok", {})
        return jsonify({"ok": True, "paused": False})

    @app.post("/api/queue/clear")
    def api_queue_clear():
        denied = enforce_role("operator")
        if denied:
            return denied

        cleared = 0
        with jobs_lock:
            while queue:
                job_id = queue.popleft()
                if job_id in jobs and jobs[job_id]["status"] == "queued":
                    jobs[job_id]["status"] = "cancelled"
                    jobs[job_id]["return_code"] = -15
                    jobs[job_id]["logs"].append("[queue] Removed by queue clear")
                    jobs[job_id]["ended_at"] = datetime.utcnow().isoformat()
                    cleared += 1

        record_audit("queue_clear", "ok", {"cleared": cleared})
        return jsonify({"ok": True, "cleared": cleared})

    @app.post("/api/queue/max_concurrent")
    def api_queue_max_concurrent():
        denied = enforce_role("operator")
        if denied:
            return denied

        nonlocal max_concurrent_jobs
        payload = request.get_json(silent=True) or {}
        value = int(payload.get("value", max_concurrent_jobs))
        max_concurrent_jobs = max(1, min(value, 10))
        record_audit("queue_max_concurrent", "ok", {"value": max_concurrent_jobs})
        return jsonify({"ok": True, "max_concurrent": max_concurrent_jobs})

    @app.post("/api/scheduler/start")
    def api_scheduler_start():
        denied = enforce_role("operator")
        if denied:
            return denied

        ok, message = start_scheduler()
        record_audit("scheduler_start", "ok" if ok else "failed", {"message": message})
        return jsonify({"ok": ok, "message": message, "scheduler": get_scheduler_status()})

    @app.post("/api/scheduler/stop")
    def api_scheduler_stop():
        denied = enforce_role("operator")
        if denied:
            return denied

        ok, message = stop_scheduler()
        record_audit("scheduler_stop", "ok" if ok else "failed", {"message": message})
        return jsonify({"ok": ok, "message": message, "scheduler": get_scheduler_status()})

    @app.get("/api/settings")
    def api_settings():
        settings = load_ui_settings()
        ensure_passive_packet_capture(settings)
        append_server_snapshot("settings", "PANEL_SETTINGS_READ", settings)
        return jsonify({"settings": settings, "packet_capture": get_packet_capture_status()})

    @app.put("/api/settings")
    def api_update_settings():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        params = payload.get("settings", {})
        logs = apply_settings_update(params)
        updated_settings = load_ui_settings()
        append_server_snapshot("settings", "PANEL_SETTINGS_UPDATE", {"settings": updated_settings, "logs": logs})
        record_audit("settings_update", "ok", {"keys": sorted(list(params.keys()))})
        return jsonify({"ok": True, "logs": logs, "settings": updated_settings, "packet_capture": get_packet_capture_status()})

    @app.get("/api/history")
    def api_history():
        limit = request.args.get("limit", default=20, type=int)
        history_rows = load_combined_history(limit=max(1, min(limit, 200)))
        source = "live"
        if not history_rows:
            snapshot = latest_snapshot_payload("history") or {}
            history_rows = snapshot.get("rows", []) if isinstance(snapshot, dict) else []
            source = "serverdb" if history_rows else "live"
        append_server_snapshot("history", "PANEL_HISTORY_SNAPSHOT", {"count": len(history_rows), "rows": history_rows})
        return jsonify({"history": history_rows, "source": source})

    @app.get("/api/packet-logs")
    def api_packet_logs():
        limit = request.args.get("limit", default=120, type=int)
        rows = load_action_log_preview(limit=max(10, min(limit, 300)))
        source = "live"
        if not rows:
            snapshot = latest_snapshot_payload("action_logs") or {}
            rows = snapshot.get("rows", []) if isinstance(snapshot, dict) else []
            source = "serverdb" if rows else "live"
        append_server_snapshot("action_logs", "PANEL_ACTION_LOGS", {"count": len(rows), "rows": rows})
        return jsonify({"rows": rows, "source": source})

    @app.get("/api/packet-flow")
    def api_packet_flow():
        limit = request.args.get("limit", default=120, type=int)
        rows = load_packet_flow_preview(limit=max(10, min(limit, 300)))
        source = "live"
        if not rows:
            snapshot = latest_snapshot_payload("packet_logs") or {}
            rows = snapshot.get("rows", []) if isinstance(snapshot, dict) else []
            source = "serverdb" if rows else "live"
        append_server_snapshot("packet_logs", "PANEL_PACKET_FLOW", {"count": len(rows), "rows": rows})
        return jsonify({"rows": rows, "source": source})

    @app.get("/api/packet-capture/status")
    def api_packet_capture_status():
        ensure_passive_packet_capture(load_ui_settings())
        return jsonify({"ok": True, "capture": get_packet_capture_status()})

    @app.post("/api/packet-capture/start")
    def api_packet_capture_start():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        settings = load_ui_settings()
        iface = str(payload.get("interface") or settings.get("last_interface") or "eth0").strip() or "eth0"
        auto = bool(payload.get("auto", False))
        ok, message = start_packet_capture(iface, auto=auto)
        record_audit("packet_capture_start", "ok" if ok else "failed", {"interface": iface, "message": message, "auto": auto})
        status_code = 200 if ok else 400
        return jsonify({"ok": ok, "message": message, "capture": get_packet_capture_status()}), status_code

    @app.post("/api/packet-capture/pause")
    def api_packet_capture_pause():
        denied = enforce_role("operator")
        if denied:
            return denied

        ok, message = pause_packet_capture()
        record_audit("packet_capture_pause", "ok" if ok else "failed", {"message": message})
        status_code = 200 if ok else 400
        return jsonify({"ok": ok, "message": message, "capture": get_packet_capture_status()}), status_code

    @app.post("/api/packet-capture/stop")
    def api_packet_capture_stop():
        denied = enforce_role("operator")
        if denied:
            return denied

        ok, message = stop_packet_capture("stopped")
        record_audit("packet_capture_stop", "ok" if ok else "failed", {"message": message})
        status_code = 200 if ok else 400
        return jsonify({"ok": ok, "message": message, "capture": get_packet_capture_status()}), status_code

    @app.post("/api/history/rerun")
    def api_history_rerun():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        command = str(payload.get("command", "")).strip()
        mode = str(payload.get("mode", "realtime"))
        timeout_seconds = int(payload.get("timeout_seconds", DEFAULT_JOB_TIMEOUT_SECONDS))

        if not command:
            entries = load_combined_history(limit=1)
            if not entries or not entries[0].get("command"):
                return jsonify({"error": "No history command available to rerun"}), 400
            command = entries[0]["command"]

        job_id, status = queue_command_job("history-rerun", "History Rerun", mode, command, timeout_seconds)
        record_audit("history_rerun", "ok", {"job_id": job_id, "mode": mode})
        return jsonify({"job_id": job_id, "status": status})

    @app.get("/api/audit")
    def api_audit():
        limit = request.args.get("limit", default=50, type=int)
        role = request.args.get("role", default="all", type=str)
        status = request.args.get("status", default="all", type=str)
        event = request.args.get("event", default="all", type=str)
        search = request.args.get("search", default="", type=str).strip()

        events = list(audit_events)
        filtered = apply_audit_filters(events, role=role, status=status, event=event, search=search)
        filtered = filtered[: max(1, min(limit, 500))]
        append_server_snapshot("audit", "PANEL_AUDIT_SNAPSHOT", {"count": len(filtered), "events": filtered})
        return jsonify({"events": filtered})

    @app.post("/api/audit/export")
    def api_audit_export():
        denied = enforce_role("operator")
        if denied:
            return denied

        export_payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "events": list(audit_events),
        }
        export_path = PROJECT_ROOT / "Reports" / f"webui_audit_export_{int(time.time())}.json"
        write_json_file(export_path, export_payload)
        record_audit("audit_export", "ok", {"path": str(export_path.relative_to(PROJECT_ROOT))})
        return jsonify({"ok": True, "path": str(export_path.relative_to(PROJECT_ROOT))})

    @app.get("/api/models/db-status")
    def api_models_db_status():
        denied = enforce_role("operator")
        if denied:
            return denied

        return jsonify(
            {
                "ok": True,
                "db_path": str(MODEL_REGISTRY_DB_FILE.relative_to(PROJECT_ROOT)),
                "total_models": model_registry.count_models(),
                "access_path": app.config["SECIDS_ACCESS_PATH"],
                "login_path": app.config["SECIDS_LOGIN_PATH"],
            }
        )

    @app.get("/api/models")
    def api_models_list():
        denied = enforce_role("operator")
        if denied:
            return denied

        limit = request.args.get("limit", default=100, type=int)
        models = model_registry.list_models(limit=limit)
        total = model_registry.count_models()
        source = "live"
        if not models:
            snapshot = latest_snapshot_payload("models") or {}
            models = snapshot.get("models", []) if isinstance(snapshot, dict) else []
            total = int(snapshot.get("total_models", len(models))) if isinstance(snapshot, dict) else len(models)
            source = "serverdb" if models else "live"
        append_server_snapshot("models", "PANEL_MODELS_SNAPSHOT", {"count": len(models), "total_models": total, "models": models})
        return jsonify({"models": models, "total_models": total, "source": source})

    @app.get("/api/models/<int:model_id>")
    def api_models_get(model_id: int):
        denied = enforce_role("operator")
        if denied:
            return denied

        item = model_registry.get_model(model_id)
        if not item:
            return jsonify({"error": "Model not found"}), 404
        return jsonify({"model": item})

    @app.post("/api/models/register")
    def api_models_register():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        rel_path = str(payload.get("path", "")).strip()
        if not rel_path:
            return jsonify({"error": "Model path is required"}), 400

        source = str(payload.get("source", "manual")).strip() or "manual"
        notes = str(payload.get("notes", "")).strip()
        file_path = (PROJECT_ROOT / rel_path).resolve()

        try:
            record = model_registry.register_model(file_path, source=source, notes=notes, test_artifact=True)
        except FileNotFoundError as exc:
            return jsonify({"error": str(exc)}), 404
        except Exception as exc:
            return jsonify({"error": f"Failed to register model: {exc}"}), 500

        record_audit("model_register", "ok", {"path": rel_path, "source": source})
        return jsonify({"ok": True, "model": record})

    @app.post("/api/models/sync")
    def api_models_sync():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        source = str(payload.get("source", "manual-sync")).strip() or "manual-sync"
        sync_result = model_registry.sync_from_directories(model_registry_dirs, source=source)
        record_audit("model_sync", "ok", {"source": source, "updated": sync_result.get("updated", 0)})
        return jsonify({"ok": True, **sync_result})

    @app.post("/api/run")
    def api_run():
        payload = request.get_json(silent=True) or {}
        action_id = payload.get("action_id", "")
        params = payload.get("params", {})
        mode = payload.get("mode", "realtime")
        timeout_seconds = int(payload.get("timeout_seconds", DEFAULT_JOB_TIMEOUT_SECONDS))

        if action_id not in action_index:
            return jsonify({"error": f"Unknown action: {action_id}"}), 400

        action = action_index[action_id]
        executor = action["executor"]
        current_role = resolve_request_role()

        if executor["kind"] == "internal":
            denied = enforce_role("operator")
            if denied:
                return denied

            ok, logs, command = run_internal_action(executor["value"], params)
            job_id = create_job(action_id, action["title"], mode, command, timeout_seconds)

            if command and mode == "realtime":
                with jobs_lock:
                    jobs[job_id]["logs"].extend(logs)
                    queue.append(job_id)
                record_audit("job_queue", "ok", {"job_id": job_id, "action_id": action_id, "role": current_role})
                return jsonify({"job_id": job_id, "status": "queued"})

            status = "completed" if ok else "failed"
            complete_job(job_id, status, 0 if ok else 1, logs)
            record_audit("internal_action", status, {"action_id": action_id, "role": current_role})
            return jsonify({"job_id": job_id, "status": status})

        try:
            command = build_command(action, params)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        required_role = required_role_for_action(action_id, command)
        denied = enforce_role(required_role)
        if denied:
            return denied

        if command.strip().startswith("sudo "):
            cached_password = get_cached_sudo_password()
            if not cached_password:
                sudo_probe = subprocess.run(
                    "sudo -n true",
                    shell=True,
                    cwd=PROJECT_ROOT,
                    executable="/bin/bash",
                    capture_output=True,
                    text=True,
                )
                if sudo_probe.returncode != 0:
                    return (
                        jsonify(
                            {
                                "error": "Sudo password required before running this action.",
                                "code": "SUDO_PASSWORD_REQUIRED",
                                "hint": "Use Execution Logs > Sudo Password Validation panel, then retry.",
                            }
                        ),
                        400,
                    )

        job_id, status = queue_command_job(action_id, action["title"], mode, command, timeout_seconds)
        record_audit(
            "job_queue",
            "ok",
            {"job_id": job_id, "action_id": action_id, "role": current_role, "required_role": required_role},
        )
        return jsonify({"job_id": job_id, "status": status})

    @app.post("/api/simulation/run")
    def api_simulation_run():
        denied = enforce_role("operator")
        if denied:
            return denied

        payload = request.get_json(silent=True) or {}
        timeout_seconds = int(payload.get("timeout_seconds", DEFAULT_JOB_TIMEOUT_SECONDS))

        attacker_profile = str(payload.get("attacker_profile", "mixed")).strip() or "mixed"
        defender_profile = str(payload.get("defender_profile", "adaptive-ai")).strip() or "adaptive-ai"
        architecture_type = str(payload.get("architecture_type", "school")).strip().lower() or "school"
        if architecture_type not in {"school", "library", "restaurant"}:
            architecture_type = "school"
        settings = load_ui_settings()
        countermeasure_mode = str(payload.get("countermeasure_mode", settings.get("countermeasure_mode", "active"))).strip().lower() or "active"
        if countermeasure_mode not in {"active", "passive"}:
            countermeasure_mode = "active"
        intensity = str(payload.get("intensity", "medium")).strip() or "medium"
        attackers = int(payload.get("attackers", 25))
        duration = int(payload.get("duration", 90))
        retrain = bool(payload.get("retrain", True))
        seed = int(payload.get("seed", 42))

        safe_args = [
            "python3",
            "Tools/simulate_ddos_workflow.py",
            "--architecture-type",
            architecture_type,
            "--attacker-profile",
            attacker_profile,
            "--defender-profile",
            defender_profile,
            "--countermeasure-mode",
            countermeasure_mode,
            "--intensity",
            intensity,
            "--attackers",
            str(max(1, attackers)),
            "--duration",
            str(max(10, duration)),
            "--seed",
            str(seed),
        ]
        if retrain:
            safe_args.append("--retrain")

        command = " ".join(shlex.quote(part) for part in safe_args)

        nist_input_sources = [
            "Archives/Attack_Dataset.csv",
            "Device_Profile/Blacklist/attack_patterns/patterns.json",
        ]
        staged_inputs = [stage_nist_csw_file(path, "input") for path in nist_input_sources]
        staged_inputs = [item for item in staged_inputs if item]
        append_server_snapshot(
            "nist_csw",
            "SIMULATION_INPUT",
            {
                "requested_at": datetime.utcnow().isoformat(),
                "attacker_profile": attacker_profile,
                "defender_profile": defender_profile,
                "architecture_type": architecture_type,
                "countermeasure_mode": countermeasure_mode,
                "intensity": intensity,
                "attackers": max(1, attackers),
                "duration": max(10, duration),
                "seed": seed,
                "retrain": retrain,
                "command": command,
                "staged_inputs": staged_inputs,
                "policy": "NIST-CSW synthetic attack simulation",
            },
        )

        # Queue as realtime command so simulation subroutine actually executes.
        job_id = create_job(
            "simulate-ddos-training-loop",
            "Simulation: DDoS Attacker vs Countermeasure",
            "realtime",
            command,
            timeout_seconds,
        )
        with jobs_lock:
            queue.append(job_id)
            jobs[job_id]["logs"].append(f"[queue] Added to queue (position {len(queue)})")

        record_audit(
            "simulation_run",
            "ok",
            {
                "job_id": job_id,
                "attacker_profile": attacker_profile,
                "defender_profile": defender_profile,
                "architecture_type": architecture_type,
                "countermeasure_mode": countermeasure_mode,
                "intensity": intensity,
                "retrain": retrain,
            },
        )
        return jsonify({"job_id": job_id, "status": "queued"})

    @app.post("/api/jobs/<job_id>/cancel")
    def api_cancel_job(job_id: str):
        denied = enforce_role("operator")
        if denied:
            return denied

        with jobs_lock:
            if job_id not in jobs:
                return jsonify({"error": "Job not found"}), 404

            job = jobs[job_id]
            if job["status"] in {"completed", "failed", "cancelled", "timeout"}:
                return jsonify({"ok": True, "message": f"Job already {job['status']}", "status": job["status"]})

            job["cancel_requested"] = True
            job["pause_requested"] = False
            queue_was_present = False
            if job_id in queue:
                queue.remove(job_id)
                queue_was_present = True

            process = active_processes.get(job_id)

        if queue_was_present:
            complete_job(job_id, "cancelled", -15, ["[cancel] Removed from queue by user"])
            record_audit("job_cancel", "ok", {"job_id": job_id, "mode": "queue-remove"})
            return jsonify({"ok": True, "status": "cancelled"})

        if process and process.poll() is not None:
            complete_job(job_id, "completed", 0, ["[complete] Auto-completed using currently collected data"])
            record_audit("job_cancel", "ok", {"job_id": job_id, "mode": "post-finish"})
            return jsonify({"ok": True, "status": "completed"})

        append_log(job_id, "[cancel] Stop requested; waiting for graceful finalization")
        record_audit("job_cancel", "ok", {"job_id": job_id, "mode": "graceful-stop"})
        return jsonify({"ok": True, "status": "stopping"})

    @app.post("/api/jobs/<job_id>/pause")
    def api_pause_job(job_id: str):
        denied = enforce_role("operator")
        if denied:
            return denied

        with jobs_lock:
            if job_id not in jobs:
                return jsonify({"error": "Job not found"}), 404

            job = jobs[job_id]
            if job["status"] in {"completed", "failed", "cancelled", "timeout"}:
                return jsonify({"ok": True, "message": f"Job already {job['status']}", "status": job["status"]})

            if job["status"] == "queued":
                return jsonify({"ok": False, "error": "Job has not started yet"}), 400

            job["pause_requested"] = True
            job["cancel_requested"] = False
            if job["status"] == "running":
                job["status"] = "paused"
                job["logs"].append("[pause] Pause requested by user")

        record_audit("job_pause", "ok", {"job_id": job_id})
        return jsonify({"ok": True, "status": "paused"})

    @app.post("/api/jobs/<job_id>/resume")
    def api_resume_job(job_id: str):
        denied = enforce_role("operator")
        if denied:
            return denied

        with jobs_lock:
            if job_id not in jobs:
                return jsonify({"error": "Job not found"}), 404

            job = jobs[job_id]
            if job["status"] in {"completed", "failed", "cancelled", "timeout"}:
                return jsonify({"ok": True, "message": f"Job already {job['status']}", "status": job["status"]})

            if job["status"] == "queued":
                return jsonify({"ok": False, "error": "Job has not started yet"}), 400

            job["pause_requested"] = False
            job["cancel_requested"] = False
            job["status"] = "running"
            job["logs"].append("[pause] Task resumed by user")
            process = active_processes.get(job_id)

        if process and process.poll() is None:
            try:
                process.send_signal(signal.SIGCONT)
            except Exception as exc:
                append_log(job_id, f"[warn] Could not resume process: {exc}")
                return jsonify({"ok": False, "error": "Failed to resume process"}), 500

        record_audit("job_resume", "ok", {"job_id": job_id})
        return jsonify({"ok": True, "status": "running"})

    @app.post("/api/jobs/<job_id>/retry")
    def api_retry_job(job_id: str):
        denied = enforce_role("operator")
        if denied:
            return denied

        with jobs_lock:
            if job_id not in jobs:
                return jsonify({"error": "Job not found"}), 404
            job = jobs[job_id]
            command = job.get("command")
            if not command:
                return jsonify({"error": "Job has no command to retry"}), 400

            mode = job.get("mode", "realtime")
            action_id = job.get("action_id", "retry")
            title = f"Retry: {job.get('title', action_id)}"
            timeout_seconds = int(job.get("timeout_seconds") or DEFAULT_JOB_TIMEOUT_SECONDS)

        new_job_id, status = queue_command_job(action_id, title, mode, command, timeout_seconds)
        record_audit("job_retry", "ok", {"source_job_id": job_id, "new_job_id": new_job_id})
        return jsonify({"ok": True, "job_id": new_job_id, "status": status})

    @app.get("/api/jobs/<job_id>")
    def api_job(job_id: str):
        with jobs_lock:
            if job_id not in jobs:
                return jsonify({"error": "Job not found"}), 404
            return jsonify(jobs[job_id])

    @app.get("/api/jobs")
    def api_jobs():
        with jobs_lock:
            ordered = sorted(jobs.values(), key=lambda item: item["started_at"], reverse=True)
            return jsonify(
                {
                    "jobs": [
                        {
                            "id": item["id"],
                            "title": item["title"],
                            "status": item["status"],
                            "return_code": item["return_code"],
                            "mode": item["mode"],
                            "timeout_seconds": item.get("timeout_seconds"),
                            "submitted_by": item.get("submitted_by"),
                            "can_retry": bool(item.get("command")),
                            "started_at": item["started_at"],
                        }
                        for item in ordered[:30]
                    ]
                }
            )

    return app


if __name__ == "__main__":
    application = create_app()
    # threaded=True allows multiple simultaneous users even in dev mode.
    # Use production_server.py (waitress) for proper multi-user production use.
    application.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
