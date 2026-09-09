# Designer agent stack

A portable agent stack for Codex and Claude Code, built to help generate better
design output and use tokens more efficiently during frontend work. It combines
design guidance, focused skills and shared tools in one user-level installation.
The package repository is the source of truth; local configuration is an installation.

## Why this stack

Better design starts with deliberate choices about hierarchy, typography, spacing,
composition and interaction. This stack gives agents a shared design profile to
guide those choices, while respecting each project's identity, components and
design tokens. It encourages purposeful motion, accessible states and responsive
layouts, with human feedback for subjective visual decisions.

Token efficiency comes from keeping the working context focused:

- Load only the skills relevant to the task; keep full upstream reference bundles
  outside global skill discovery.
- Retrieve specific symbols, files and reference rules when needed, and reuse
  findings instead of repeatedly scanning the repository.
- Use targeted checks and semantic browser inspection, with automated vision and
  extra agents reserved for cases where they add value.
- Stop once the requested work and meaningful checks are complete.

The aim is more intentional interfaces with less unnecessary context and repeated
work. These are workflow goals, not measured guarantees of design quality or token
savings; results depend on the task, model and project.

## Install

Requires Git, internet access, and an installed supported client for automatic
detection. The installer bootstraps uv and Python 3.13, and installs a private
Node LTS if usable Node 24+ and npm are missing. No administrator access is needed.
Linux needs the standard shared libraries required by Chrome; missing system
libraries are reported, not installed through an unattended sudo command.

macOS / Linux:

```sh
git clone https://github.com/CaptExcellent/designer-agent-stack.git
cd designer-agent-stack
./scripts/install.sh
```

Windows (PowerShell 5.1+ or PowerShell 7):

```powershell
git clone https://github.com/CaptExcellent/designer-agent-stack.git
cd designer-agent-stack
.\scripts\install.ps1
```

If your PowerShell policy blocks a downloaded script, review the repository and
run it with `powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1`.
This changes policy only for that process. The installer never changes policy.

Install for one agent:

| Client | macOS / Linux | Windows |
| --- | --- | --- |
| Codex | `./scripts/install.sh --agent codex` | `.\scripts\install.ps1 -Agent codex` |
| Claude Code | `./scripts/install.sh --agent claude-code` | `.\scripts\install.ps1 -Agent claude-code` |
| Both | `./scripts/install.sh --all` | `.\scripts\install.ps1 -All` |

Explicit selection can prepare configuration for a future client. Doctor reports
the client as missing until you install it; the stack never purchases or configures
an agent account. Restart clients and terminals after installation. In Codex,
check `/mcp` for Serena; review `/hooks` only if you opt into hooks.

## What gets installed

Six small, discoverable modules:

1. `design`: personal composition and judgment, with a shared UI UX Pro Max lookup only when needed.
2. `motion`: purposeful animation opportunities, implementation and review.
3. `frontend-quality`: React and component guidance; targeted upstream rules on demand.
4. `engineering-quality`: repository-aware implementation, review and debugging.
5. `task-planning`: concise high-value clarification, goals and bounded task execution.
6. `browser-qa`: semantic inspection first; human feedback for subjective appearance.

Serena MCP and agent-browser CLI are shared tools. Full upstream instruction
bundles stay outside global skill discovery. Vision and parallel agents default
to zero; escalate only when useful and allowed. No account or billing changes.
Serena's dashboard and GUI log window stay closed; semantic tools remain available
in the background when a client starts the MCP integration.

Serena hooks and Vercel Optimize are **opt-in**. Use `--serena-hooks` or
`--with-vercel` on POSIX; `-SerenaHooks` or `-WithVercel` on Windows. Choices persist.
To disable, use `--no-serena-hooks` / `--no-with-vercel` or `-NoSerenaHooks` /
`-NoVercel`. Disabling removes only unchanged package-owned integrations; shared
runtimes remain. Existing unrelated hooks and skills are never removed.

Use `agent-stack reference react waterfall` or
`agent-stack reference composition context` to obtain at most eight file pointers.
Read only the relevant rule. Optional production analysis uses
`agent-stack reference optimize` after opting in.

## Update, doctor and uninstall

| Operation | macOS / Linux | Windows |
| --- | --- | --- |
| Update dependencies and skills | `./scripts/install.sh --update` | `.\scripts\install.ps1 -Update` |
| Diagnostic only | `./scripts/doctor.sh` | `.\scripts\doctor.ps1` |
| Read-only installation plan | `./scripts/install.sh --dry-run` | `.\scripts\install.ps1 -DryRun` |
| Remove integrations | `./scripts/uninstall.sh` | `.\scripts\uninstall.ps1` |

Use `git pull --ff-only` to update this package's installer and canonical files
before running the update command. Local repository changes are never discarded.
Ordinary reinstall reuses cached sources. Only explicit update refreshes upstream sources.
Dry-run and doctor require the bootstrap runtime to exist; they never install it.

