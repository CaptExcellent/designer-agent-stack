---
name: browser-qa
description: Targeted semantic browser verification and human-led subjective visual review.
---
# Browser QA

Use agent-browser when client permissions permit. Choose a named session so other
tasks' browsers remain untouched; open the actual running app:

```sh
agent-browser --session task-check open <actual-url>
agent-browser --session task-check snapshot -i
agent-browser --session task-check click @e2
agent-browser --session task-check snapshot -i
agent-browser --session task-check close
```

Refs belong to the observed state. Re-snapshot after changes before selecting new
refs. Inspect relevant content, semantics, states, interactions and routing.
An interactive snapshot is not a complete accessibility audit: use a targeted
fuller snapshot or DOM measurement when needed. Check a narrow viewport for
substantial responsive work without screenshotting every breakpoint.

Reinspect the changed region, not complete unchanged output. For unfamiliar syntax,
use `agent-browser <command> --help`; consult `skills get core` only when broader
workflow details are actually needed. Close only this task's session.

Subjective composition, type, balance, character and motion feel are human-led:
show or link the result and ask one concrete visual question if one remains.
Do not make tiny changes wait for design approval. User feedback outranks generic critique.

Automated vision defaults to zero. Use it when explicitly requested, necessary
for a supplied reference, the user cannot reasonably inspect, or a specific defect
genuinely requires vision. Semantic uncertainty is not blanket authorization for
aesthetic screenshots. After a justified check, fix the highest-impact issue,
verify affected state and stop.

Respect browser denial across tools and surfaces. Report blocked checks and get
renewed authorization rather than bypassing it. An executable or syntax check
does not establish real-browser QA.
