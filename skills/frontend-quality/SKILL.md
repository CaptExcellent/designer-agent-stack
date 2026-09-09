---
name: frontend-quality
description: Substantial React/Next.js implementation, data flow, performance, and reusable component APIs.
---
# Frontend quality

Apply relevant checks during implementation, not a performance audit for every
visual edit. Inspect framework version and local patterns before version-specific advice.

- Start independent requests together; respect dependency order, cancellation,
  errors and authorization. Avoid moving latency to another serial layer.
- Keep secrets and privileged work on the server. Place client boundaries around
  actual interaction, not entire trees for one control. Use local loading/error patterns.
- Scope caching by ownership, freshness and invalidation. Shared caches cannot
  leak user data. Do not assume the same caching defaults across Next versions.
- Limit client payload and heavy imports. Split genuinely optional features with
  supported mechanisms; do not fragment tiny code for theoretical savings.
- Keep state near readers and derive values rather than synchronize copies.
  Stable identity and memoization must solve a concrete issue, not become rituals.
- Reuse existing primitives. Choose explicit variants or composition when boolean
  props encode different structures. Compound APIs and context must simplify real reuse.
- Make state ownership, controlled/uncontrolled behavior and component contracts
  explicit. Avoid providers, factories and wrappers for speculative reuse.

For a specific uncertainty, consult only relevant framework docs or retained
upstream rules. `agent-stack reference react <term>` and
`agent-stack reference composition <term>` list matching reference files before
reading one. Never load a complete catalog by default. Requested production
analysis is separate: `agent-stack reference optimize` locates Vercel Optimize
when installed using `--with-vercel`.

Validate changed behavior and the concrete performance risk. Distinguish measured
results from inferred improvements; do not claim unmeasured speed gains.
