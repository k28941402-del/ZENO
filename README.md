# ZENO

*A local-first personal intelligence agent — built like it has to survive contact with an actual user, not just a demo.*

![CI](https://github.com/YOUR_USERNAME/zeno/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Why this README is written the way it is

A previous assistant project of mine ("Nova") shipped with a README that described a lot more than the code actually did. It *behaved* like a normal assistant, but couldn't reliably do the specific tasks it was supposed to be built for — because the gap between "documented" and "implemented" was invisible until you hit it.

ZENO is built to make that gap impossible to hide:

- Every tool is registered with an explicit status — `implemented` or `stub` — in [`zeno/tools/registry.py`](zeno/tools/registry.py).
- [`CAPABILITIES.md`](CAPABILITIES.md) is **generated from that live registry**, not hand-written. It cannot say a tool works if the code disagrees.
- CI re-generates it on every push and **fails the build** if the committed file is stale (`scripts/gen_capabilities.py --check`).
- A stub doesn't silently return a fake answer — calling one raises `NotImplementedError` on purpose.

If you clone this repo, `CAPABILITIES.md` is the actual, current, provable truth about what ZENO can do today. Nothing in this README overrides it.

## What ZENO is

ZENO is the always-on, proactive assistant idea — the "JARVIS / Ultron" concept of a system that perceives, remembers, decides, and acts on your behalf — built as an honest, incrementally-real engineering project instead of a costume worn over an API call.

**Core architecture:**

| Component | File | What it does |
|---|---|---|
| 8-stage core loop | `zeno/core/loop.py` | perceive → contextualize → plan → permission-check → execute → reflect → update-goals → respond |
| 7-layer memory | `zeno/memory/layers.py` | working, session (ephemeral) + episodic, semantic, procedural, reflective, identity (persisted in SQLite) |
| Permission engine | `zeno/core/permissions.py` | allow / confirm / deny per tool — nothing destructive runs without explicit confirmation |
| Goal engine | `zeno/core/goals.py` | priority-ordered standing goals, the seed of proactive behavior |
| Event bus | `zeno/core/events.py` | every loop stage publishes an event; nothing needs to know who's listening |
| Tool registry | `zeno/tools/registry.py` | the single source of truth for what's real |

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full design rationale and how this maps onto the Langflow multi-agent flow this project also uses.

## Quickstart

**Just want to use it? Download, don't clone.** Go to this repo's **Releases** page and download the file for your OS (`zeno-windows.exe`, `zeno-macos`, or `zeno-linux`) — no Python install required. Double-click it (on macOS/Linux: `chmod +x zeno-macos && ./zeno-macos` the first time) and it opens the ZENO console in your browser automatically at `http://127.0.0.1:8420`.

**Developing on it instead:**

```bash
git clone https://github.com/YOUR_USERNAME/zeno.git
cd zeno
pip install -e ".[dev,webui]"
pytest                     # 65 tests, all exercising real behavior
python scripts/gen_capabilities.py   # regenerate CAPABILITIES.md
zeno                       # terminal REPL
zeno-web                   # same thing, browser UI at http://127.0.0.1:8420
```

Inside the REPL (or the web console's command line):

```
zeno> tools
zeno> note: pick up the CI badge URL once this repo is public
zeno> system status
zeno> delegate: search: current mars weather
zeno> pending
zeno> run pending
```

That last block is the "hand it off" pattern: `delegate:` queues something
without running it yet, `pending` shows what's queued, `run pending` has
ZENO actually attempt everything — using only tools that genuinely exist,
and telling you plainly if something has no automatic path yet rather than
faking a result. See [`ARCHITECTURE.md`](ARCHITECTURE.md#delegation--handle-it-for-me).

## The web console

`zeno-web` (or the downloaded standalone build) serves a single-page console at `http://127.0.0.1:8420` — a tool registry panel, a command log, a delegation queue, and a Godseye panel, all backed by the exact same objects the CLI uses (`zeno/webui.py`). Nothing in the UI is mocked; the registry counts, tool list, and turn results all come from live calls into `zeno/core` and `zeno/tools`.

## Godseye — the live 3D-globe companion

[`godseye/`](godseye/) vendors [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view) by Bilawal Sidhu (MIT license, attribution preserved in `godseye/LICENSE`) — a real-time console of live aircraft, ships, satellites, earthquakes, and public CCTV on a 3D globe. It's a separate Node/Vite app, not something the Python backend implements. ZENO's web console detects whether it's running (a real reachability check, `GET /api/godseye/status` — no fake "connected" state) and either links straight to it or shows the exact setup steps. See [`godseye/INTEGRATION.md`](godseye/INTEGRATION.md).

## Cutting a release (maintainers)

Push a version tag and GitHub Actions builds and attaches standalone executables for Windows, macOS, and Linux automatically:

```bash
git tag v0.1.0
git push origin v0.1.0
```

See [`.github/workflows/release.yml`](.github/workflows/release.yml) — it runs the full test suite before packaging, so a tagged release can't ship from a broken commit.

## Current capabilities (short version)

Real today: notes, reminders, projects (full CRUD, persisted), live weather lookup, DuckDuckGo instant-answer search, local system-status reporting with threshold alerting, morning-briefing assembly, idle check-in detection, PDF and PPTX generation. Routing is handled by a Supervisor (`zeno/core/supervisor.py`) that delegates to small per-domain rule-based sub-agents — same honest rule-based approach as the default planner, just structured so each domain is independently testable.

Declared but not built yet: voice I/O, screen/vision, desktop device control, always-on ambient sensing. These are registered as stubs on purpose — see [`CAPABILITIES.md`](CAPABILITIES.md) for the full, current, generated table. Voice specifically needs real audio hardware to test against, which this development sandbox doesn't have; the interface is defined so a real implementation can be dropped in and verified on a machine that does.

## The companion Langflow flow

[`langflow/zeno_flow.json`](langflow/zeno_flow.json) is a multi-agent Orchestrator + 4-sub-agent flow (Comms & Tasks, Web & Research, Files/Docs & Code, Memory & Growth) for Langflow. It's a corrected version of an earlier export — see [`langflow/README.md`](langflow/README.md) for the specific bugs that were found (including all four sub-agents being indistinguishable to the Orchestrator at the tool-schema level) and fixed.

## Known limitations

- The default planner is a small rule-based keyword matcher, not an LLM. It is genuinely functional for the phrasings it recognizes and honestly unhelpful outside them — see `zeno/core/loop.py::default_rule_based_planner`. Swapping in an LLM-backed planner (e.g. via the companion Langflow flow) is the natural next step; the `PlannerFn` interface is built for that.
- Reminder due-times are naive datetimes (no timezone normalization yet).
- Memory retrieval is exact key lookup, not embedding/semantic search.
- No voice, vision, or OS-level control — see the stub list above.

## Roadmap

- [x] Session ID plumbing for the companion Langflow flow's Message History memory
- [x] Structured multi-domain routing (Supervisor pattern)
- [x] Task delegation / offloading (Delegator + GoalEngine)
- [x] Browser-based console (Flask + vanilla JS) and standalone downloadable builds
- [ ] Timezone-aware reminders
- [ ] LLM-backed planner (pluggable `PlannerFn`, wired to the Langflow orchestrator)
- [ ] Scheduled/proactive runs — `proactive.check_idle` and `proactive.morning_briefing` exist as real functions; wiring them to an actual OS-level scheduler/timer loop is still open
- [ ] Voice I/O (needs real audio hardware to implement and test against)
- [ ] Desktop/device control
- [ ] Vector-backed semantic memory search

## Contributing

Before adding a tool: register it with `status=ToolStatus.STUB` first if it isn't done, run `python scripts/gen_capabilities.py`, and commit the regenerated `CAPABILITIES.md` alongside your code. CI checks that the file matches the registry — it will fail your PR if it's out of sync.

## License

MIT — see [`LICENSE`](LICENSE).
