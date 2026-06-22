# Claude Project Entry

Read `README.md` before acting. Then use the installed
`data-phinter-workflows:read-effective-verbal-context` skill to materialize or load
`effective-verbal-context.local.md` and recover the current working state.

When the plugin is not installed, read and follow
`plugins/data-phinter-workflows/skills/read-effective-verbal-context/SKILL.md` directly. Do not
assume browser control, scheduling, shell access, or a signed-in session merely because a workflow
mentions them; run the capability checks in
`plugins/data-phinter-workflows/references/runtime-prerequisites.md`.

`effective-verbal-context.md` is the committed, machine-independent project context.
`effective-verbal-context.local.md` is the gitignored local working context and takes precedence for
machine/run state. Never commit the local file, browser profiles, cookies, credentials, generated
run outputs, or mutable current-run pointers.
