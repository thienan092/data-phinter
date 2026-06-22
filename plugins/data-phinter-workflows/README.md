# Data Phin-ter Workflows

Cross-agent workflow plugin for the Data Phin-ter repository. The same `skills/` bundle is packaged
for Codex and Claude/Cowork through host-specific manifests.

Start with [references/overview.md](references/overview.md). It maps the four plugin entry points without
duplicating the detailed mechanics in each skill. Use
[references/architecture.md](references/architecture.md) for boundaries, data flow, decision gates,
and architecture-maintenance rules. Check
[references/runtime-prerequisites.md](references/runtime-prerequisites.md) before executing an
external or local workflow.

The independent Stranger audit is an external quality check of this plugin. It is not bundled as a
skill or automatic plugin workflow.

## Bundled Skills

- `read-effective-verbal-context`: recover and reconcile project state.
- `notebooklm-sst-research`: generate strict candidate artifacts.
- `app-sst-candidate-intake`: audit, verify, report, repair, and accumulate after approval.
- `shopee-scrape-recovery`: classify and recover Shopee-specific failures.

Verification defaults to Selenium-backed `compatible`. The plugin also exposes `fast` (BS4) and an
approval-gated `adaptive` escalation (CloakBrowser/provider) through its overview and intake skill.

The plugin is a project workflow layer. The Data Phin-ter application, configs, runtime scripts, and
data artifacts remain in the workspace and are not copied into the plugin.

`write-effective-verbal-context` is intentionally retained by the project owner and is not bundled.
Strangers can materialize/read `effective-verbal-context.local.md` and report a documentation delta,
but must not assume they can invoke the owner-held maintenance skill or publish local state.

## Host Adapters

| Host | Package entry | Runtime note |
|---|---|---|
| Codex | `.codex-plugin/plugin.json` | Repository canonical skills also live under `.codex/skills/`. |
| Claude Code | `.claude-plugin/plugin.json`; load with `claude --plugin-dir ./plugins/data-phinter-workflows` | Skills are invoked under the `data-phinter-workflows` namespace. |
| Claude Desktop / Cowork | Install or upload the same plugin package | Skills travel with the plugin; local shell/browser/session capabilities must still be checked at runtime. |

Browser and scheduler implementations are adapters, not workflow semantics. A NotebookLM run may
continue only when the current host can control the intended signed-in browser context and route
human intervention. App workflows likewise require access to the local project and listener.

## Development

The canonical development skills live under the repository's `.codex/skills/` directory. Synchronize
them into this bundle with:

```powershell
python plugins/data-phinter-workflows/scripts/sync_skills.py
```

Then validate the bundle and plugin manifest before audit or release.

```powershell
python plugins/data-phinter-workflows/scripts/validate_bundle.py

python <plugin-creator-skill>/scripts/validate_plugin.py plugins/data-phinter-workflows
```

Version 1.0.0 is a repository-local plugin artifact. Marketplace publication or installation is a
separate, explicit step after external Stranger audit. Validate both manifests before release.
