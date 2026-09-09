---
name: engineering-quality
description: Readable substantial features, multi-file refactors, and diagnosis of difficult bugs.
---
# Engineering quality

Choose implementation, changed-code review or diagnosis as needed. Repository
conventions are evidence, not problems to replace with personal habits. Read
relevant neighbors and standards once; retain compact task-local conclusions,
commands, decisions and source pointers. Refresh stale or conflicting evidence.
No mandatory document or persistent cache service.

For substantial exploration, use Serena's relevant symbol overview, then specific
bodies/references. Bound depth and results. Reuse context; ordinary file access
suits obvious edits. If semantic tools fail, use a narrow fallback and disclose
material limits rather than repeatedly retrying.

Inspect changed scope for unclear names, duplication, deep nesting, hidden coupling,
surprising side effects, relevant error handling and dead code. Split units with
distinct responsibilities. Prefer obvious control flow and understandable APIs.
Refactor only what the task needs; no arbitrary line limits, speculative reuse or
normalization of unrelated code. Frontend checks belong to frontend-quality.

For difficult bugs, establish the cheapest reliable failure signal: focused test,
request, CLI fixture or browser interaction. Form one hypothesis, change the
smallest relevant thing and recheck. After repeated equivalent failure, revisit
the hypothesis or missing evidence. Broaden only when results justify it. No
mandatory test suite, instrumentation project or separate reviewer for an obvious fix.

Handoff explains behavior, meaningful verification and limitations concisely.
Skipped or blocked checks are not passes. Explicit reviews distinguish adherence
to the request from repository standards in one review unless independent
reviewers are justified and authorized.
