# Japanese Technical Writing Norms

Supplementary rules for Japanese technical manuscripts (book chapters, articles, explainers). Apply together with `base-writing.md` and `ja-writing.md`.

## Formatting

- One sentence per line. Separate paragraphs with blank lines.
- Wrap code, diffs, logs, and config fragments in code blocks.
- Move tangential supplements (term etymology, formal names) to footnotes (`[^label]`).
- Use bullet lists for definitions or classifications. Bold the term being defined. First occurrence uses bold; subsequent mentions use 「」.
- Do not use dashes (em dash `—`, double dash `——`) in Japanese body text. Use parentheses for parenthetical insertions; split rephrasing into two sentences with a period or join with a comma (読点).
- Do not use nakaguro (・) for parallel listing in Japanese. It is acceptable only inside a single proper noun.
- Do not pack two elements into a heading with a separator (e.g., 「種別──主題」). Make each heading a single natural phrase.
- In definition lists, use a full-width colon: 「**用語**：説明」.

## Paragraph and argument structure

Use paragraph writing as the foundation. Each paragraph is one step in the argument; the reader must be able to follow logic paragraph by paragraph.

- One topic per paragraph. If a paragraph mixes multiple phases (investigation, reporting, verification, evaluation), split into one paragraph per step.
- The first sentence of each paragraph should make the paragraph's topic clear.
- Open each paragraph with an explicit logical connector to the previous paragraph (「であれば」「実際」「しかし」「この例自体からも」).
- Do not introduce a new concept with a dictionary-style assertion (「XはYである」). First place the subject, then describe its function or difference, then give the definition if needed.
- Drive the argument in one direction. Do not state the conclusion, handle objections, then restate the conclusion. Handle objections first, then state the conclusion once.
- Explicitly deny the reader's likely misinterpretation before stating the real reason.
- When negating with 「AではなくB」, add one sentence of evidence for the negation. Counterfactuals (「もしAなら〜だっただろう」) often work well.
- In concessions (「確かに〜」), stay at factual acknowledgment. Do not assert in the author's voice content that will be corrected later.
- Do not reveal information meant to have impact at a climax in earlier paragraphs.
- Place forward references (「後の章で扱う」) at the end of a completed argument, not in the middle of one.

## Argument rigor

- Do not mechanically convert speculation, possibility, or reader doubts into assertions. Convert to assertion only when the proposition is established by evidence within the text.
- Do not group distinct things under 「同じ」. Keep distinguishable objects (separate decisions, separate causes, different kinds of problems) separate.
- Do not reduce a multi-factor event to a single cause.
- Maintain consistent treatment of the same concept across chapters and sections.
- When claiming causation, show the mechanism in one sentence. Do not write 「AだとBになる」 without explaining why.
- Do not write as if detection, guarantee, or resolution can "always" be achieved. State precisely with conditions (「〜しやすい」「〜できることが多い」「〜が成り立つときに限り」).
- Verify that the examples cited actually support the full scope of the claim. If they support only part, narrow the claim.
- Confirm that topics deferred with 「次節で扱う」 are actually resolved there. Do not plant unresolved foreshadowing.
- After placing a concession or limitation (「ただし」「とはいえ」), always advance the argument. Do not end on an adversative and leave the reader hanging.
- Define a section's central term before using it in that section.

## Reader load management

- Do not introduce proper nouns (file names, function names, identifiers) that will not be referenced later. Use general descriptions instead.
- When an abstract phrase does not resolve unambiguously from context, specify its referent with an inline parenthetical appositive.
- When adding a new example, preface it with what differs from the previous example and why another is needed.
- Do not overload chapter or section introductions with excessive detail unrelated to the examples.
- Keep specifics necessary for the argument. Omit only decorative precision (timestamps, HTTP status codes) and proper nouns not referenced later.

## Headings

- Make each heading a phrase that identifies the question the section answers or the subject it covers.
- Do not use headings that merely describe a procedure (「例に戻す」「〜を読み直す」) or carry no information.
- Do not make a heading a "punchline" that gives away the section's conclusion.
- Choose between a question form and a noun phrase based on whichever matches the body text's tone.

## Honesty with the reader

- If an example may appear contrived, do not hide it. Acknowledge the reader's likely doubt preemptively and briefly provide grounds that the scenario is realistic.
- Base those grounds on general facts or common experience the reader can relate to, not on the author's assertion (e.g., 「この症状は珍しくないだろう」 rather than 「十分あり得る状況だ」).
- Do not write as though something has been verified when it has not.
