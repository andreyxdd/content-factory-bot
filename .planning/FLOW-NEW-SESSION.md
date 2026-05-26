# `/new` session flow (canonical)

```
/new  [requires setup complete: profile ready + ≥1 provider connection]
  → SETUP (inline keyboards)
       • Where to post — if 2+ connected: toggles (default **all ON**); if exactly 1: implicit (no toggles)
       • Web research?  [default from onboarding]
       • Cover / thumbnail?  [default OFF]
  → INPUT
       • Text / voice (STT) / image
  → RESEARCH (if ON at setup)
       • Sonar brief from input + personality profile
  → WRITING (worker)
       • 3 draft options
  → REVIEW (if enabled at onboarding)
       • Critique / scores → show Creator
  → INITIAL DRAFT MENU
       • 3 options + custom reply
  → FOLLOW-UP MENU
       • Three new | Edit selected | Confirm + custom
  → … refinement rounds …
  → CONFIRM final draft
  → COVER (if ON at setup)
  → PUBLISH → urls → session closed
```

Setup flags are fixed for the session once input starts (no re-ask cover mid-session unless `/new` again).
