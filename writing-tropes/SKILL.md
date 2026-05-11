---
name: writing-tropes
description: Writing and editing quality guardrail for drafting, rewriting, summarizing, documenting, reporting, emailing, review comments, README/docs prose, tickets, slide copy, and other prose artifacts. Use when the coding agent writes or revises user-facing or repository documentation, especially to follow the full writing-quality guide for avoiding generic AI phrasing, unsupported claims, promotional tone, citation misuse, drafting residue, and format-inappropriate markup.
---

# Writing Tropes

Use this skill whenever producing or editing prose. Apply it silently unless the user asks for a style audit or reasoning.

## Required Reference

Before drafting or revising prose, read and follow the full guide:

- `references/writing-quality.md`

Do not treat that file as optional or as background reading. It is the source of truth for this skill. The guide is already a condensed prompt, so do not summarize it further before applying it.

## Operating Rules

- First identify the artifact purpose, audience, evidence boundary, claim type, and output syntax.
- Keep claims source-bound and proportionate.
- Avoid generic AI phrasing, unsupported synthesis, inflated significance, promotional tone, citation residue, drafting residue, and platform-inappropriate markup.
- Match the target medium instead of defaulting to Markdown or a template structure.
- Run the guide's final self-audit before returning or saving the artifact.
