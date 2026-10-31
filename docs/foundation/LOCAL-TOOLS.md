# Local development tools

Verified 29 October 2026. Docker Desktop was already installed; it has been started successfully with its WSL2 Linux engine. No separate Ubuntu installation or Windows reboot was required for these checks.

Node 26.13.0 (npm 11.20.0) and Go 1.27.3 were downloaded from official distribution endpoints, checked against published SHA256 hashes and extracted under work/runtimes. The existing global Node installation and global PATH are unchanged. Runtime archives and binaries are ignored by Git.

From a PowerShell terminal in C:/Users/ADMIN/mcpStudio, run:

```powershell
. .\tools\Use-ProjectToolchain.ps1
node --version
npm --version
go version
docker version
```

Activation affects only the current terminal and its child processes. Repeat it in a new terminal. Keep Docker Desktop running for container work.

`powershell -NoProfile -File tools/check-prerequisites.ps1` automatically selects the local tools and performs read-only checks. `npm run check:contracts` checks source integrity; it is not application testing.

Evidence: docs/quality/prerequisite-installation.json. A trusted Alpine fixture ran as a non-root user with capabilities dropped, no-new-privileges, read-only input/root, network none, resource limits and writable temporary filesystem. Input bytes were unchanged and the container removed itself. The fixture is not comprehensive adversarial sandbox proof. Database constraints, application services, SDK interoperability, selected worker Python and full integration workflow remain M0.3 work.
