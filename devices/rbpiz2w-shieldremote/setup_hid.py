#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_hid.py — Configure a Pi Zero 2 W as a composite USB HID gadget (Keyboard + Consumer Control).

This script uses Linux ConfigFS to expose TWO HID interfaces to the host (your Shield):
  • /dev/hidg0 → Boot Keyboard (arrows, Enter, Esc) — 8-byte input report
  • /dev/hidg1 → Consumer Control (Play/Pause, Next/Prev, Vol±) — 3-byte input report
                  (Report ID + 2-byte payload)

Why this file exists:
  - It makes the gadget setup **idempotent** and **self-healing** (rewrites bad/ASCII descriptors).
  - It unbinds, edits, relinks, and rebinds in the correct order to avoid EBUSY.
  - It documents descriptors in plain English so you can safely extend/modify them.

USAGE (run as root):
  sudo ./setup_hid.py            # create/update gadget, link functions, bind UDC
  sudo ./setup_hid.py --status   # show current config & descriptor sanity
  sudo ./setup_hid.py --rebind   # unbind/bind without touching descriptors
  sudo ./setup_hid.py --teardown # unbind and remove gadget

Prereqs (you’ve done these already):
  • /boot/firmware/config.txt     includes: dtoverlay=dwc2
  • /boot/firmware/cmdline.txt    has: modules-load=dwc2 (after rootwait)
  • Modules present: dwc2, libcomposite (we modprobe libcomposite here)
"""

from __future__ import annotations
import argparse
import os
import sys
import time
import re
from pathlib import Path
from typing import Optional

# ----------------------------
# ConfigFS layout (paths)
# ----------------------------
G_NAME = "gtv"  # gadget name under /sys/kernel/config/usb_gadget/
G_ROOT = Path(f"/sys/kernel/config/usb_gadget/{G_NAME}")
CFG    = G_ROOT / "configs" / "c.1"
STR_EN = G_ROOT / "strings" / "0x409"
CFG_EN = CFG / "strings" / "0x409"
KB_FUNC = G_ROOT / "functions" / "hid.keyboard"
CC_FUNC = G_ROOT / "functions" / "hid.consumer"
UDC_FILE = G_ROOT / "UDC"

# ----------------------------
# Helper: parse commented hex into bytes
# ----------------------------
def hex_bytes(s: str) -> bytes:
    """
    Return bytes from a human-friendly, commented hex blob.
    Accepts tokens like '05', '0x05', separated by spaces/newlines/commas.
    Strips #… and //… to end-of-line, and /* … */ blocks.
    """
    # Strip /* ... */ comments
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    # Strip //... and #... comments
    s = re.sub(r"(?m)\s*(//|#).*?$", "", s)
    # Normalize 0xAB → AB
    s = re.sub(r"0x([0-9A-Fa-f]{2})\b", r"\1", s)
    # Pull all two-hex-digit tokens
    tokens = re.findall(r"\b[0-9A-Fa-f]{2}\b", s)
    return bytes(int(t, 16) for t in tokens)

# =============================================================================
# Descriptor reference (Keyboard)
# -----------------------------------------------------------------------------
# Standard “boot keyboard” (HID Usage Page 0x07).
# Report is 8 bytes:
#   byte0: modifier bits (LCtrl,LShift,LAlt,LGUI, RCtrl,RShift,RAlt,RGUI)
#   byte1: reserved (0)
#   byte2..7: up to 6 simultaneous keycodes (0 when no key)
# =============================================================================
KB_DESC = hex_bytes("""
05 01  # Usage Page (Generic Desktop)
09 06  # Usage (Keyboard)
A1 01  # Collection (Application)

  05 07  # Usage Page (Keyboard/Keypad)
  19 E0  # Usage Minimum (0xE0 = LeftControl)
  29 E7  # Usage Maximum (0xE7 = Right GUI)
  15 00  # Logical Minimum (0)
  25 01  # Logical Maximum (1)          → each modifier is 1 bit
  75 01  # Report Size (1)
  95 08  # Report Count (8)             → BYTE 0 (8 modifier bits)
  81 02  # Input (Data,Var,Abs)

  95 01  # Report Count (1)
  75 08  # Report Size (8)
  81 03  # Input (Const,Var,Abs)        → BYTE 1 (reserved)

  95 05  # Report Count (5)
  75 01  # Report Size (1)
  05 08  # Usage Page (LEDs)
  19 01  # Usage Minimum (Num Lock)
  29 05  # Usage Maximum (Kana)
  91 02  # Output (Data,Var,Abs)        → 5 LED output bits (host→device)

  95 01  # Report Count (1)
  75 03  # Report Size (3)
  91 03  # Output (Const,Var,Abs)       → LED padding

  95 06  # Report Count (6)
  75 08  # Report Size (8)
  15 00  # Logical Minimum (0)
  25 65  # Logical Maximum (0x65 = 101) → allowed keycode range
  05 07  # Usage Page (Keyboard/Keypad)
  19 00  # Usage Minimum (0)
  29 65  # Usage Maximum (101)
  81 00  # Input (Data,Array)           → BYTES 2..7 (key slots)

