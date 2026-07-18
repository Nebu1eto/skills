# Writing Quality Guide

General-purpose writing rules for drafting and editing prose in any language.
Produce clearer, more specific, better-sourced writing and avoid generic
machine-patterned prose.

## Before writing

Identify these before drafting:

- **Purpose**: explain, analyze, persuade, summarize, document, report, review, email, essay, technical guide, wiki article, README, slide copy, or another genre.
- **Audience**: general reader, expert, internal team, client, reviewer, developer, policymaker, or academic reader.
- **Evidence boundary**: provided sources only, external research allowed, no citations required, or citations required.
- **Claim type**: fact, interpretation, probability, recommendation, speculation, opinion, or instruction.
- **Output syntax**: plain prose, Markdown, HTML, wikitext, academic manuscript, README, report, email, or another format.

If evidence is missing, do not fill the gap with plausible generalities. Narrow the claim, qualify it, or omit it.

## Core rules

1. Prefer concrete facts over abstract significance.
2. Prefer simple words over grandiose words.
3. Prefer direct verbs over inflated constructions.
4. Prefer named sources over vague authorities.
5. Prefer one accurate claim over several decorative claims.
6. Prefer consistent terminology over forced synonym variation.
7. Prefer source fidelity over confident-sounding synthesis.
8. Prefer natural paragraph flow over template-like outlines.
9. Prefer formatting restraint.
10. Treat AI-writing indicators as warning signs, not as the only problem. Fix the deeper issue: weak sourcing, generic reasoning, unsupported inference, promotional tone, or poor structure.

## Source and attribution

Use source-bound reasoning. For each non-obvious claim, ask:

- What source supports this?
- Does the source actually say this?
- Am I paraphrasing, interpreting, or extending it?
- Would a skeptical reader accept the citation for this sentence?
- Can the sentence be narrowed?

If one source says something, name that source. If two sources say it, do not call it consensus. Do not write "experts argue", "industry reports suggest", or "scholars believe" unless the sources are named and the quantity is accurate.

If the provided material does not verify a claim, say so directly when relevant, narrow the claim, or omit it.

## Claim proportionality

Match claim strength to evidence strength.

Use: reported, found, described, argued, estimated, projected, associated with, consistent with.

Do not use: proved, redefined, transformed, demonstrated conclusively, changed everything, revolutionized, unless the evidence supports that level of certainty.

Do not make ordinary facts sound historically, socially, culturally, or technologically profound unless reliable sources establish that interpretation.

## Significance and notability

Do not try to prove importance by asserting it. Summarize what sources actually say and cite normally. Do not create sections titled "Media coverage", "Notability", "Significance", "Future Outlook", or "Challenges and Future Directions" unless the genre explicitly requires them and the content is specific and sourced.

## Format and medium

Use the syntax, density, and structure expected by the target medium. Do not default to Markdown, wikitext, academic structure, or slide structure unless that is the requested format.

- Use headings only for real sections. Use sentence-case unless the style guide expects title case.
- Do not skip heading levels in structured documents.
- Use lists only for parallel items or scannable procedures.
- Use tables only when aligned comparison is clearer than prose.
- Avoid excessive boldface, emoji headings, decorative Unicode, and ornamental separators in prose documents.

Do not mix platform syntaxes. Do not invent fields, tags, labels, templates, categories, metadata, or schema keys for any platform. If platform syntax is unknown, write portable plain text or simple Markdown.

## Citation integrity

Never fabricate or misuse references.

Do not invent URLs, article titles, authors, dates, DOIs, ISBNs, PMIDs, page numbers, journal metadata, publisher names, or quotes.

When citations are required:

- Verify that URLs resolve and DOI links lead to the cited work.
- For books, include page numbers when supporting specific claims.
- Do not cite a broad book or general webpage for a specific claim.
- Do not use a citation merely because it is topically related.
- If a source supports only a narrower claim, narrow the sentence.

Remove tracking parameters from cited URLs (utm_source, referrer, etc.).

## Register and consistency

Maintain the requested language variety and the style appropriate to the document. Use the same term for the same concept. Do not use elegant variation merely to avoid repetition. Change terms only when the meaning changes.

## Language and localization

Write as a fluent speaker of the output language would write for the stated audience. Do not preserve English word order, noun phrases, metaphors, collocations, or abstract terms merely because they have a dictionary translation.

- Prefer expressions common in the target language and field.
- Do not coin terms by translating technical nouns word for word. Use an established term when one exists; otherwise describe the behavior plainly or keep the source term.
- Translate the intended meaning and function, not each source word.
- Avoid noun-heavy or passive constructions carried over from English when the target language normally uses a direct verb.
- Preserve the user's terminology when it is clear and natural.

Before finalizing non-English prose, reread it without reference to the English source. Replace calques, translated idioms, and unnatural phrasing.

## Paragraph and document structure

- Do not turn every idea into a one-line paragraph or a punchy fragment.
- Do not disguise a list as prose with "The first...", "The second...".
- Do not summarize at every level: avoid "what I will say, what I am saying, what I just said."
- Do not add a generic conclusion that repeats the whole document.
- Remove duplicate or near-duplicate claims, sections, and paragraphs.

Every substantive paragraph should add at least one of: date, number, actor, source, mechanism, location, condition, limitation, example, counterexample, causal link, comparison baseline, implementation detail, decision criterion, tradeoff, or implication.

## Genre structures

Choose structure by genre:

- **Analysis**: claim, evidence, reasoning, limitation or counterargument, implication.
- **Technical writing**: problem, constraints, design, implementation, failure modes, tradeoffs, verification.
- **Informational article**: identifying fact, relevant background, chronology or components, sourced details, controversies or limitations only if sourced.
- **Recommendation**: criteria, options, tradeoffs, risks, decision rule.
- **Summary**: main finding, supporting details, exclusions, uncertainty.

## Revision protocol

When drafting or revising:

1. Remove unsupported claims of importance, legacy, influence, or transformation.
2. Replace vague attribution with named sources or remove the claim.
3. Replace inflated verbs and nouns with direct language.
4. Collapse listicle prose into a real list or connected prose.
5. Delete repeated summaries, duplicated content, and one-point dilution.
6. Remove promotional language unless the genre is promotional.
7. Check markup against the target platform.
8. Verify every citation, URL, DOI, ISBN, page number, and quote.
9. Remove placeholders, drafting residue, and tool artifacts.
10. Re-read for rhythm: avoid both monotony and theatrical punchiness.
11. Confirm that each paragraph adds information, reasoning, evidence, limitation, or necessary context.
12. For non-English prose, confirm that terminology, word order, and tone sound natural to the intended readers.

## Self-audit

Before producing final output, check:

- Are there unsupported significance claims?
- Are ordinary facts given generic broader meaning?
- Are source gaps filled with speculation?
- Are opinions attributed to unnamed experts, observers, critics, or reports?
- Does the draft imply consensus from too little evidence?
- Is formatting overused or mismatched to the target platform?
- Do all citations support the exact sentences they are attached to?
- Are all placeholders, internal artifacts, and drafting residues removed?
- Does the ending add judgment, limitation, implication, or next action rather than restating the piece?
- In non-English output, would a native speaker use these terms and sentence patterns?

Apply this guide silently. Do not mention the checklist unless the user asks.
