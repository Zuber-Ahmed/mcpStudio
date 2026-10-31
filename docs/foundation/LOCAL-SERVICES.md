# Local foundation services

M0.3 readiness fixtures only. PostgreSQL 17.11 backs Temporal 1.32.1; SeaweedFS 4.51 provides local S3. Image digests are pinned in `infra/compose.yaml` and recorded in `docs/quality/local-service-images.json`.

From the repository root, with Docker Linux containers running:

```powershell
python tools/fixtures/services/configure-local-services.py
docker compose --env-file .local/services/services.env -f infra/compose.yaml -p mcpstudio-local up -d
docker compose --env-file .local/services/services.env -f infra/compose.yaml -p mcpstudio-local ps
```

The configuration generator uses Python's standard library, generates local credentials once, and reuses them. Keep `.local/services` private and ignored. Preserve credentials together with existing service volumes; replacing credentials does not change an existing PostgreSQL password.

Temporal is published at `127.0.0.1:7233`, S3 at `http://127.0.0.1:8333`. PostgreSQL has no host port. Temporal uses development `--allow-no-auth`; these settings are for this local foundation only. S3 uses generated credentials. The worker/database network is internal; Temporal and storage additionally use a bridge for loopback publication. SeaweedFS telemetry is disabled.

Stop while retaining data:

```powershell
docker compose --env-file .local/services/services.env -f infra/compose.yaml -p mcpstudio-local stop
```

Do not remove named volumes when retaining workflow history or stored objects.

## Repeating the controlled readiness check

The local `mcpstudio-service-readiness:0.1.0` image contains the checked Python worker runtime plus hash-locked boto3 dependencies. Its Dockerfile and lockfile are in `tools/fixtures/services`; the assembled wheelhouse/build context is under ignored `work/service-fixture-build`. Rebuild that existing context offline with `docker build --network none -t mcpstudio-service-readiness:0.1.0 work/service-fixture-build`. A fresh checkout must first assemble the locked wheels and worker image; neither generated image is distributed with the repository.

```powershell
$fixtureArgs = @('run','--rm','--network','mcpstudio-local_default','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','512m','--cpus','1','--pids-limit','64','--tmpfs','/tmp:rw,noexec,nosuid,size=16m','--env-file','.local/services/fixture.env','--mount',"type=bind,source=$((Resolve-Path docs/quality).Path),target=/evidence")
docker @fixtureArgs mcpstudio-service-readiness:0.1.0
if ($LASTEXITCODE -ne 0) { throw 'Initial fixture failed; retain evidence for diagnosis.' }
docker compose --env-file .local/services/services.env -f infra/compose.yaml -p mcpstudio-local restart temporal storage
if ($LASTEXITCODE -ne 0) { throw 'Restart failed.' }
docker @fixtureArgs -e FIXTURE_PHASE=restart mcpstudio-service-readiness:0.1.0
if ($LASTEXITCODE -ne 0) { throw 'Persistence fixture failed; inspect evidence before repeating.' }
```

The first phase creates a unique trusted object through a workflow activity. The second reads the completed workflow and object after restart, then deletes only that object's key. Both phases poll service readiness. Run the phases sequentially; the second phase consumes the first phase's evidence and must not be repeated after successful cleanup. Workflow history remains in the local namespace with its configured retention.

`docs/quality/local-service-validation.json` records 11 passing check entries, including health before and after restart, invalid-credential rejection, byte/digest matching and exact fixture cleanup. This demonstrates service readiness, not application API, consent, authorization, analyzer or production-schema behavior. Final M0.3 readiness review remains open.
