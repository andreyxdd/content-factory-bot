# Optional review step after writing

When enabled at onboarding (`review_agent` answer), each **writing step** output passes through a **review step**: a separate model call scores clarity, voice match to **personality profile**, and platform fit, returning short feedback (and optionally a numeric score). Creators can disable at onboarding or later via `/profile`. Skipping review keeps the original two-menu draft flow unchanged.