C0     # End Collection
""")

# =============================================================================
# Descriptor reference (Consumer Control)
# -----------------------------------------------------------------------------
# Three-byte input report (Report ID + 2-byte payload):
#   byte0 = Report ID (1)
#   byte1 = 5 one-bit fields, in THIS ORDER:
#            bit0 = Play/Pause    (Usage 0xCD)
#            bit1 = Next Track    (Usage 0xB5)
#            bit2 = Previous      (Usage 0xB6)
#            bit3 = Volume Up     (Usage 0xE9)
#            bit4 = Volume Down   (Usage 0xEA)
#            bits5..7 = padding
#   byte2 = full padding byte     (to make payload 2 bytes so writes never block)
# =============================================================================
CC_DESC = hex_bytes("""
05 0C  # Usage Page (Consumer)
09 01  # Usage (Consumer Control)
A1 01  # Collection (Application)

85 01  # Report ID (1)  → adds 1 byte to each input report

15 00  # Logical Min (0)
25 01  # Logical Max (1)     → on/off bits

09 CD  # Usage (Play/Pause)
09 B5  # Usage (Scan Next)
09 B6  # Usage (Scan Previous)
09 E9  # Usage (Volume Up)
09 EA  # Usage (Volume Down)

75 01  # Report Size (1)
95 05  # Report Count (5)    → 5 actual data bits in BYTE 1
81 02  # Input (Data,Var,Abs)

95 03  # Report Count (3)    → pad to a full byte (still BYTE 1)
81 03  # Input (Const,Var,Abs)

75 08  # Report Size (8)
95 01  # Report Count (1)    → BYTE 2 (full padding byte)
81 03  # Input (Const,Var,Abs)

C0     # End Collection
""")

# ----------------------------
# Small helpers
# ----------------------------
def _require_root():
    if os.geteuid() != 0:
        sys.exit("Run as root (sudo).")

def _run(cmd: str) -> None:
    os.system(cmd)

def _write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)

def _write_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(data)

def _read_text(path: Path) -> str:
    try:
        return path.read_text().strip()
    except Exception:
        return ""

def _file_has_literal_backslash_x(path: Path) -> bool:
    """True if file contains the literal two characters '\' 'x' (an ASCII heredoc mistake)."""
    try:
        s = path.read_text(errors="ignore")
        return "\\x" in s
    except Exception:
        return False

def udc_current() -> str:
    return _read_text(UDC_FILE)

def udc_available() -> Optional[str]:
    try:
        names = sorted(p.name for p in Path("/sys/class/udc").iterdir())
        return names[0] if names else None
    except Exception:
        return None

def unbind():
    if UDC_FILE.exists() and udc_current():
        _write_text(UDC_FILE, "")
        time.sleep(0.1)

def bind():
    name = udc_available()
    if not name:
        sys.exit("No UDC found in /sys/class/udc (dwc2 not loaded or OTG not available).")
    _write_text(UDC_FILE, name)

# ----------------------------
# Ensure functions/descriptors
# ----------------------------
def ensure_gadget_root():
    # IDs and strings (these are what the host sees)
    G_ROOT.mkdir(parents=True, exist_ok=True)
    _write_text(G_ROOT / "idVendor",  "0x1d6b")   # Linux Foundation (fine for internal use)
    _write_text(G_ROOT / "idProduct", "0x0104")   # arbitrary composite device PID
    _write_text(G_ROOT / "bcdUSB",    "0x0200")   # USB 2.0

    STR_EN.mkdir(parents=True, exist_ok=True)
    _write_text(STR_EN / "serialnumber", "0123456789")
    _write_text(STR_EN / "manufacturer", "Pi Zero 2 W")
    _write_text(STR_EN / "product",      "Shield HID Remote")

    CFG_EN.mkdir(parents=True, exist_ok=True)
    _write_text(CFG_EN / "configuration", "Cfg 1")
    _write_text(CFG / "MaxPower", "250")  # 500 mA in 2mA units

def ensure_keyboard():
    KB_FUNC.mkdir(parents=True, exist_ok=True)
    # Attributes must be set while unbound/unlinked
    _write_text(KB_FUNC / "protocol", "1")        # 1 = keyboard
    _write_text(KB_FUNC / "subclass", "1")        # 1 = boot interface
    _write_text(KB_FUNC / "report_length", "8")   # 8-byte input reports

    desc = KB_FUNC / "report_desc"
    # Rewrite if missing, ASCII "\x" heredoc, or wrong length/content
    if (not desc.exists()) or _file_has_literal_backslash_x(desc) or (len(desc.read_bytes()) != len(KB_DESC)):
        _write_bytes(desc, KB_DESC)

