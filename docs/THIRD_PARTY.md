# Optional Headroom dependency

Designer Agent Stack is MIT licensed. The optional installer downloads
`headroom-ai[proxy]==0.37.0` into a private uv tool environment. This repository
contains original integration code; it does not vendor Headroom's source,
binaries or model weights and does not relicense them under MIT.

- [Headroom 0.37.0 source](https://github.com/headroomlabs-ai/headroom/tree/v0.37.0)
- [Apache License 2.0](https://github.com/headroomlabs-ai/headroom/blob/v0.37.0/LICENSE)
- [Upstream NOTICE and third-party acknowledgements](https://github.com/headroomlabs-ai/headroom/blob/v0.37.0/NOTICE)
- [Dependency declarations](https://github.com/headroomlabs-ai/headroom/blob/v0.37.0/pyproject.toml)

Apache-2.0 allows commercial use and integration alongside this MIT package.
Headroom, its dependencies and downloaded models retain their own licenses.
If distributing a bundled runtime or modified upstream code, preserve applicable
licenses and notices and identify upstream modifications as required. The current
installer fetches upstream distributions rather than shipping a combined artifact.

The proxy extra uses ONNX-based compression and can download model assets on first
use. The [Kompress model repository](https://huggingface.co/chopratejas/kompress-v2-base)
declares Apache-2.0. Additional or replacement models need their own license review;
the Python package license does not automatically cover every optional model.
The stack does not install the `all`, memory, or PyTorch ML extras.

The top-level Headroom release is pinned; transitive packages and externally fetched
model revisions are not fully locked. Re-check their licenses when changing the
release, extras or model configuration. RTK is not a dependency of this integration.
