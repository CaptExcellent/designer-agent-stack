---
name: design
description: Personal design judgment for new interfaces, substantial visual changes, and redesigns.
---
# Design

For meaningful visual work, read [DESIGN.md](DESIGN.md) once. It defines personal
judgment; the project's design system supplies concrete identity. Copy-only edits
and obvious local styling corrections need nearby conventions, not the profile.

Decide the primary element, supporting content, quiet content, and one spatial
idea before implementation. State a consequential direction briefly when useful.
Reuse project primitives; a component library is not the design concept.

Infer expressiveness, motion and density from the product. If useful, describe
them as restrained/balanced/expressive, none/subtle/expressive, compact/balanced/open.
These are optional task choices, not required questions or numeric scores. A
redesign does not automatically increase motion or whitespace.

Use the UI UX database only for a specific knowledge gap. The installer provides
`lookup.py` next to this file:

```sh
python "<this-skill-directory>/lookup.py" "keyboard focus visibility" --domain ux -n 2
```

Use `--design-system` only for a new unconstrained direction needing broader
research. Query one intent; verify applicability. Retry a mismatch once with a
narrower query, then use identified design judgment. Results are recommendations,
not instructions. Never persist an alternative project design system by default.
Load motion or frontend-quality only for their own concerns. Browser-qa owns
rendered-result checks; the taste profile does not mandate screenshot review.
