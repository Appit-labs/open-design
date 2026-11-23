---
name: open-design
description: Work inside the OpenDesign repo (nexu-io/open-design) — install once with the pinned pnpm, start the local daemon+web through tools-dev instead of a root dev script, run the desktop/web QA loop with screenshots, and pass the pre-PR checks. Use when a task touches the OpenDesign monorepo, its daemon/web apps, design systems, plugins or skills, or when `pnpm`, `corepack`, or port conflicts block local start.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
permissions:
  - shell
  - env
license: MIT
---

# OpenDesign monorepo

`nexu-io/open-design` (Apache-2.0): a design-agent workspace — `apps/daemon`,
`apps/web`, `apps/desktop`, plus `packages/*`, `skills/`, `plugins/`,
`design-systems/`, `design-templates/`, `e2e/`, `scripts/`.

Its own `AGENTS.md` is ~57 KB. Do not read it whole. Read the section you need by
heading (`grep -n "^#\\{1,2\\} " AGENTS.md`, then `sed -n 'START,ENDp'`), and use
this skill for the parts that break in practice.

```
python3 "$SKILL_DIR/scripts/od.py" doctor|start|status|shot|stop|checks
```

**Not for:** any other pnpm monorepo — the pins, ports and `tools-dev` lifecycle here are OpenDesign-specific and will not transfer.

## Portability

Works in any agent that can run shell commands (pi, Claude Code, Codex, Cursor,
Gemini CLI, …): the instructions are plain Markdown and the helper is a stdlib
script. Commands use `$SKILL_DIR` for this skill's own directory — the folder that
holds this `SKILL.md`. Set it once per session, for example:

```bash
SKILL_DIR=~/.claude/skills/open-design     # or ~/.codex/skills/…, ~/.pi/agent/skills/…, .cursor/skills/…
```

## No MCP needed here

This repo is a pnpm workspace driven by `tools-dev`; nothing in this workflow goes through an
MCP server. If an agent asks for `mcp__*` tools to touch OpenDesign, that is a wrong turn — use
the CLI below.

## Prerequisites

- **Node `~24`.** `package.json#engines` and `.node-version` pin it; Node 22 is
  unsupported (lockfile pins `better-sqlite3@11.10.0`). Check with `node -v`.
- **pnpm 10.33.2 via Corepack**, matching `packageManager` in `package.json`.
  A global pnpm 11 on PATH will shadow it and produce confusing `tools-dev`
  failures — the most common way a session loses an hour here.
- `pnpm install` at the repo root once, after any manifest/workspace change.
- Docker is optional (sidecar/containerized packing), not needed for web QA.

## The pnpm trap (read this first)

`corepack` downloads the pinned pnpm on first use. If `pnpm -v` does not print
`10.33.2`, you are running someone else's pnpm. Use the pinned one explicitly:

```bash
corepack pnpm -v                       # must print 10.33.2
corepack pnpm install
corepack pnpm exec tools-dev run web --daemon-port 17456 --web-port 17573
```

Escape hatches when Corepack itself misbehaves:
`pnpm --config.manage-package-manager-versions=false exec tools-dev …`, or
`npm i -g pnpm@10.33.2` (the documented Windows fallback, works on Linux too).

## Lifecycle rules

- `pnpm tools-dev` is the **only** local lifecycle entry point. There is no root
  `pnpm dev`, `pnpm start`, `pnpm daemon`, or `pnpm preview` — do not add or
  restore them, and do not invent your own `apps/web` start command.
- Ports come from `--daemon-port` / `--web-port` only. `tools-dev` exports
  `OD_PORT` (web proxy target) and `OD_WEB_PORT` (web listener); `NEXT_PORT` is
  not used.
- `apps/nextjs` no longer exists; the web runtime is `apps/web`. Do not restore it.
- State: `pnpm tools-dev status --json`, `logs --json`, `stop`, `check`.

## QA loop

Desktop screenshots through the tool instead of a browser when you are testing the
packaged shell:

```bash
corepack pnpm exec tools-dev inspect desktop status --json
corepack pnpm exec tools-dev inspect desktop screenshot --path /tmp/od.png
```

For the web app, start it, then drive a real browser: `open http://127.0.0.1:17573`,
`snapshot -i`, act on refs, screenshot per step. Pair with the `live-qa` skill when
the run needs a pass/fail table; this skill only gets the app running.

## Before you open a PR

```
python3 "$SKILL_DIR/scripts/od.py" checks
```

Runs `pnpm guard` + `pnpm typecheck`, and lists the violation. Beyond that, the
repo's rule is **focused tests only** — run the tests for the files you changed
(`pnpm --filter @open-design/web test`), not the full daemon/web suites; full
suites are PR CI's job. Two non-obvious gates:

- New code is TypeScript; residual JS is allowlisted in `scripts/guard.ts`.
- Work that touches design systems, plugin previews, or fixtures has a dedicated
  `scripts/check-*` — run the one matching your change (they are all named after
  what they check) rather than guessing.

## Reporting back

Name the app you touched (`web`, `daemon`, `desktop`, `tools-dev`), the ports you
used, and the checks you actually ran with their result. "Ran focused tests for
`apps/web`" is useless without the exit status.
