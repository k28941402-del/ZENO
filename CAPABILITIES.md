# ZENO — Capability Matrix

**This file is generated from the live tool registry. Do not hand-edit it —
run `python scripts/gen_capabilities.py` instead.** CI fails if this file is
out of date with the code, so it cannot silently drift from what actually
works.


**17 implemented, 5 stub.**

| Tool | Status | Description |
|---|---|---|
| `device.control` | 🚧 stub (raises `NotImplementedError`) | Control desktop/OS-level actions (open apps, files). |
| `docgen.pdf` | ✅ implemented | Generate a PDF from a title and a list of (heading, body) sections. |
| `docgen.pptx` | ✅ implemented | Generate a PPTX from a title and a list of (slide_title, body) slides. |
| `notes.create` | ✅ implemented | Create a note with a title and optional body. |
| `notes.delete` | ✅ implemented | Delete a note by id. |
| `notes.list` | ✅ implemented | List all stored notes. |
| `proactive.check_idle` | ✅ implemented | Pure time check: has enough idle time passed to justify a check-in? |
| `proactive.morning_briefing` | ✅ implemented | Assemble due reminders (and optional weather, if lat/lon given) into a briefing. |
| `projects.create` | ✅ implemented | Create a project with a name and optional description. |
| `projects.list` | ✅ implemented | List projects, optionally filtered by status. |
| `projects.set_status` | ✅ implemented | Set a project's status to active, paused, or done. |
| `reminders.complete` | ✅ implemented | Mark a reminder as done by id. |
| `reminders.create` | ✅ implemented | Create a reminder with text and an ISO-8601 due timestamp. |
| `reminders.list_due` | ✅ implemented | List reminders due at or before a given time (defaults to now). |
| `sensing.ambient` | 🚧 stub (raises `NotImplementedError`) | Always-on environmental/world sensing. |
| `system.check_thresholds` | ✅ implemented | Given a status dict, return alert strings for anything over threshold. |
| `system.status` | ✅ implemented | Report local CPU, memory, and disk usage. |
| `vision.screen` | 🚧 stub (raises `NotImplementedError`) | Read and reason about the current screen contents. |
| `voice.listen` | 🚧 stub (raises `NotImplementedError`) | Real-time voice input via microphone. |
| `voice.speak` | 🚧 stub (raises `NotImplementedError`) | Text-to-speech output. |
| `weather.current` | ✅ implemented | Fetch current weather for a lat/lon via the Open-Meteo API. |
| `web_search.answer` | ✅ implemented | Query DuckDuckGo's Instant Answer API for a fact/definition (not a full search-results list). |

A **stub** is registered so its intended name/shape is visible and importable, but calling it raises `NotImplementedError` on purpose — it does not silently pretend to succeed.
