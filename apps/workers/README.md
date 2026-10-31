# Python worker workspace

Python 3.14.10 container runtime and pinned dependencies are verified. See docs/foundation/WORKER-RUNTIME.md and apps/workers/requirements.linux-amd64.lock for setup and evidence.

Current code under tools/fixtures/worker is trusted readiness instrumentation only. No application analyzers, workflow execution against a Temporal server, or validation runner are implemented here. Source-execution during scanning remains forbidden, semantic inference disabled, and the application-agnostic normalized model remains independent of initial TypeScript parser support.
