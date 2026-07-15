# Writing Tropes

[한국어](README.ko-KR.md)

Agent skill for drafting and revising prose with clear claims, source discipline, and medium-appropriate formatting. Works in any language with native idiom and natural sentence structure.

## Purpose

Use this skill when writing or editing user-facing prose, repository documentation, review comments, tickets, reports, emails, slide copy, or summaries.

It helps avoid generic AI phrasing, unsupported claims, inflated tone, citation misuse, drafting residue, and markup that does not fit the target medium.

## Usage

```bash
/writing-tropes Rewrite this README section.
/writing-tropes Review this report for unsupported claims.
/writing-tropes Draft a concise PR comment from these findings.
```

## Works Best For

- README and documentation prose
- Technical explanations and reports
- Review comments and issue tickets
- Emails and short messages
- Summaries and slide copy
- Source-bound revisions
- Multilingual documents

## Writing Rules

- Identify the purpose, audience, evidence boundary, claim type, and output syntax before drafting.
- Keep claims specific, source-bound, and proportionate.
- Use direct verbs and consistent terminology.
- In every language, use native idiom and natural sentence structure. Do not carry English wording or collocations into another language by literal translation.
- Avoid promotional tone, generic transitions, theatrical sentence patterns, and decorative formatting.
- Remove placeholders, drafting notes, tool artifacts, and citation residue before final output.

## Reference

The skill follows the full guide in:

```text
references/writing-quality.md
```

That file is the source of truth for style, attribution, citation integrity, formatting, localization, and final self-audit rules.

## Structure

```text
writing-tropes/
├── SKILL.md
├── agents/openai.yaml
└── references/writing-quality.md
```
