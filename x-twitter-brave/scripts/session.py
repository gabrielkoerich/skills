#!/usr/bin/env python3
"""Shared headless Brave for every agent that uses this skill, CDP on 18801, on macOS and Linux.

Usage: session.py start [--window] <run-id> | stop <run-id>
start registers the run and launches headless Brave if nothing answers on 18801, --window shows it, for logging in.
stop unregisters the run and quits Brave only when no other run is registered, so one agent never closes the
browser under another. It quits only a Brave this script launched, never one started by hand.
X_BRAVE_PROFILE picks the profile under ~/.claude/browser (default "Default"), BRAVE_BIN the Brave binary
"""

import http.client
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROFILE = Path.home() / ".claude/browser" / os.environ.get("X_BRAVE_PROFILE", "Default") / "user-data"
RUNS = PROFILE.parent / "runs"
PID_FILE = PROFILE.parent / "brave.pid"
PORT = 18801
MACOS_BRAVE = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
# A run that crashed before stop stops counting after this, so it cannot keep Brave open forever
STALE_SECONDS = 2 * 3600


def brave() -> str:
    names = [os.environ["BRAVE_BIN"]] if "BRAVE_BIN" in os.environ else [MACOS_BRAVE, "brave-browser", "brave", "brave-browser-stable"]
    found = next(filter(None, map(shutil.which, names)), None)
    if found is None:
        raise SystemExit(f"Brave not found, tried {', '.join(names)}, install it or set BRAVE_BIN")

    return found


def listening() -> bool:
    try:
        conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=2)
        conn.request("GET", "/json/version")
        return conn.getresponse().status == 200
    except OSError:
        return False


def active_runs() -> list[Path]:
    if not RUNS.exists():
        return []

    now = time.time()
    return [run for run in RUNS.iterdir() if now - run.stat().st_mtime < STALE_SECONDS]


def start(run_id: str, window: bool) -> None:
    # As root Brave runs only with --no-sandbox, and these pages are untrusted, so jobs run as the desktop user
    if os.geteuid() == 0:
        raise SystemExit("refusing to run Brave as root, run the job as the user that owns the profile")

    up = listening()
    if window and up:
        raise SystemExit("Brave already holds the profile, a window opens once no run uses it")

    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / run_id).touch()
    if up:
        return

    mode = ["https://x.com"] if window else ["--headless=new"]
    env = dict(os.environ)
    # A job or an SSH session on a Linux desktop has no DISPLAY, the window goes to the desktop's screen
    if window and sys.platform == "linux" and not (env.get("DISPLAY") or env.get("WAYLAND_DISPLAY")):
        env["DISPLAY"] = ":0"
        env.setdefault("XAUTHORITY", str(Path.home() / ".Xauthority"))

    process = subprocess.Popen([brave(), f"--user-data-dir={PROFILE}", f"--remote-debugging-port={PORT}", "--no-first-run", *mode], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    _ = PID_FILE.write_text(str(process.pid))
    for _ in range(20):
        if listening():
            return

        time.sleep(0.5)

    raise SystemExit(f"Brave did not open CDP on {PORT}")


def stop(run_id: str) -> None:
    (RUNS / run_id).unlink(missing_ok=True)
    others = active_runs()
    if others:
        print(f"Brave left open, {len(others)} other run(s) still use it")
        return

    if not PID_FILE.exists():
        return

    pid = PID_FILE.read_text().strip()
    PID_FILE.unlink()
    # The pid may have been reused since start, so only quit a process still running this profile
    args = subprocess.run(["ps", "-o", "args=", "-p", pid], capture_output=True, text=True).stdout
    if str(PROFILE) not in args:
        return

    _ = subprocess.run(["kill", pid], check=True)
    print(f"Brave {pid} stopped")


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--window"]
    if len(args) != 2 or args[0] not in ("start", "stop"):
        raise SystemExit("usage: session.py start [--window] <run-id> | stop <run-id>")

    if args[0] == "start":
        start(args[1], "--window" in sys.argv)
    else:
        stop(args[1])


if __name__ == "__main__":
    main()
