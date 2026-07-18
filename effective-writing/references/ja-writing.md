# Japanese Writing Norms

Supplementary rules for Japanese prose. Apply together with `base-writing.md`.

## Perspective and voice

- Use actors as subjects with active verbs, not passive result listings. Prefer 「調査して特定し、見つけた」 over 「特定され、判明した」.
- Do not address the reader as 「あなた」 in argumentation. Use role names such as 「開発者」 or 「読者」. Reserve second-person address for boundaries like chapter openings and closings.
- Choose specific terms for referents. Do not blur with broad words like 「AI」 or 「ツール」. Once a technical term is introduced, use it consistently; do not retreat to vague words like 「文脈」 or 「ツール」.
- Choose terminology established in the field. Do not substitute a semantically close kanji compound as if it were the conventional term.
- Do not repurpose technical-sounding words in non-technical contexts. Use plain expressions instead.

## Expression restraint

Use rhetoric only where it produces a concrete effect.

- Reserve dramatic buildup (溜め) and rhetorical questions for moments where tension serves the argument. State things directly when explanation suffices.
- Do not overuse short punchlines as standalone paragraphs. Noun-ending sentences (体言止め) are acceptable only at scene climaxes.
- Limit bold emphasis to logical pivots, at most one or two per section.
- Prefer judgment framing (「〜するわけにはいかない」) over imperative prohibitions (「〜してはならない」).
- Do not overdramatize turning points. A single factual sentence often suffices.
- Do not preview claims with 「重要なのは〜である」. State the claim directly.
- Do not use twisted idioms or ambiguous metaphors. Use plain verbs.

## Cognitive rhythm

Dense writing becomes tedious when every sentence operates in the same cognitive mode. Create forward momentum by deliberately switching the reader's mode: observing, hesitating, asserting, re-examining.

### Sentence rhythm

- Ground with a short sentence, flow with a longer sentence, stop with a short sentence. This "ground-flow-stop" pattern is the basic paragraph beat.
- Do not push through with assertions alone. Alternate assertion (「〜だった」「〜である」) with hesitation (「〜に違いない」「〜とは思う。ただ…」). Hesitation is a device, not weakness: a conviction later overturned by facts sets up a reader's expectation to be broken.

### Paragraph density

- After two or three dense paragraphs, place one sparse paragraph. A sparse paragraph serves one of: anchoring a settled point, presenting the next subject, or shifting perspective distance.
- Alternate paragraphs that zoom in on specifics (records, numbers, quotes) with paragraphs that step back to interpret meaning.

### Opening design

The opening's job is to create one unresolved tension within the first few sentences. The form is free, but avoid a toneless agenda listing (「本章ではA、B、Cを扱う」). Choose an entry that generates tension: a hypothesis from the reader's experience, an assertion with conviction, a narrator's assumption overturned by facts.

### Section transitions

Do not announce sections with 「本節では〜を扱う」. Instead, restate the discomfort left by the previous section as a question, write the reader's natural objection directly, or open with the writer's confession. Introduce theory only after creating a "not-yet-named discomfort" in the reader.

### List grounding

After listing properties or categories, ground each item in a concrete scene from the preceding discussion. Vary the landing style across items rather than using a uniform format.

### Question resolution and endings

- Do not abandon questions raised in the text. Resolve them explicitly. Returning answers in halves creates momentum for the second half.
- End by landing accumulated abstractions onto something concrete the reader already holds (the opening scene, their own experience). Do not end on abstraction alone.
- One tension may remain open at the very end.

### Distinguishing slack from padding

The test has one axis: does the sentence update the **situation** or the **document**?

- **Situation-updating sentence**: conveys new information about the subject world (events, data, statements) or the narrator's judgment state (assumptions, reservations, regrets). Keep it.
- **Document-updating sentence**: only describes how this chapter or explanation "looks" or "what comes next." Delete it by default.

Only four exceptions are allowed: (1) refuting a specific misreading by quoting it, (2) setting or resolving a question after creating tension, (3) a request or disclaimer to the reader placed at a boundary, (4) opening or closing the frame of a hypothetical example.

Padding appears in short punchy forms too, not only in long explanatory sentences. When a document-updating sentence is shortened into a rhythmic one-liner, it looks like a good beat and survives editing. Delete it unless it passes the topic test.

## LLM-patterned expressions to avoid

Do not use expressions that add no argument and only create an appearance of thoroughness:

- **Previews and summaries**: 「本章では〜を扱う／探求する」「まとめると」「〜に他ならない」
- **Empty adjectives**: 「不可欠」「核心的」「鍵となる」「根本的な」「多角的」「包括的」「総合的」
- **Empty verbs**: 「掘り下げる」「深掘りする」「言語化する」「触れる」「言及する」
- **Boilerplate connectors** (carrying no new information): 「〜において」「〜という側面から」「〜の観点から」; chaining 「さらに」「また」「加えて」
- **Groundless hedging and empty intensifiers**: 「〜と言えるだろう」「〜かもしれない」 when weakening a claim without basis; 「非常に」「極めて」「大いに」 as contentless emphasis

Preserve 「かもしれない」 and 「だろう」 when they express genuine uncertainty, hypothesis, a reader's anticipated doubt, or a character's perception. Distinguish between situations that require uncertainty and situations where hedging merely weakens the argument.

## Redundancy

- Do not restate the same claim in different words. State each claim once.
- Do not re-summarize a scene immediately after describing it. Add only a single sentence of interpretation.
- Combine parallel facts with the same logical role into one sentence.
- Do not explain intermediate steps the reader can infer on their own.
- Do not insert sentences that serve only as evaluation or connective filler (e.g., 「それ自体はよいことである」).
- Do not use imaginary reader Q&A as a rhetorical device. State the claim directly.
- Do not introduce the reader's expected idea with meta-framing (「ここまでの話には自然な続きがある」「〜という発想である」). Write the idea itself directly.
- Connective expressions that create rhythm are not redundancy.

## Post-writing checklist

After completing a draft, check in this order:

1. **Topic test**: Examine the first sentence of each paragraph and every standalone short sentence. Determine whether it updates the situation or the document. Delete or rewrite document-side sentences.
2. **Leakage test**: Search for device vocabulary (「緊張」「回収」「線を引く」 etc.) appearing literally in the text. If found, delete and re-implement the device through content.
3. **Tension ledger**: List every question, assumption, and promise raised in the text. Confirm each has a resolution point. If not, either write the resolution or remove the question.
4. **Rhythm check**: Find stretches of three or more consecutive long declarative sentences. Insert a short grounding sentence, a stop, or a moment of hesitation.
5. **Boundary check**: Confirm that second-person address, reader requests, and authorial modesty do not appear in the middle of argumentation. Move them to boundaries or delete.

## Diagnostic guide

- **Every paragraph feels the same**: No sentence rhythm. Apply checklist step 4.
- **Correct but no desire to keep reading**: No unresolved tension. Create tension at the opening and verify at least one is always open.
- **Theory sections feel cold**: Theory was introduced before creating discomfort. Place a question or confession before the theory.
- **Slack exists but feels limp**: Slack sentences are document-updates (progress narration). Apply the topic test and rewrite to situation-side.
- **Chapter ending feels preachy**: Closed on abstraction. Land on the reader's concrete experience and leave one question open.
- **Opening feels bureaucratic**: A toneless agenda listing. Give the preview sentence an attitude, or precede it with the reader's experience or resistance.
