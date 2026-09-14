# 10 — The scheduled run

The message a scheduled session receives. It is short because the instruction lives in the
repository, versioned, where the gate can see it:

```
Run /newsroom-run. Today is {{date}} (Europe/Lisbon). Work on main; push only with every gate
green; never set estado: publicado; when blocked, write to the editor's inbox and stop. End with
the run record written to redacao/runs/ and one message in the editor's inbox.
```

For a headless run (`claude -p`), the same text is the prompt argument and the skill is found in
`.claude/skills/newsroom-run/SKILL.md`. For a Routine, it is the Routine's prompt. For the GitHub
Action, it is the `prompt:` input. See `../05__schedule/README.md`.
