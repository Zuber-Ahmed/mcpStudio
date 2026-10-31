# Worker runtime readiness

Verified 29 October 2026. Worker runtime uses the approved Linux-container architecture: Python 3.14.10, Temporal Python SDK 1.35.0, tree-sitter 0.26.0 and TypeScript/TSX grammar 0.23.2. This is runtime/parser readiness, not a finished analyzer or Temporal server integration.

## Evidence

- docs/quality/worker-runtime-validation.json: 11 checks passed with container network disabled, non-root user, read-only root, dropped capabilities, no-new-privileges and bounded CPU/memory/processes.
- docs/quality/worker-wheel-manifest.json: exact base image digest, readiness image ID and seven wheel hashes checked against PyPI metadata.
- apps/workers/requirements.linux-amd64.lock: complete resolved runtime dependencies with hashes for this tested Linux/CPython platform.
- tools/fixtures/worker: trusted parser/Temporal sandbox fixtures, readiness Dockerfile and setup reproducer.

The installer for native Windows Python was downloaded from python.org and passed its published SHA256 and Authenticode checks, but Windows Installer could not open its cached core MSI (error 2203 / exit 3). It did not install the native runtime. No older host Python was substituted for the worker test; the selected version was verified in the container.

## Reproduce

Use an available host Python interpreter to run tools/fixtures/worker/build-runtime.py. It downloads binary wheels, independently checks their published hashes, generates a complete lock, builds the image without network, and runs the trusted fixture. It writes evidence and readiness metadata, not product features. For an unchanged image, rerun the fixture with Docker using the existing local mcpstudio-worker-readiness:0.1.0 image and only docs/quality mounted at /evidence; network none and the resource/isolation flags from build-runtime.py are required.

The setup reproducer currently resolves transitive dependencies again before recording hashes. For deterministic reuse of the exact verified dependency set, download with --require-hashes against the committed requirements.linux-amd64.lock and use the pinned base digest; do not silently replace the lock on routine test runs. Future dependency updates require an explicit refreshed lock and validation evidence.

## Limits and next work

No application repository was mounted or executed. The source canary was only parsed; real framework/route detection remains unimplemented. Temporal workflow metadata and sandbox import preparation were checked without a Temporal server; execution, retry/recovery and storage remain next work. Worker dependency vulnerability review and broader resource/timeout/host-path tests belong to final readiness validation. No generated adapter, application deployment, Git commit or push was performed.
