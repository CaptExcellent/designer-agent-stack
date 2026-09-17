# Working defaults

Authority: explicit user request > repository instructions > repository design/code
standards > established local patterns > personal taste > expert guidance > general
practice > library defaults. Global guidance fills gaps; preserve project DESIGN.md
tokens and semantics. Never create or rewrite it without a request.

Tiny edits: use nearby context and finish directly. Substantial work: scan relevant
conventions once; retain conclusions and source pointers for the task, refreshing
only changed or conflicting evidence. Choose the cheapest adequate retrieval:
local files for obvious edits, Serena symbols/references for larger exploration.
Before reading broad command output, start with a narrow query: use `rg --files`,
`rg -n` with the needed context, a bounded file range, or a focused test target.
Avoid full-file reads, recursive listings and complete build/test logs unless the
task requires their details. If a compact command hides evidence needed to diagnose
or implement a change, rerun only that specific source command with the needed
range or context.

Load only relevant skills: design for visual decisions; motion for animation;
frontend-quality for substantial React/component work; engineering-quality for
features/refactors; task-planning for ambiguous or large work and high-value
clarification; browser-qa for objective UI checks and human-led visual review.

Reuse context, bound output, reinspect changes, and re-plan after repeated failure.
Extra agents and automated vision default to zero; use only when their value and
permissions justify them. Keep model/account settings unchanged unless authorized.
Once requirements and meaningful checks are satisfied, stop; disclose blocked checks.
