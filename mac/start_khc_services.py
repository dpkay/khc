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
    ~/Library/Logs/khc_services/<service>.log

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
    tail -f ~/Library/Logs/khc_services/*.log

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
      tail -n 200 ~/Library/Logs/khc_services/<service>.log
  Common causes: missing env vars, wrong serial port, wrong OSC port, etc.
• Session doesn’t exist / "no server running…" → Just re-run this script.
• You changed SERVICE names or directory → Update SERVICES / SERVICES_ABS_DIR below.
───────────────────────────────────────────────────────────────────────────────
"""

import os
import subprocess
import sys
from pathlib import Path

# ============================
# Configuration (edit here)
# ============================

# Name of the tmux session that will hold your windows
SESSION = "khc"

# Get absolute path to the directory where this script lives
SCRIPT_DIR = Path(__file__).resolve().parent

# Point SERVICES_ABS_DIR to a "services" sibling directory
SERVICES_ABS_DIR = SCRIPT_DIR / "services"

# List of service *base names*. Each must exist as "<name>.py" in SERVICES_ABS_DIR.
# These names are also used for tmux window names and log filenames.
SERVICES = [
    "khc-mqtt-to-kvm",
    "khc-mqtt-to-reaper",
    "khc-sparrow-to-mqtt"
]

# Where logs go (rotated manually with logrotate/newsyslog if desired)
LOGDIR = Path.home() / "Library" / "Logs" / "khc_services"

# Optionally pin tmux/python paths via env; otherwise we use PATH
TMUX = os.environ.get("TMUX") or subprocess.getoutput("command -v tmux")
PY   = os.environ.get("PY")   or subprocess.getoutput("command -v python3")


# ============================
# Helpers
# ============================

def die(msg: str) -> None:
    """Print an error and exit."""
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(1)

def tmux(*args: str) -> subprocess.CompletedProcess:
    """Run tmux with the given arguments; do not raise if it fails."""
    return subprocess.run([TMUX, *args], check=False, capture_output=True, text=True)


# ============================
# Sanity checks
# ============================

if not TMUX or not Path(TMUX).exists():
    die("tmux not found (brew install tmux) or set TMUX=/path/to/tmux")
if not PY or not Path(PY).exists():
    die("python3 not found or set PY=/path/to/python3")
if not SERVICES_ABS_DIR.is_dir():
    die(f"missing dir: {SERVICES_ABS_DIR}")

missing = [svc for svc in SERVICES if not (SERVICES_ABS_DIR / f"{svc}.py").is_file()]
if missing:
    die("missing scripts:\n  " + "\n  ".join(f"{SERVICES_ABS_DIR}/{m}.py" for m in missing))

LOGDIR.mkdir(parents=True, exist_ok=True)


# ============================
# Launch flow
# ============================

# 1) Kill any existing session (ignore errors if it doesn't exist).
tmux("kill-session", "-t", SESSION)

# 2) Create a fresh session with the first service.
first = SERVICES[0]
first_cmd = f"{PY} -u {SERVICES_ABS_DIR}/{first}.py 2>&1 | tee -a '{LOGDIR}/{first}.log'"

#   Use `sh -lc` so the full pipeline runs in a login-compatible shell,
#   and `-u` (unbuffered) so logs stream immediately.
r = tmux("new-session", "-d", "-s", SESSION, "-n", first, "sh", "-lc", first_cmd)
if r.returncode != 0:
    die(f"tmux new-session failed: {r.stderr.strip()}")
print(f"[ok] created session '{SESSION}' with window '{first}'")

# 3) Add one window per remaining service.
for svc in SERVICES[1:]:
    cmd = f"{PY} -u {SERVICES_ABS_DIR}/{svc}.py 2>&1 | tee -a '{LOGDIR}/{svc}.log'"
    # IMPORTANT: target "SESSION:" (with trailing colon) so tmux picks the next free index
    r = tmux("new-window", "-t", f"{SESSION}:", "-n", svc, "sh", "-lc", cmd)
    if r.returncode != 0:
        # Non-fatal: we keep going and report the stderr line
        print(f"[warn] could not start '{svc}': {r.stderr.strip()}")
    else:
        print(f"[ok] started '{svc}'")

print(f"[done] attach with: tmux attach -t {SESSION}")
print(f"[logs]  tail -f {LOGDIR}/*.log")
