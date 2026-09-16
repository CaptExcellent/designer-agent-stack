# Upstream conventions checked 2026-09-06

Headroom integration checked 2026-09-16:

- [Headroom 0.37.0](https://github.com/headroomlabs-ai/headroom/tree/v0.37.0): separate proxy and `mcp serve` entry points; cache mode and workspace/config isolation. The stack does not call the upstream installer, wrappers or cleanup routines.
- [Codex config reference](https://learn.chatgpt.com/docs/config-file/config-reference): session `-c` overrides, built-in `openai_base_url` and additive MCP server configuration.
- [Claude CLI reference](https://code.claude.com/docs/en/cli-reference): session `--settings` and additive `--mcp-config`; no strict MCP replacement.
- [Licensing](THIRD_PARTY.md): upstream license, notices and model boundaries.

Integration validation on macOS: 32 unit tests passed; isolated installation of
Headroom 0.37.0; live proxy health/readiness; MCP discovery, synthetic compression
and exact original retrieval; real Codex CLI accepted additive session MCP
configuration while preserving the existing Serena entry. The optional Kompress
model reported not ready during this smoke test, so full ML compression was not
validated. No authenticated model requests, billing comparison, desktop routing
or live Windows/Linux sessions were tested.

- [Codex skills](https://learn.chatgpt.com/docs/build-skills): user skills at `~/.agents/skills`; duplicate names are not merged.
- [Codex instructions](https://developers.openai.com/codex/guides/agents-md): global `AGENTS.md` under CODEX_HOME, with repository precedence.
- [Codex hooks](https://learn.chatgpt.com/docs/hooks): hooks.json, enabled by default, exact-definition trust review through `/hooks`. `hooks` is canonical; `codex_hooks` is a deprecated alias.
- [Serena installation](https://oraios.github.io/serena/02-usage/010_installation.html): `uv tool install -p 3.13 serena-agent`.
- [Serena clients](https://oraios.github.io/serena/02-usage/030_clients.html): client contexts, project-from-cwd, reminder and lifecycle hooks. Hooks are alpha upstream.
- [Claude settings](https://code.claude.com/docs/en/settings), [MCP](https://code.claude.com/docs/en/mcp), [skills](https://code.claude.com/docs/en/skills): independent instructions, skills, user MCP and hooks.
- [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill): current CLI `ui-ux-pro-max-cli`, `uipro init --ai universal`. Generated in staging before safe distribution to native skill locations.
- [Vercel skills](https://github.com/vercel-labs/agent-skills): manual skill-directory installation is supported. Skill names differ from source folder names.
- [agent-browser](https://github.com/vercel-labs/agent-browser): npm global CLI, browser download and semantic snapshots.
- [Google DESIGN.md](https://github.com/google-labs-code/design.md): optional lint CLI; alpha format. Windows should use the `designmd` bin alias to avoid `.md` file association issues.
- [uv installer](https://docs.astral.sh/uv/getting-started/installation/), [Node distributions](https://nodejs.org/dist/): official runtime sources.

Serena's optional Claude auto-approval hook and system-prompt replacement are not
installed. They change permissions or replace too much client behavior for this
small adapter. Reminder/activation/cleanup hooks are included. Codex's current
default hook enablement is used, preserving an explicit user disable.
