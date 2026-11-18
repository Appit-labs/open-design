# open-design

<h3 align="center">The OpenDesign monorepo, including the pnpm trap that eats the first hour.</h3>

<p align="center">
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-MIT-3DA639?style=flat-square"></a>
  <img alt="agents" src="https://img.shields.io/badge/works%20in-pi%20%7C%20Claude%20Code%20%7C%20Codex%20%7C%20Cursor-4B5563?style=flat-square">
  <img alt="skillspector" src="https://img.shields.io/badge/SkillSpector-0%2F100%20SAFE-2EA043?style=flat-square">
  <img alt="cost" src="https://img.shields.io/badge/session%20cost-~102%20tok-6E7681?style=flat-square">
</p>

<p align="center">
  <img alt="open-design demo — real run, regenerable from demos/open-design.json" src="skills/open-design/assets/demo.gif" width="900">
</p>

## What it is

`open-design` is a **short, verified guide to working in `nexu-io/open-design`**: which pnpm the
repo pins and how to actually run it, the `tools-dev` lifecycle (there is no root `pnpm dev`), ports, how
to take a desktop screenshot through the tool, and which checks a pull request must pass.

## The problem it removes

The repo's own `AGENTS.md` is ~57 KB, and the first hour usually disappears into a
corepack/pnpm version conflict or into inventing a dev command that does not exist.

## Install

```bash
# Claude Code — the whole collection as one marketplace
claude plugin marketplace add Appit-labs/appit-skills
claude plugin install open-design@appit-skills

# pi
pi install git:github.com/Appit-labs/open-design

# any agent that reads a skills directory
git clone git@github.com:Appit-labs/open-design.git
cp -r open-design/skills/open-design ~/.claude/skills/      # or ~/.codex/skills/, .cursor/skills/, …
```

## Use

- **Health** — `scripts/od.py doctor` — node, pnpm, ports, repo
- **Start** — `scripts/od.py start --web-port 17573`
- **Screenshot** — `scripts/od.py shot /tmp/od.png`
- **Pre-PR** — `scripts/od.py checks`

## What it does not do

- It does not duplicate `AGENTS.md`; it points at the sections you need by heading.
- It does not install the repo for you beyond `corepack pnpm install`.

## Requires

- Node `~24` (pinned in `.node-version`).
- pnpm **10.33.2** via Corepack — a global pnpm 11 shadows it and breaks `tools-dev`.
- Docker only for containerized packing.

## Cost

| | tokens |
| --- | --- |
| always-on — the description, paid every session | ~102 |
| on invoke | ~1k |

The demo above is not a mockup: `demos/open-design.json` holds the captured run and
`tools/make_demo.py` renders it, so it can be regenerated and audited.

## Provenance

Every command in this skill was run against a real target before it was written down: a live
database, a staging host, a failing CI run, a browser session. The repository was created and
published on 2026-11-18; where the workflow itself is older, `CHANGELOG.md` carries the dates.

## Security

SkillSpector: **0/100, SAFE, 0 open findings** against the committed baseline. Every accepted
finding is listed with its reason in [SECURITY.md](SECURITY.md). No `shell=True`, no credential
storage, no network destination chosen at runtime.

## Part of the Appit collection

[appit-skills](https://github.com/Appit-labs/appit-skills) — browser QA · CI triage · Postgres · runbooks ·
SSH · Trello · cloud browsers · OpenDesign · Blender.

## License

MIT, copyright Appit Labs. See [LICENSE](LICENSE).
