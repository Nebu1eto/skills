# Effective Writing

[한국어](README.ko-KR.md)

Agent skill for drafting and revising prose with clear claims, source discipline, and medium-appropriate formatting. Loads layered reference guides by language and domain.

## Purpose

Use this skill when writing or editing user-facing prose, repository documentation, review comments, tickets, reports, emails, slide copy, or summaries in any language.

It helps avoid generic AI phrasing, unsupported claims, inflated tone, citation misuse, drafting residue, and markup that does not fit the target medium.

## Usage

```bash
/effective-writing Rewrite this README section.
/effective-writing Review this report for unsupported claims.
/effective-writing Draft a concise PR comment from these findings.
/effective-writing この章を推敲してください。
```

## Works Best For

- README and documentation prose
- Technical explanations and reports
- Review comments and issue tickets
- Emails and short messages
- Summaries and slide copy
- Source-bound revisions
- Multilingual documents

## Layered References

The skill loads reference guides based on the output language and document type:

| Situation | References loaded |
|---|---|
| English | `base-writing.md` + `en-writing.md` |
| Japanese general | `base-writing.md` + `ja-writing.md` |
| Japanese technical | `base-writing.md` + `ja-writing.md` + `ja-tech-writing.md` |
| Other languages | `base-writing.md` |

### Naming Convention

- `base-writing.md` — rules for all languages
- `<lang>-writing.md` — rules for a specific language
- `base-<domain>-writing.md` — domain rules for all languages
- `<lang>-<domain>-writing.md` — domain rules for a specific language

## Acknowledgments

The Japanese writing references (`ja-writing.md`, `ja-tech-writing.md`) were derived from the following skills by [@k16shikano](https://github.com/k16shikano), released under the [Unlicense](https://gist.github.com/k16shikano/67625f2a7d96e3bbdfae8d571a936063):

- [japanese-tech-writing](https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d)
- [cognitive-rhythm-writing](https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432)

## Structure

```text
effective-writing/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── base-writing.md
    ├── en-writing.md
    ├── ja-writing.md
    └── ja-tech-writing.md
```
