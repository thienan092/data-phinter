# Runtime Prerequisites And Stop Behavior

Read this before executing a workflow. Stranger recovery and accessibility review do not require
these systems to be exercised.

| Workflow | Required capability | Pre-execution check | Stop or intervention behavior |
|---|---|---|---|
| Context recovery | Repository files plus readable `effective-verbal-context.md` | Confirm README, public context, context helper, configs, and linked references exist. Materialize or prefer `effective-verbal-context.local.md` and confirm it is ignored | Report broken links or unresolved conflicts before acting. Never put machine/run state into the public context by default |
| NotebookLM generation | A host-authorized browser-control capability, a Google account already signed in, and an intervention channel | Identify the host adapter (Codex Browser/Chrome plugin, Claude for Chrome, or equivalent permitted browser tool). Confirm the scheduled/current execution can control the intended tab and notify the user | If browser/session control is unavailable, do not begin partial generation. Name the missing capability. On login, quota, captcha, download, or permission action, notify the user and preserve the run |
| App candidate intake | Python project dependencies, a compatible Chrome/ChromeDriver pair for default `compatible`, configured default/candidate pointers, and supported `app.py` | Run the candidate audit first. Confirm Selenium can use its standard cache or explicit `CHROME_BINARY`/`CHROMEDRIVER_PATH`. Resolve the listener from `PORT` (default `5000`); start with `python app.py`, select/report a free port when occupied, then open `?agent=1`. Treat `fast` and `adaptive` as explicit alternatives, not automatic fallbacks | Stop on blockers or review gates. Notify on missing/mismatched driver, captcha, login, access block, ambiguous acceptance, irreversible write approval, or a proposed adaptive escalation |
| Shopee recovery | Existing diagnostic artifact or permission to create one; approved `adaptive` mode and browser/runtime for a live probe | Read the saved artifact and taxonomy before choosing a probe. Confirm the user approved adaptive execution for the stated scope | Keep environment, captcha, login, access, timeout, and selector failures distinct; request human action only for the matching condition |

The supported visible channels are the app UI, in-app browser, and user-visible artifacts/reports.
When a background batch is necessary, explain why those channels are unsuitable and return
checkpoints and results to a visible channel.

No workflow may silently substitute an unrelated transport when its required browser or app
capability is unavailable.

## Host Capability Matrix

| Host | Skill loading | Capabilities that still require preflight |
|---|---|---|
| Codex | Repository skills or `.codex-plugin` package | Browser plugin/session ownership, automation execution context, shell/runtime |
| Claude Code | `.claude-plugin` package via install or `--plugin-dir` | Browser extension/tool, shell permissions, local listener reachability |
| Claude Desktop / Cowork | Installed/uploaded plugin; folder instructions for repository entry | Local folder permissions, browser-control availability, connector network scope, intervention visibility |

Plugin installation proves only that the instructions are available. It does not prove that the host
can access a signed-in browser, a loopback app, or a scheduler capable of human intervention.

Agent controls are local by default. `?agent=1` reveals them but does not authorize them. Loopback
requests require `X-Agent-Automation: 1`; remote requests additionally require
`ENABLE_REMOTE_AGENT_AUTOMATION=1` and a matching `X-Agent-Automation-Token` value configured through
`AGENT_AUTOMATION_TOKEN`.
