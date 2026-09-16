# Version 2 decisions

The six functional modules replace the v1 bundle. Global routing is 1,315
characters, down from 2,270 (42%). Individual skill files contain 1,603–2,659
characters, roughly 400–665 tokens at four characters per token. The personal
profile is 5,202 characters and loads only for meaningful visual decisions.
These are text-size estimates, not measured model billing or quality gains.

| Source/capability | Decision | Reason and cost boundary |
| --- | --- | --- |
| Personal design profile | Internalize structure, preserve intent | One deeper profile, loaded through design; products keep distinct identities |
| UI UX Pro Max | Adapt | Retain executable database search; no mandatory initial query or huge global skill |
| Serena | Keep MCP; optional hooks | Semantic retrieval when cheaper; no reminder on every shell call by default |
| React + composition references | Internalize common rules, retain targeted reference files | One small module; rule paths returned on demand, not whole collections |
| agent-browser | Keep CLI, replace instruction bundle | One semantic QA module; human subjective judgment, zero default vision |
| Vercel Optimize | Optional | Actual authenticated production analysis only; no routine install or QA trigger |
| Headroom | Optional, pinned, session launcher | Compress tool results in cache mode; preserve retrieval; no overlapping hooks, memory or Serena installation |
| AI Hero workflow skills | Internalize selected ideas | Tight bug signals, compact context pointers and handoffs; reject compulsory workflow chains/review agents |
| Emil motion skills | Merge concepts into motion modes | Purpose, interruption and reduced motion; reject overlapping skills and universal timing rules |
| Taste Skill | Research only | Infer a small creative brief; reject large prompt and fixed aesthetic/motion presets |

Research material: [AI Hero](https://www.aihero.dev/skills),
[Emil's skills](https://github.com/emilkowalski/skills),
[Taste Skill](https://github.com/Leonxlnx/taste-skill).
Internal rules are concise original synthesis; no third-party code or long prompt
blocks are redistributed in this repository. Upstream reference checkouts retain
their own licenses in private installation state.

## Cost controls and limits

Tiny tasks bypass planning and broad scans. Standard tasks load only relevant
modules. Complex tasks use a short goal, with parallel work only when independent,
authorized and worth duplicated context plus integration. This is routing guidance,
not a new scheduler or rigid task-classification system.

Stable conventions and source pointers are reused within a task; changes invalidate
the relevant conclusions. No persistent semantic cache is added: invalidation and
private-source leakage risks outweigh demonstrated savings here. Browser rechecks
target changed regions; no custom browser cache duplicates the existing CLI.

Tool/schema loading belongs to each client. The stack does not promise to remove
all Serena schemas or unrelated plugin descriptions from model context. No invented
universal lazy-MCP flag, model routing API, native goal command or prompt-cache
switch is installed. Supported client-native discovery/caching may help, but it is
not portable behavior guaranteed by these files. Accounts and default models stay
unchanged; monetary savings require task-level comparisons with acceptable output.

## Ownership and migration

Version 2 is a breaking layout change. Only hash-matching owned v1 skills retire,
with timestamped backups. Unmanaged names, edited skills/hooks/blocks and edited
helper commands cause conflicts. New skill-name collisions are checked before
retirement. Related runtime tools remain installed even when their integration is
disabled. Hooks from other packages and user settings remain untouched.

One canonical personal DESIGN.md lives in skills/design. Install-time runtime.json
points its thin search entry point at the shared private database. Those absolute
paths never enter this repository. Ordinary installs reuse upstream sources;
explicit updates fetch supported current versions. This is online reproducibility,
not a lockfile-based offline distribution.

Repository instructions and design/code standards precede personal defaults. This
is additive guidance, subject to the client's own instruction and permission rules.
It cannot technically guarantee perfect model compliance; behavior tests check it.
