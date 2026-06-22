# Runtime Prerequisites And Stop Behavior

Read this before executing a workflow. Stranger recovery and accessibility review do not require
these systems to be exercised.

| Workflow | Required capability | Pre-execution check | Stop or intervention behavior |
|---|---|---|---|
| Context recovery | Repository files and readable handoff | Confirm README, handoff, configs, and linked references exist | Report broken links or unresolved conflicts before acting |
| NotebookLM generation | Installed Codex Browser or Chrome Plugin, callable browser-control tools, and a Google account already signed in | Discover the current browser capability; confirm the existing tab or login state | If browser control is unavailable, name the missing capability. If login, quota, or download permission requires a person, notify the user and preserve the run |
| App candidate intake | Python project dependencies, configured default/candidate pointers, and supported `app.py` | Run the candidate audit first. Resolve the listener from `PORT` (default `5000`); start with `python app.py`, select/report a free port when occupied, then open `?agent=1` | Stop on blockers or review gates. Notify on captcha, login, access block, ambiguous acceptance, or irreversible write approval |
| Shopee recovery | Existing diagnostic artifact or permission to create one; browser/runtime only for a live probe | Read the saved artifact and taxonomy before choosing a probe | Keep environment, captcha, login, access, timeout, and selector failures distinct; request human action only for the matching condition |

The supported visible channels are the app UI, in-app browser, and user-visible artifacts/reports.
When a background batch is necessary, explain why those channels are unsuitable and return
checkpoints and results to a visible channel.

No workflow may silently substitute an unrelated transport when its required browser or app
capability is unavailable.
