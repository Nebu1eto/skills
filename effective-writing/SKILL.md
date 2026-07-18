---
name: effective-writing
description: Apply layered writing-quality guides to user-facing prose and persisted documents. Loads universal rules plus language-specific and domain-specific references as needed. Use for drafting or revising reports, documentation, tickets, messages, review comments, and presentation copy in any language.
---

# Effective Writing

Use this skill whenever producing or editing prose. Do not insert the skill's
checklist or internal drafting notes into the artifact. Follow the active runtime's
requirements for announcing skill use.

## Reference Loading

Before drafting or revising, identify the output language and document type,
then read the applicable references in order:

1. Always: `references/base-writing.md`
2. Language-specific (if available):
   - English: `references/en-writing.md`
   - Japanese: `references/ja-writing.md`
3. Domain-specific (if available):
   - Japanese technical documents: `references/ja-tech-writing.md`

Each reference file is a condensed prompt. Do not summarize them further before
applying. References are additive: later files supplement, not override, earlier ones.

## Naming Convention

Reference files follow this pattern:

- `base-writing.md` — rules for all languages
- `<lang>-writing.md` — rules for a specific language
- `base-<domain>-writing.md` — domain rules for all languages
- `<lang>-<domain>-writing.md` — domain rules for a specific language

## Operating Rules

- First identify the artifact purpose, audience, evidence boundary, claim type, and output syntax.
- Keep claims source-bound and proportionate.
- In every language, use native idiom and natural sentence structure. Do not carry
  English wording, abstractions, or collocations into another language by literal
  translation.
- Avoid generic AI phrasing, unsupported synthesis, inflated significance, promotional tone, citation residue, drafting residue, and platform-inappropriate markup.
- Match the target medium instead of defaulting to Markdown or a template structure.
- Run the applicable self-audit before returning or saving the artifact.
