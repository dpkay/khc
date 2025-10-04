#!/usr/bin/env python3
"""
start_khc_services.py
=====================

Launch multiple Python "services" into a single tmux session (one window per service).
This is a lightweight way to keep small daemons running, restart them easily,
and tail their logs—without Docker or launchd plists.

───────────────────────────────────────────────────────────────────────────────
What it does
------------
• Kills any existing tmux session named `khc`
• Creates a fresh session with the first service
• Adds one tmux window per remaining service
• Pipes stdout/stderr of each service to:
    ~/Library/Logs/khc/<service>.log

Where service scripts live
--------------------------
• Put your service .py files in `SERVICES_ABS_DIR`
• Each service name in `SERVICES` must correspond to a file "<service>.py"

Example:
    SERVICES_ABS_DIR = ~/sandbox/khc_mac/services
    SERVICES = [ "khc-mqtt-to-kvm", "khc-mqtt-to-reaper" ]
    => expects:
        ~/sandbox/khc_mac/services/khc-mqtt-to-kvm.py
        ~/sandbox/khc_mac/services/khc-mqtt-to-reaper.py

Dependencies
------------
• macOS (or Linux), tmux installed:  `brew install tmux`
• A working Python3:                 `which python3` should resolve

Recommended environment
-----------------------
• If your services read secrets (e.g., MQTT_HOST/USER/PASSWORD), export them
  in your shell profile (~/.zshrc) or source a private file before launching.

Runbook / Common commands
-------------------------
Start (or restart everything cleanly):
    ./start_khc_services.py

See tmux sessions / windows:
    tmux ls
    tmux list-windows -t khc

Attach to the session (watch live output):
    tmux attach -t khc
    # Detach: Ctrl-b then d

Tail logs (both at once):
    tail -f ~/Library/Logs/khc/*.log

Restart a single service window (example: khc-mqtt-to-reaper):
    tmux kill-window -t khc:khc-mqtt-to-reaper
    # Then re-run:
    ./start_khc_services.py
    # (reaper window will be recreated if missing)

Stop everything:
    tmux kill-session -t khc

Add to Login Items (auto-start at login):
    System Settings → Users & Groups → Login Items → + → select this file

Troubleshooting
---------------
• "tmux: command not found" → Install tmux: `brew install tmux`
• A service window appears then exits → Check its log:
      tail -n 200 ~/Library/Logs/khc/<service>.log
  Common causes: missing env vars, wrong serial port, wrong OSC port, etc.
• Session doesn’t exist / "no server running…" → Just re-run this script.
• You changed SERVICE names or directory → Update SERVICES / SERVICES_ABS_DIR below.
───────────────────────────────────────────────────────────────────────────────
"""

import os
import shlex
import subprocess
import sys
from pathlib import Path

# ============================
# Configuration
# ============================

from pathlib import Path
import os, subprocess, sys

# Project root and python dir (fixed layout)
KHC_ROOT   = Path.home() / "khc"
PYTHON_DIR = KHC_ROOT / "python"

# Require venv: abort if missing
VENV_PY = PYTHON_DIR / ".venv" / "bin" / "python"
if not VENV_PY.exists():
    sys.stderr.write(
        f"[fatal] Missing venv: {VENV_PY}\n"
        f"Create it with:\n"
        f"  cd {PYTHON_DIR}\n"
        f"  python3 -m venv .venv\n"
        f"  . .venv/bin/activate && pip install -e .\n"
    )
    sys.exit(1)

# Always use the venv's python for services
PY = str(VENV_PY)

# tmux binary (fail if not found)
TMUX = os.environ.get("TMUX") or subprocess.getoutput("command -v tmux")
if not TMUX:
    sys.stderr.write("[fatal] tmux not found on PATH (try: brew install tmux)\n")
    sys.exit(1)

# Logs dir
LOGDIR = Path.home() / "Library" / "Logs" / "khc"

# Tmux session name
SESSION = "khc"

# Short service names (without package prefix)
SERVICES = [
    "khc_mqtt_to_kvm",
    "khc_mqtt_to_reaper",
    "khc_sparrow_to_mqtt",
]

# Common module prefix (all services live here)
MODULE_PREFIX = "khc.services.mac_mini"

# Optional extra environment variables to inject into tmux
EXTRA_ENV = {
    # "DEBUG": "1",
}


# ============================
# Helpers
# ============================

def die(msg: str) -> None:
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(1)

def tmux(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([TMUX, *args], check=False, capture_output=True, text=True)

def check_cmd_exists(path_or_name: str, label: str) -> None:
    if not path_or_name:
        die(f"{label} not found on PATH")
    p = Path(path_or_name)
    if not p.exists() and not path_or_name.startswith("/"):
        return
    if p.exists() and not p.is_file():
        die(f"{label} at {path_or_name} is not a file")

def py_can_import(py: str, module: str) -> tuple[bool, str]:
    code = f"import importlib; importlib.import_module({module!r}); print('OK')"
    r = subprocess.run([py, "-c", code], capture_output=True, text=True)
    if r.returncode == 0 and "OK" in r.stdout:
        return True, ""
    return False, (r.stderr or r.stdout).strip()


# ============================
# Sanity checks
# ============================

check_cmd_exists(TMUX, "tmux")
check_cmd_exists(PY, "python")

LOGDIR.mkdir(parents=True, exist_ok=True)

# Verify all modules importable
failed = []
for svc in SERVICES:
    mod = f"{MODULE_PREFIX}.{svc}"
    ok, err = py_can_import(PY, mod)
    if not ok:
        failed.append((mod, err))
if failed:
    msg = ["Some modules failed to import:"]
    for mod, err in failed:
        msg.append(f"  - {mod}\n      {err}")
    msg.append("\nFix by activating venv and installing:")
    msg.append("  cd ~/khc/python && . .venv/bin/activate && pip install -e .")
    die("\n".join(msg))


# ============================
# Launch flow
# ============================

# Export any custom env vars to tmux
for k, v in EXTRA_ENV.items():
    tmux("set-environment", "-g", k, v)

# Kill old session
tmux("kill-session", "-t", SESSION)

# First window
first = SERVICES[0]
first_mod = f"{MODULE_PREFIX}.{first}"
first_log = LOGDIR / f"{first}.log"
first_cmd = f"{shlex.quote(PY)} -u -m {shlex.quote(first_mod)} 2>&1 | tee -a {shlex.quote(str(first_log))}"

r = tmux("new-session", "-d", "-s", SESSION, "-n", first, "sh", "-lc", first_cmd)
if r.returncode != 0:
    die(f"tmux new-session failed: {r.stderr.strip()}")
print(f"[ok] created session '{SESSION}' with window '{first}'")

# Remaining windows
for svc in SERVICES[1:]:
    mod = f"{MODULE_PREFIX}.{svc}"
    log = LOGDIR / f"{svc}.log"
    cmd = f"{shlex.quote(PY)} -u -m {shlex.quote(mod)} 2>&1 | tee -a {shlex.quote(str(log))}"
    r = tmux("new-window", "-t", f"{SESSION}:", "-n", svc, "sh", "-lc", cmd)
    if r.returncode != 0:
        print(f"[warn] could not start '{svc}': {r.stderr.strip()}")
    else:
        print(f"[ok] started '{svc}'")

print(f"[done] attach with: tmux attach -t {SESSION}")
print(f"[logs]  tail -f {LOGDIR}/*.log")