def ensure_consumer():
    CC_FUNC.mkdir(parents=True, exist_ok=True)
    _write_text(CC_FUNC / "protocol", "0")
    _write_text(CC_FUNC / "subclass", "0")
    _write_text(CC_FUNC / "report_length", "3")   # 3-byte input reports (ReportID + 2-byte payload)

    desc = CC_FUNC / "report_desc"
    if (not desc.exists()) or _file_has_literal_backslash_x(desc) or (len(desc.read_bytes()) != len(CC_DESC)):
        _write_bytes(desc, CC_DESC)

def ensure_links():
    CFG.mkdir(parents=True, exist_ok=True)
    for func, name in ((KB_FUNC, "hid.keyboard"), (CC_FUNC, "hid.consumer")):
        link = CFG / name
        if link.exists() or link.is_symlink():
            try:
                if not link.is_symlink() or link.resolve() != func:
                    link.unlink(missing_ok=True)
                    link.symlink_to(func)
            except Exception:
                link.unlink(missing_ok=True)
                link.symlink_to(func)
        else:
            link.symlink_to(func)

# ----------------------------
# User commands
# ----------------------------
def cmd_status():
    print(f"Gadget root: {G_ROOT}  (exists={G_ROOT.exists()})")
    print(f"UDC bound: {udc_current() or '<none>'}")
    print("Config links:")
    if CFG.exists():
        for p in sorted(CFG.iterdir()):
            if p.is_symlink():
                print(f"  {p.name} -> {os.readlink(p)}")
    else:
        print("  <none>")

    for label, func in (("keyboard", KB_FUNC), ("consumer", CC_FUNC)):
        rl = _read_text(func / "report_length") if func.exists() else "<missing>"
        print(f"{label:9} report_length: {rl}")
        rd = func / "report_desc"
        if rd.exists():
            raw = rd.read_bytes()
            print(f"{label:9} desc bytes: {len(raw):3d}  ascii-escape? {'YES' if _file_has_literal_backslash_x(rd) else 'no'}")
        else:
            print(f"{label:9} desc: <missing>")

def cmd_rebind():
    if not G_ROOT.exists():
        sys.exit("Gadget not found.")
    unbind()
    bind()
    print(f"Rebound to UDC: {udc_current()}")

def cmd_teardown():
    if not G_ROOT.exists():
        print("Gadget not present.")
        return
    unbind()
    # unlink functions from config
    for name in ("hid.keyboard", "hid.consumer"):
        (CFG / name).unlink(missing_ok=True)
    # remove functions (best-effort)
    for fn in (KB_FUNC, CC_FUNC):
        try:
            for _ in fn.iterdir():  # ensure empty
                pass
        except Exception:
            pass
        try:
            fn.rmdir()
        except Exception:
            pass
    # remove strings/config dirs (best-effort)
    for p in (CFG_EN,):
        try: p.rmdir()
        except Exception: pass
    try: CFG.rmdir()
    except Exception: pass
    for p in (STR_EN,):
        try: p.rmdir()
        except Exception: pass
    try:
        G_ROOT.rmdir()
        print("Gadget removed.")
    except Exception as e:
        print(f"Leftovers remained (ok): {e}")

def cmd_setup():
    # Stop anything that might be writing to /dev/hidg* before we touch config
    # (commented so this script stays self-contained; do this outside if needed)
    # _run("systemctl stop mqtt_to_shield_hid.service >/dev/null 2>&1 || true")

    # Ensure libcomposite (ConfigFS gadget framework)
    _run("/sbin/modprobe libcomposite >/dev/null 2>&1 || true")

    # Always create IDs/strings/config dirs up front
    ensure_gadget_root()

    # Unbind if currently active (we will relink & rebind cleanly)
    was_bound = bool(udc_current())
    if was_bound:
        unbind()

    # Unlink functions before changing their attributes (avoids EBUSY)
    for name in ("hid.keyboard", "hid.consumer"):
        (CFG / name).unlink(missing_ok=True)

    # (Re)create function attributes + descriptors
    ensure_keyboard()
    ensure_consumer()

    # Link both functions into config, then bind
    ensure_links()
    bind()

    print(f"{'Re' if was_bound else ''}Bound to UDC: {udc_current()}")

# ----------------------------
# Main
# ----------------------------
def main():
    _require_root()
    ap = argparse.ArgumentParser(description="Setup/teardown USB HID gadget (Keyboard + Consumer Control).")
    ap.add_argument("--status",   action="store_true", help="Show current gadget state.")
    ap.add_argument("--rebind",   action="store_true", help="Unbind/bind without changing descriptors.")
    ap.add_argument("--teardown", action="store_true", help="Unbind and remove gadget.")
    args = ap.parse_args()

    if args.status:
        cmd_status(); return
    if args.rebind:
        cmd_rebind(); return
    if args.teardown:
        cmd_teardown(); return
    cmd_setup()

if __name__ == "__main__":
    main()
