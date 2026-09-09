# Upstream conventions checked 2026-09-06

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
