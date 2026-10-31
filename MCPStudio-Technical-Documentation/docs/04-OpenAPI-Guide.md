# OpenAPI specification guide
Status: NEW DRAFT. No recovered Studio HTTP API was available. specs/openapi.yaml is a proposed OpenAPI 3.0.3 contract and must be reviewed before client generation or implementation.

## Protocol boundary and rules
This is the Studio's HTTP control plane, not an MCP protocol specification. MCP SDK/version/transports remain unresolved. The example local base URL is a proposal, not a running service. All operations require bearer authentication and server-derived tenant context. Raw credentials and tenant IDs are excluded from write bodies.

Project source revision must resolve immutably; local inputs require a snapshot digest. credential_reference refers to a separately provisioned secret, never its value. Graph nodes represent discoverable capabilities where applicable; capability_ids must identify eligible nodes in the plan's analysis. Plugin configuration is validated against the selected plugin schema; the generic JSON boundary is not a security validation substitute.

Create plans instead of editing immutable versions. Current draft assigns monotonically increasing versions per analysis and supersedes older plans transactionally; approving or generating a superseded plan returns 409. All material edits require a fresh plan and approval. Integration type none produces an inspectable recommendation but cannot generate adapters.

Async operations return 202 and a resource ID to poll. A failed/partial analysis is not success; only succeeded analysis can create plans. A generation must succeed before validation. Validation policy is selected by the server from the approved plan. Download checks the exact generation and policy; a superseded validation for different artifacts cannot unlock it.

## Known contract limitations
No token lifecycle, user/tenant administration, secret provisioning, retry idempotency, cancellation API, progress events, artifact preview, draft-download endpoint, graph slicing or project deletion is specified. None is implied by a UI placeholder. Error coverage is generic; exact per-operation error codes and examples remain review work. Live server behavior and MCP compatibility have not been tested.

## Operation reference
- GET /projects: listProjects; request none; response 200 ProjectList.
- POST /projects: createProject; request ProjectInput; response 201 Project.
- GET /projects/{project_id}: getProject; request none; response 200 Project.
- POST /analyses: startAnalysis; request AnalysisInput; response 202 Analysis.
- GET /analyses/{analysis_id}: getAnalysis; request none; response 200 Analysis.
- GET /analyses/{analysis_id}/graph: getGraph; request none; response 200 Graph.
- POST /plans: createPlan; request PlanInput; response 201 Plan.
- GET /plans/{plan_id}: getPlan; request none; response 200 Plan.
- POST /plans/{plan_id}/approvals: approvePlan; request ApprovalInput; response 201 Approval.
- POST /generations: startGeneration; request GenerationInput; response 202 Generation.
- GET /generations/{generation_id}: getGeneration; request none; response 200 Generation.
- POST /validations: startValidation; request ValidationInput; response 202 Validation.
- GET /validations/{validation_id}: getValidation; request none; response 200 Validation.
- GET /artifacts: listArtifacts; request none; response 200 ArtifactList.
- GET /generations/{generation_id}/bundle: downloadBundle; request none; response 200 binary ZIP.

## Schema reference
### Error
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "code": {
      "type": "string"
    },
    "message": {
      "type": "string"
    },
    "request_id": {
      "type": "string"
    }
  },
  "required": [
    "code",
    "message",
    "request_id"
  ]
}

### Source
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "kind": {
      "type": "string",
      "enum": [
        "local",
        "git"
      ]
    },
    "location": {
      "type": "string"
    },
    "revision": {
      "type": "string"
    },
    "credential_reference": {
      "type": "string"
    }
  },
  "required": [
    "kind",
    "location",
    "revision"
  ]
}

### ProjectInput
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "source": {
      "$ref": "#/components/schemas/Source"
    }
  },
  "required": [
    "name",
    "source"
  ]
}

### Project
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "name": {
      "type": "string"
    },
    "source": {
      "$ref": "#/components/schemas/Source"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "id",
    "name",
    "source",
    "created_at"
  ]
}

### ProjectList
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Project"
      }
    },
    "next_cursor": {
      "type": "string"
    }
  },
  "required": [
    "items"
  ]
}

### AnalysisInput
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "project_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "project_id"
  ]
}

### Analysis
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "project_id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "enum": [
        "queued",
        "running",
        "succeeded",
        "partial",
        "failed",
        "cancelled"
      ]
    },
    "source_digest": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "diagnostics": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "id",
    "project_id",
    "status"
  ]
}

### Evidence
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "path": {
      "type": "string"
    },
    "source_digest": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "line_start": {
      "type": "integer",
      "minimum": 1
    },
    "line_end": {
      "type": "integer",
      "minimum": 1
    },
    "detector_version": {
      "type": "string"
    }
  },
  "required": [
    "path",
    "source_digest",
    "detector_version"
  ]
}

