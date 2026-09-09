---
name: motion
description: Decide, implement, or review purposeful UI animation and gesture behavior.
---
# Motion

Choose the needed mode: identify an opportunity, implement an interaction, or
review changed motion. Do not run all modes by default.

Name the benefit: state, continuity, feedback, hierarchy or explanation. Frequent
actions need immediate responses. Rare celebration can be expressive; the same
treatment on every interaction becomes tiring. Preserve project motion tokens
and personality. No new library for a fade.

For implementation, decide in order:

1. The state change and what stays usable during it.
2. Existing mechanism; otherwise CSS transition, animation or WAAPI before a new
   library. Existing motion libraries can be useful for gestures and layout.
3. Properties and origin. Prefer transform/opacity when adequate; layout animation
   needs a reason and bounded scope. Property names do not guarantee compositing.
   Avoid `transition: all` and unintended movement of reading targets.
4. Timing. Use project values first. Otherwise roughly 100–200ms suits small
   feedback and 150–300ms many panels: starting ranges, not universal limits.
   Responsive entrances often decelerate; continuous motion may need another curve.
5. Interruption. Rapid input retargets, reverses or cancels correctly, without
   stale completion callbacks. Gestures preserve direct control.
6. Reduced motion, touch/hover differences, cleanup and focus/state consistency.
   Honor requests for no animation while retaining clear static feedback.

For opportunities, solve an observable communication problem; do not hunt across
the whole repository unless asked. For review, inspect changed interactions and
their relevant states. Route subjective timing/feel through browser-qa's human
review. A technically valid curve cannot prove the motion feels right.
