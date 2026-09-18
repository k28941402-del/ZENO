# The ZENO Langflow flow

`zeno_flow.json` is the companion multi-agent flow: Orchestrator + four
sub-agents (Comms & Tasks, Web & Research, Files/Docs & Code, Memory &
Growth), each a Google Gemini-backed LangFlow Agent. Import it into Langflow
directly.

This version is a corrected copy of an earlier export. The corrections below
were found by inspecting the flow's actual JSON, not by re-describing what it
was supposed to do — the same discipline the rest of this repo uses.

## Bugs found and fixed

**1. All four sub-agents were indistinguishable to the Orchestrator.**
When each sub-agent is wired into the Orchestrator's `tools` input, Langflow
exposes it as a callable tool using the `tools_metadata` field. Every single
one of the four sub-agents had been left on the untouched default: the tool
name was `Call_Agent_message_response` / `Call_Agent_json_response` for all
four, and the description was the generic placeholder *"Define the agent's
instructions, then enter a task to complete using tools."* for all four. The
Orchestrator's system prompt confidently told it to call tools named
`comms_and_tasks`, `web_and_research`, etc. — names that didn't exist
anywhere in its actual tool schema. It had no reliable way to pick the right
sub-agent. Fixed: each sub-agent now has a unique `tools_metadata` name
(`Call_web_and_research_message_response`, etc.) and a role-specific
description, matching what the Orchestrator's prompt actually says.

**2. The Memory & Growth agent had no `# Role` section at all.**
Its system prompt jumped straight from the generic `# Identity` block to the
generic `# Safety` block — the paragraph that would have told it "you are
the Memory & Growth agent, here's your job" was simply missing. It had the
full safety/tone/tool-use scaffold but no actual task description. Fixed:
added the missing Role section.

**3. The Orchestrator's sub-agent list was stale.** It listed five
sub-agents — including `files_and_docs` and `system_and_code` as two
separate entries — from before those two were consolidated into one agent.
Fixed: the list now matches the real four-agent lineup, and explicitly says
"these are the ONLY four; do not address them by any other name."

**4. The Comms & Tasks agent had no explicit Gmail-send confirmation rule.**
It relied only on the generic shared safety text ("confirm before
externally-visible actions"), even though it has a live, connected Gmail
send tool. Fixed: added an explicit rule to show the full drafted email and
wait for confirmation before every send, with "one approval = one send."

**5. Session ID was blank on Chat Input, Message History, and Chat Output.**
This is the cross-session-memory gap that had been flagged as outstanding —
with all three blank, the Memory (Retrieve mode) component had no reliable
shared key to filter on across turns. Fixed: all three now share the
explicit value `zeno-primary-session`.

**Known follow-up, not fixed here:** `zeno-primary-session` is a hardcoded
single-user value. For a real multi-user deployment, pass `session_id` as a
runtime parameter through the Langflow API instead (each conversation gets
its own value) rather than hardcoding one in the flow file.

## Model lineup

Every agent currently runs on Google Gemini (`gemini-3.5-flash-lite` through
`gemini-3.8-flash`, varying by agent). Earlier design notes for this project
called for local Ollama-served models instead. Whether to move back to local
models is a cost/privacy/latency tradeoff for you to make — nothing about
the fixes above depends on which provider is used, and the same
`tools_metadata` fix pattern applies regardless of model backend.

## Relationship to the Python skeleton

This flow is complementary to, not merged with, the `zeno/` Python package
in this repo. See `ARCHITECTURE.md` for the intended integration point
(`CoreLoop`'s pluggable `planner`).
