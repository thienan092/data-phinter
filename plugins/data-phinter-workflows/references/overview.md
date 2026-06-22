# Data Phin-ter Plugin Overview

Use this map after recovering project state with `read-effective-verbal-context`. It provides the
smallest complete set of entry points; follow the responsible skill when deeper mechanics are needed.

```mermaid
flowchart LR
    P[Portable context<br/>effective-verbal-context.md]
    L[Local context<br/>effective-verbal-context.local.md]
    C[Recover context<br/>read-effective-verbal-context]
    G[Generate candidates<br/>notebooklm-sst-research]
    A[Audit, verify, accumulate<br/>app-sst-candidate-intake]
    S[Recover Shopee failures<br/>shopee-scrape-recovery]
    M{Verification mode}
    D[Compatible by default<br/>Selenium]
    F[Fast option<br/>BS4]
    X[Adaptive escalation<br/>CloakBrowser/provider]

    P -->|First use: materialize| L
    L --> C
    P -. durable baseline .-> C
    C --> G
    C --> A
    G --> A
    A --> M
    M --> D
    M --> F
    M -->|Evidence + proposal + approval| X
    X --> S
    A -->|Shopee failure| S
    S --> A
```

| Need | Entry skill | Next depth |
|---|---|---|
| Understand or resume the project | `read-effective-verbal-context` | Handoff, configs, then detailed architecture |
| Produce a new candidate artifact | `notebooklm-sst-research` | Generation boundary and output contract |
| Process an existing candidate | `app-sst-candidate-intake` | Audit, verification, report gate, approved write |
| Diagnose a Shopee-specific failure | `shopee-scrape-recovery` | Failure taxonomy and bounded recovery |

Verification starts in Selenium-backed `compatible`. A stranger can discover `fast` and `adaptive`
from this map without activating them accidentally. Context recovery may identify evidence for an
adaptive escalation, but the agent must explain and obtain user approval before switching.

The public context is committed and virtualized. `read-effective-verbal-context` creates or prefers
the gitignored local context for machine/run state. Handoff writing remains owner-maintained outside
the plugin: a stranger may materialize/read local context and report a documentation delta, but does
not publish it.

The skill graph is host-neutral. Codex, Claude Code, and Claude/Cowork use host-specific plugin/tool
adapters, then follow the same artifact, decision, and ownership contracts. Runtime capability does
not follow automatically from installing a skill.

Continue with [architecture.md](architecture.md) for component mechanics or
[artifact-and-status-contract.md](artifact-and-status-contract.md) for state and artifact semantics.
Before execution, read [runtime-prerequisites.md](runtime-prerequisites.md) for capability checks,
human-intervention points, and supported stop behavior.