Installations record resolved npm versions and skill source commit IDs in a local
manifest. Current supported releases are preferred. A clean clone plus installation
reproduces the workflow; this is not an offline mirror of all upstream dependencies.

Uninstall removes only unchanged owned skills, marked instruction/MCP blocks,
exact owned JSON entries/hooks, and PATH entries added by the package. User edits
are preserved with warnings. It keeps runtimes, downloaded tools, browser caches,
backups and the manifest, since other software may now depend on them. It never
restores backups automatically. These private runtime files are outside the repo.

## How it works

```text
request + project instructions / DESIGN.md
  -> infer safe defaults; ask only high-value unresolved questions
  -> design judgment; database lookup only for a knowledge gap
  -> narrow context (Serena when useful)
  -> relevant implementation / motion / engineering guidance
  -> targeted tests and semantic browser inspection
  -> human visual feedback by default; focused vision only when justified
  -> targeted fix, verify, stop

requested Vercel production analysis -> Vercel Optimize + actual metrics
```

Project DESIGN.md defines the actual product identity and tokens. The personal
DESIGN.md judges hierarchy, restraint, composition, density and character. Project
constraints and explicit requests win. Google DESIGN.md token semantics are
preserved. No project DESIGN.md is required or generated automatically.

Optional project linting (only when relevant):

```sh
npx --yes --package=@google/design.md designmd lint DESIGN.md
```

The `designmd` alias avoids Windows `.md` file-association problems. Google's
format is still alpha; this is an optional tool, not an installation requirement.

## Ownership and locations

One canonical personal profile lives in `skills/design/DESIGN.md`. All six skills
use hash-tracked managed copies so generated local lookup paths cannot modify the
portable source. Edit repository sources and reinstall. Edited installed copies
cause a conflict. Version 2 retires only unchanged, package-owned v1 skill folders,
with backups; the original personal documents remain in Git history.

| Location | Purpose |
| --- | --- |
| `~/.local/share/sjoerd-agent-stack` | Private tools, sources, manifest and timestamped backups |
| `~/.agents/skills` | Codex user skills |
| `$CODEX_HOME/AGENTS.md`, `config.toml`, `hooks.json` | Codex adapter; defaults to `~/.codex` |
| `~/.claude/skills`, `CLAUDE.md`, `settings.json` | Claude skill, instruction and hook adapter |
| `~/.claude.json` | Claude user-scope MCP entry; unrelated fields preserved |

`SJOERD_STACK_HOME` can relocate package state. Its legacy name is retained so
existing installations remain updateable. `CLAUDE_CONFIG_DIR` is respected,
including its `.claude.json`. Home directories are discovered at runtime. Windows
user PATH is merged and backed up; POSIX shell profiles receive marked source
lines for a managed env.sh. No existing Node/Python installation is replaced.
Backups can contain existing private configuration: never commit the state folder.

## Compatibility and limits

- Shared skill content and design decisions are identical across adapters.
- MCP context, global instruction locations and hook schemas are client-specific.
- Serena's Claude context is single-project when started in a repository; project
  activation occurs at startup and `activate_project` is then unavailable. Codex
  can activate explicitly, which matters when its desktop launch cwd differs.
- Released Serena 1.7.0 lacks the website's `reset` command. The Codex adapter
  capability-checks it and omits that PostToolUse hook until supported.
- Codex hooks require `/hooks` trust review. Doctor validates definitions and
  enablement, not persisted runtime trust. Explicit hook disables are preserved.
- Claude auto-approval hooks and system-prompt replacement are deliberately not
  installed. Neither is required for MCP operation.
- Browser use is subject to the active client's permissions. A client policy can
  require a different browser tool; that limitation must be reported.
- Windows x64 is the first live installation. Automated preservation tests run on
  Windows, macOS and Linux in CI; authenticated Claude behavior requires a Claude
  installation. Cross-platform CI is not proof of every machine's browser libraries.

## Package layout

```text
skills/                    six modules; design/DESIGN.md is canonical
instructions/GLOBAL.md     neutral workflow
adapters/                  codex, claude-code, generic guide
scripts/                   shell/PowerShell launchers + portable manager
config/tools.json          upstream tools and sources
tests/                     preservation tests + real smoke probes/prompt
docs/                      upstream sources and architecture
VERSION, LICENSE           version and license
```

## Adding another agent

Map skills, global Markdown, MCP and lifecycle hooks through one small adapter.
Keep core content unchanged. See [the adapter contract](adapters/generic/README.md).
See [upstream references](docs/SOURCES.md) for the conventions used here.

## Development checks

```sh
python -m unittest discover -s tests -v
python scripts/stack.py install --all --dry-run
```

The tests use temporary home directories and never modify real agent config.
The real Serena probe uses the MCP SDK already installed in Serena's uv tool
environment. Personal practice projects, galleries and run reports stay local.