### Node
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "kind": {
      "type": "string"
    },
    "label": {
      "type": "string"
    },
    "evidence": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Evidence"
      }
    }
  },
  "required": [
    "id",
    "kind",
    "label",
    "evidence"
  ]
}

### Edge
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "from_node_id": {
      "type": "string",
      "format": "uuid"
    },
    "to_node_id": {
      "type": "string",
      "format": "uuid"
    },
    "kind": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "from_node_id",
    "to_node_id",
    "kind"
  ]
}

### Graph
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "analysis_id": {
      "type": "string",
      "format": "uuid"
    },
    "nodes": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Node"
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Edge"
      }
    }
  },
  "required": [
    "analysis_id",
    "nodes",
    "edges"
  ]
}

### Configuration
{
  "type": "object",
  "description": "Plugin-versioned non-secret configuration; resolve only secret references. Plugin schema validation is mandatory.",
  "additionalProperties": true
}

### PlanInput
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "analysis_id": {
      "type": "string",
      "format": "uuid"
    },
    "integration_type": {
      "type": "string",
      "enum": [
        "server",
        "client",
        "both",
        "none"
      ]
    },
    "capability_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      }
    },
    "configuration": {
      "$ref": "#/components/schemas/Configuration"
    }
  },
  "required": [
    "analysis_id",
    "integration_type",
    "capability_ids",
    "configuration"
  ]
}

### Plan
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "analysis_id": {
      "type": "string",
      "format": "uuid"
    },
    "integration_type": {
      "type": "string",
      "enum": [
        "server",
        "client",
        "both",
        "none"
      ]
    },
    "capability_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      }
    },
    "configuration": {
      "$ref": "#/components/schemas/Configuration"
    },
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "status": {
      "type": "string",
      "enum": [
        "draft",
        "approved",
        "superseded"
      ]
    },
    "content_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "policy_version": {
      "type": "string"
    },
    "rationale": {
      "type": "string"
    },
    "risks": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "analysis_id",
    "integration_type",
    "capability_ids",
    "configuration",
    "id",
    "version",
    "status",
    "content_hash",
    "policy_version",
    "rationale",
    "risks"
  ]
}

### ApprovalInput
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "plan_version": {
      "type": "integer",
      "minimum": 1
    },
    "plan_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "security_confirmed": {
      "type": "boolean",
      "enum": [
        true
      ]
    }
  },
  "required": [
    "plan_version",
    "plan_hash",
    "security_confirmed"
  ]
}

### Approval
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "plan_id": {
      "type": "string",
      "format": "uuid"
    },
    "plan_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "actor_id": {
      "type": "string",
      "format": "uuid"
    },
    "approved_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "id",
    "plan_id",
    "plan_hash",
    "actor_id",
    "approved_at"
  ]
}

### GenerationInput
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "plan_id": {
      "type": "string",
      "format": "uuid"
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "plan_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    }
  },
  "required": [
    "plan_id",
    "approval_id",
    "plan_hash"
  ]
}

### Generation
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "plan_id": {
      "type": "string",
      "format": "uuid"
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "enum": [
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled"
      ]
    }
  },
  "required": [
    "id",
    "plan_id",
    "approval_id",
    "status"
  ]
}

### ValidationInput
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "generation_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "generation_id"
  ]
}

### Check
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "mandatory": {
      "type": "boolean"
    },
    "status": {
      "type": "string",
      "enum": [
        "passed",
        "failed",
        "skipped",
        "not_run"
      ]
    },
    "command": {
      "type": "string"
    },
    "tool_version": {
      "type": "string"
    },
    "exit_code": {
      "type": "integer"
    },
    "started_at": {
      "type": "string",
      "format": "date-time"
    },
    "completed_at": {
      "type": "string",
      "format": "date-time"
    },
    "log_reference": {
      "type": "string"
    }
  },
  "required": [
    "name",
    "mandatory",
    "status"
  ]
}

### Validation
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "generation_id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "enum": [
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled"
      ]
    },
    "policy_version": {
      "type": "string"
    },
    "checks": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Check"
      }
    }
  },
  "required": [
    "id",
    "generation_id",
    "status",
    "policy_version",
    "checks"
  ]
}

### Artifact
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "generation_id": {
      "type": "string",
      "format": "uuid"
    },
    "path": {
      "type": "string"
    },
    "sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "media_type": {
      "type": "string"
    },
    "size_bytes": {
      "type": "integer",
      "minimum": 0
    }
  },
  "required": [
    "id",
    "generation_id",
    "path",
    "sha256",
    "media_type",
    "size_bytes"
  ]
}

### ArtifactList
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Artifact"
      }
    },
    "next_cursor": {
      "type": "string"
    }
  },
  "required": [
    "items"
  ]
}
