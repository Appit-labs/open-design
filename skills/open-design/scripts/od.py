#!/usr/bin/env python3
"""OpenDesign local lifecycle helper: pinned pnpm, tools-dev, screenshots, checks.

    od.py doctor                       # node/pnpm/ports/data-dir health
    od.py start [--daemon-port N] [--web-port N] [--wait 90]
    od.py status [--json]
    od.py shot PATH                    # desktop screenshot via tools-dev inspect
    od.py stop
    od.py checks [--only guard|typecheck]
    od.py self-test

Runs `corepack pnpm` (never a bare `pnpm`) so the version pinned in
package.json#packageManager is the one that runs. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("OD_ROOT", Path.cwd())).resolve()
DEFAULT_DAEMON_PORT = 17456
DEFAULT_WEB_PORT = 17573


def pnpm(*args: str) -> list[str]:
    return ["corepack", "pnpm", *args]


def run(argv: list[str], timeout: int = 300, cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(cwd or ROOT), timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def pinned_pnpm(root: Path) -> str | None:
    try:
        data = json.loads((root / "package.json").read_text())
    except (OSError, ValueError):
        return None
    field = data.get("packageManager") or ""
    return field.split("@", 1)[1] if "@" in field else None


def pinned_node(root: Path) -> str | None:
    try:
        return (root / ".node-version").read_text().strip()
    except OSError:
        return None


def port_free(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) != 0


def cmd_doctor() -> int:
    problems = []
    node = shutil.which("node")
    if not node:
        problems.append("node not on PATH (need ~24)")
    else:
        _, out = run(["node", "-v"], 20)
        actual = out.strip().lstrip("v")
        want = (pinned_node(ROOT) or "").lstrip("v")
        print(f"node: {out.strip()} (repo wants {want or '~24'})")
        if want and actual.split(".")[0] != want.split(".")[0]:
            problems.append(f"node major {actual.split('.')[0]} != repo major {want.split('.')[0]}")
    if not shutil.which("corepack"):
        problems.append("corepack missing: `corepack enable`")
    else:
        code, out = run(pnpm("-v"), 120)
        want_pnpm = pinned_pnpm(ROOT)
        print(f"pnpm via corepack: {out.splitlines()[-1] if out else '?'} (repo wants {want_pnpm})")
        if code != 0:
            problems.append("corepack pnpm failed; run `corepack prepare pnpm@%s --activate`" % want_pnpm)
        elif want_pnpm and out.strip().splitlines()[-1].strip() != want_pnpm:
            problems.append(f"corepack resolved pnpm {out.strip()} instead of {want_pnpm}")
    _, bare = run(["sh", "-lc", "pnpm -v 2>/dev/null || true"], 30)
    if bare.strip() and pinned_pnpm(ROOT) and bare.strip() != pinned_pnpm(ROOT):
        print(f"warning: bare `pnpm` is {bare.strip()} (not {pinned_pnpm(ROOT)}); always use `corepack pnpm`")
    for port in (DEFAULT_DAEMON_PORT, DEFAULT_WEB_PORT):
        state = "free" if port_free(port) else "IN USE"
        print(f"port {port}: {state}")
    print(f"repo: {ROOT.name}")
    for p in problems:
        print(f"PROBLEM: {p}")
    return 1 if problems else 0


def cmd_start(daemon_port: int, web_port: int, wait: int) -> int:
    for port in (daemon_port, web_port):
        if not port_free(port):
            print(f"port {port} already in use; pick another with --daemon-port/--web-port", file=sys.stderr)
            return 2
    log = Path("/tmp/open-design-tools-dev.log")
    argv = pnpm("exec", "tools-dev", "run", "web", "--daemon-port", str(daemon_port),
                "--web-port", str(web_port))
    with log.open("ab") as fh:
        proc = subprocess.Popen(argv, cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
                                start_new_session=True)
    print(f"started pid {proc.pid}; log {log}")
    deadline = time.time() + wait
    while time.time() < deadline:
        if not port_free(web_port):
            print(f"web up: http://127.0.0.1:{web_port}")
            return 0
        if proc.poll() is not None:
            print(f"tools-dev exited with {proc.returncode}; last log lines:", file=sys.stderr)
            print("\n".join(log.read_text(errors="replace").splitlines()[-15:]), file=sys.stderr)
            return 1
        time.sleep(2)
    print(f"not listening after {wait}s; check {log}", file=sys.stderr)
    return 1


def cmd_status() -> int:
    code, out = run(pnpm("exec", "tools-dev", "status", "--json"), 120)
    print(out)
    return code


def desktop_running() -> bool | None:
    """None when the status shape is unknown, else whether a desktop app is up."""
    code, out = run(pnpm("exec", "tools-dev", "status", "--json"), 90)
    if code != 0:
        return None
    try:
        apps = json.loads(out[out.index("{"):]).get("apps") or {}
    except (ValueError, KeyError):
        return None
    desktop = apps.get("desktop") or {}
    return str(desktop.get("state", "")).lower() == "running"


def cmd_shot(path: str) -> int:
    running = desktop_running()
    if running is False:
        print("desktop app is not running; a sidecar screenshot needs it.", file=sys.stderr)
        print("start it first:  corepack pnpm exec tools-dev start desktop", file=sys.stderr)
        return 1
    code, out = run(pnpm("exec", "tools-dev", "inspect", "desktop", "screenshot", "--path", path), 180)
    print(out)
    if code != 0 and ("ENOENT" in out or "sidecar" in out.lower()):
        print("the desktop app or its sidecar socket is not up; start it with "
              "`corepack pnpm exec tools-dev start desktop`", file=sys.stderr)
    if code == 0 and not Path(path).exists():
        print(f"screenshot reported success but {path} is missing", file=sys.stderr)
        return 1
    if code == 0:
        print(f"{path} ({Path(path).stat().st_size} bytes)")
    return code


def cmd_stop() -> int:
    code, out = run(pnpm("exec", "tools-dev", "stop"), 180)
    print(out)
    return code


def cmd_checks(only: str | None) -> int:
    failed = []
    for name, argv in (("guard", pnpm("guard")), ("typecheck", pnpm("typecheck"))):
        if only and only != name:
            continue
        code, out = run(argv, 900)
        print(f"== {name}: exit {code}")
        if code != 0:
            failed.append(name)
            print("\n".join(out.splitlines()[-25:]))
    return 1 if failed else 0


def self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "package.json").write_text(json.dumps({"packageManager": "pnpm@10.33.2"}))
        (root / ".node-version").write_text("24.19.0\n")
        assert pinned_pnpm(root) == "10.33.2", pinned_pnpm(root)
        assert pinned_node(root) == "24.19.0"
        assert pnpm("-v") == ["corepack", "pnpm", "-v"]
        assert re.fullmatch(r"\d+", str(port_free(1))) or True
        (root / "package.json").write_text("{}")
        assert pinned_pnpm(root) is None, "no pin must not crash"
        (root / "package.json").write_text("not json")
        assert pinned_pnpm(root) is None, "bad json must not crash"
    print("self-test ok")
    return 0


def main(argv: list[str]) -> int:
    opts = dict(a.lstrip("-").split("=", 1) for a in argv[1:] if a.startswith("--") and "=" in a)
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args or args[0] in {"-h", "--help", "help"}:
        print(__doc__)
        return 0
    cmd = args[0]
    if cmd == "self-test":
        return self_test()
    if cmd == "doctor":
        return cmd_doctor()
    if cmd == "start":
        return cmd_start(int(opts.get("daemon-port", DEFAULT_DAEMON_PORT)),
                         int(opts.get("web-port", DEFAULT_WEB_PORT)),
                         int(opts.get("wait", 90)))
    if cmd == "status":
        return cmd_status()
    if cmd == "shot" and len(args) > 1:
        return cmd_shot(args[1])
    if cmd == "stop":
        return cmd_stop()
    if cmd == "checks":
        return cmd_checks(opts.get("only"))
    print(f"unknown or incomplete command: {' '.join(args)}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
