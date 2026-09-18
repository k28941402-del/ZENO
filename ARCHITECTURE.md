# Architecture

## Design principle

Every layer is small enough to read in one sitting, and every claim of
capability is backed by a test. This project would rather have 13 tools that
definitely work than 100 that might.

## The core loop

```
 input
   │
   ▼
1. PERCEIVE        capture raw input for this turn
   │
   ▼
2. CONTEXTUALIZE   pull relevant memory into working layer
   │
   ▼
3. PLAN            decide intent + tool + args (pluggable planner)
   │
   ▼
4. PERMISSION CHECK   allow / confirm / deny (zeno/core/permissions.py)
   │
   ▼
5. EXECUTE         call the tool via the registry
   │
   ▼
6. REFLECT         write outcome to episodic memory
   │
   ▼
7. UPDATE GOALS    mark related goals active/done
   │
   ▼
8. RESPOND         structured result back to the caller
```

Every stage publishes an event (`stage.perceive`, `stage.plan`, ...) on the
`EventBus` before running. Nothing subscribes by default in the library
itself — the CLI, a future logger, or a future UI can hook in without the
loop needing to change.

## Memory: seven layers, two lifetimes

| Layer | Lifetime | Backing |
|---|---|---|
| working | cleared every turn | in-memory dict |
| session | cleared on `new_session()` | in-memory dict |
| episodic | persistent | SQLite |
| semantic | persistent | SQLite |
| procedural | persistent | SQLite |
| reflective | persistent | SQLite |
| identity | persistent | SQLite |

All five persistent layers share one `SQLiteStore` (`zeno/memory/store.py`) —
a single table namespaced by layer. There is no embedding search here yet;
retrieval is exact key lookup. That's a real limitation, not a hidden one —
it's called out in the README and roadmap.

## Permissions

Three-tier policy per tool: `ALLOW`, `CONFIRM`, `DENY`. The engine itself
never invents a "yes" — `CONFIRM` only proceeds if the caller explicitly
passes `confirmed=True`, which in the CLI means a human typed something.
This is the same shape of guardrail used in the companion Langflow flow's
"confirm-before-send" rule on the Comms & Tasks agent.

## Routing: Supervisor + sub-agents

`zeno/core/supervisor.py` structures the planner as a Supervisor delegating
to small per-domain sub-agent functions (`notes_agent`, `projects_agent`,
`system_agent`, `web_agent`, `briefing_agent`), each a pure function
`(text, memory) -> PlannedAction | None`. The Supervisor tries them in order
and returns the first match. It implements the same `PlannerFn` interface as
the simpler default planner in `core/loop.py` — it's a drop-in replacement,
not a separate system — and is what `zeno/cli.py` wires in by default.

This mirrors the "Orchestrator + sub-agents" structure of the companion
Langflow flow (`langflow/zeno_flow.json`) at the code level: same idea of a
router delegating to domain specialists, same emphasis on each specialist
being independently identifiable and testable. In the Langflow flow, making
each sub-agent actually distinguishable to the Orchestrator (unique tool
name + description) was one of the concrete bugs fixed — see
`langflow/README.md`. The Python Supervisor doesn't have that failure mode
because sub-agents are plain Python functions with real names, not
LLM-exposed tools with generatable metadata that can silently collide.

## Tool registry: the honesty mechanism

This is the part that exists specifically because of a prior project's
mistake. Every tool is registered with a `ToolStatus` of `IMPLEMENTED` or
`STUB`. `CAPABILITIES.md` is generated from this registry
(`scripts/gen_capabilities.py`) and CI fails if the committed file doesn't
match what the code currently registers. There is no path for the docs to
say more than the code does.

## Relationship to the Langflow multi-agent flow

This repo is the ZENO *runtime skeleton* — the parts you'd want regardless
of which LLM or orchestration layer sits on top. The companion Langflow
flow (Orchestrator + Files/Docs/Code + Comms & Tasks + Web & Research +
Memory & Growth, four sub-agents) is a separate, complementary piece: it's
where multi-model routing, Composio-based Gmail/Calendar integration, and
LLM-driven planning live.

The intended integration point is `CoreLoop`'s `planner` argument
(`zeno/core/loop.py`): the default is a small rule-based matcher, but it's a
pluggable `PlannerFn`, so a real integration would swap in a function that
calls the Langflow Orchestrator (or any LLM) to produce a `PlannedAction`,
instead of keyword matching. That swap is listed on the roadmap rather than
implemented here, because it needs the Langflow flow's Session ID wiring
finished first (also on the roadmap) to be worth doing properly.

## Delegation — "handle it for me"

`zeno/core/delegate.py`'s `Delegator` is the part that actually earns the
JARVIS comparison: `delegate("...")` queues a task on the GoalEngine without
running it, and `run_next()` / `run_all_pending()` attempt it using the same
Supervisor routing as normal input. Three outcomes, all honestly reported:

1. **Handled** — a real tool existed, permission allowed it, it ran. Goal marked DONE.
2. **No automatic path yet** — nothing in the tool registry matches. Goal stays PENDING, and the result says so explicitly rather than fabricating a completion.
3. **Needs your confirmation** — the matched tool requires human sign-off (`PermissionEngine.CONFIRM`) and none was given. Goal stays PENDING. Delegation is deliberately never allowed to auto-confirm on your behalf — "handle it" and "you're pre-approved to send/delete/etc." are kept as two separate, explicit steps.

`run_all_pending` won't let one unsolvable goal block the rest of the queue — it skips a goal for that pass after one failed attempt rather than retrying it forever, so other queued tasks still get a chance. Try it from the CLI: `delegate: <task>`, then `run pending`.

## What's deliberately not built yet

Voice I/O, screen/vision, desktop device control, and always-on ambient
sensing are registered as stubs (`zeno/tools/__init__.py`) rather than left
out entirely, so their intended interface is visible, importable, and
testable — but calling any of them raises `NotImplementedError`. See
`CAPABILITIES.md` for the live, generated status of every tool.

Note: `sensing.ambient`'s stub status is unaffected by the Godseye
companion app (`godseye/`) — Godseye is a real, working, separately-run
visualization layer, but it's not a Python-backend sensing pipeline the
tool registry can claim credit for. See `godseye/INTEGRATION.md` for
exactly what it does and doesn't provide.
