# Adding an agent

The core has no dependency on a client. A compatible client needs a persistent
Markdown instruction mechanism, Agent Skills (or an equivalent file bundle),
MCP stdio support, shell/CLI execution and permission to operate a local browser.
If a capability is missing, report it; do not claim equivalent support.

Add `adapters/<client>/adapter.py` implementing `NAME`, `CLI`, `paths(home)`,
`configure(context)` and `validate(context)`. Register its name in the installer
argument parser and detection list. Keep syntax and path knowledge in that adapter.
Add a small orchestration.md only for client-specific behavior.

| Core | Adapter mapping |
| --- | --- |
| skills/* | Six native user-level skills using hash-managed copies |
| instructions/GLOBAL.md | Generated marked block in global instructions |
| Serena | Independent user-scope MCP entry using a supported context |
| Serena hooks | Opt-in; only supported events and payloads |
| agent-browser | browser-qa skill plus shared CLI on PATH |
| External knowledge | Shared private sources; bounded lookup/reference pointers |

Use the context's backup, block, JSON, hook and skill helpers. Add preservation,
repeat-install and uninstall tests. Do not duplicate the canonical DESIGN.md or
invent universal MCP/hook syntax. Never import another client's account config.
