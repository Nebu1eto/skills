# PDF Translation Orchestrator

You are the orchestrator agent for PDF document translation. Your role is to coordinate the entire translation pipeline, from PDF extraction to final output generation.

---

## Overview

```
PDF → Extract → source.md → [Split if large] → Translate → Merge → Generate PDF
```

---

## Phase 0: Environment Setup

Before starting, ensure the environment is ready:

```bash
bash scripts/setup_env.sh
```

Set the Python path:
```bash
PYTHON=".venv/bin/python"
```

---

## Phase 1: Extract PDF to Markdown

Extract the PDF to a clean Markdown format:

```bash
WORK_DIR="/tmp/pdf_translate_$(date +%s)"
$PYTHON scripts/extract_to_markdown.py \
  --pdf "{PDF_PATH}" \
  --output-dir "$WORK_DIR" \
  --source-lang {SOURCE_LANG} \
  --target-lang {TARGET_LANG}
```

**Outputs:**
- `$WORK_DIR/source.md` - Original document as Markdown
- `$WORK_DIR/images/` - Extracted images
- `$WORK_DIR/metadata.json` - Document metadata

---

## Phase 2: Determine Translation Strategy

Read the metadata to check document size:

```bash
cat $WORK_DIR/metadata.json
```

### Decision Logic

| Estimated Tokens | Strategy |
|------------------|----------|
| ≤ 6000 | Direct translation (no splitting) |
| > 6000 | Split into sections, parallel translation |

---

## Phase 3A: Direct Translation (Small Documents)

For small documents, translate directly:

1. Read `references/translator_markdown.md` for translation guidelines
2. Read `$WORK_DIR/source.md`
3. Translate the entire content following the guidelines
4. Write output to `$WORK_DIR/translated.md`

**Important:** Follow all formatting rules in `translator_markdown.md`.

---

## Phase 3B: Parallel Translation (Large Documents)

### Step 1: Split the Markdown

```bash
$PYTHON scripts/split_markdown.py \
  --input "$WORK_DIR/source.md" \
  --output-dir "$WORK_DIR/sections" \
  --max-tokens 6000
```

### Step 2: Read the Manifest

```bash
cat $WORK_DIR/sections/sections_manifest.json
```

Example output:
```json
{
  "source_file": "/tmp/.../source.md",
  "total_tokens": 15000,
  "sections": 3,
  "files": ["section_001.md", "section_002.md", "section_003.md"]
}
```

### Step 3: Spawn Translation Agents

Create a `translated/` directory:
```bash
mkdir -p $WORK_DIR/translated
```

Spawn parallel Task agents for each section:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" for --high-quality
  run_in_background: false,
  prompt: "You are a Markdown translation agent.

Read the translation guidelines at:
{SKILL_DIR}/references/translator_markdown.md

Translate the following file from {SOURCE_LANG} to {TARGET_LANG}:
{WORK_DIR}/sections/section_001.md

Write the translated output to:
{WORK_DIR}/translated/section_001.md

Additional instructions:
- Academic mode: {true/false}
- Term annotation style: {parenthesis/footnote/inline}
- First occurrence only: {true/false}

If a custom dictionary is provided, apply it:
{DICT_PATH or 'None'}
"
)
```

**Parallel Execution:** Launch all section translation tasks simultaneously for efficiency.

### Step 4: Wait for Completion

Monitor all translation tasks until complete. Check for any failures and retry if necessary.

---

## Phase 4: Merge Translated Sections

After all sections are translated, merge them:

```bash
cat $WORK_DIR/translated/section_*.md > $WORK_DIR/translated.md
```

Verify the merge:
```bash
wc -l $WORK_DIR/translated.md
```

---

## Phase 5: Generate Output

### Markdown Output

Copy to the output directory:
```bash
cp $WORK_DIR/translated.md {OUTPUT_DIR}/{filename}_translated.md
```

### PDF Output

Generate PDF from the translated Markdown:

```bash
$PYTHON scripts/generate_pdf.py \
  --markdown "$WORK_DIR/translated.md" \
  --output "{OUTPUT_DIR}/{filename}_translated.pdf"
```

---

## Phase 6: Validation (Optional)

For quality assurance, validate the translation:

1. Check that all Markdown formatting is preserved
2. Verify tables render correctly
3. Ensure no untranslated text remains
4. Confirm images are referenced properly

Use `references/validator_generic.md` or `references/validator_ko.md` for language-specific validation.

---

## Error Handling

| Error | Recovery Action |
|-------|-----------------|
| PDF extraction failure | Report error, skip file |
| Section translation failure | Retry with smaller max-tokens |
| Merge failure | Check section files, retry merge |
| PDF generation failure | Output Markdown only |

---

## Model Selection

### Default
| Task | Model |
|------|-------|
| Section translation | Sonnet |
| Validation | Haiku |

### With --high-quality
| Task | Model |
|------|-------|
| Section translation | Opus |
| Validation | Sonnet |

---

## Variables Reference

| Variable | Description |
|----------|-------------|
| `{PDF_PATH}` | Input PDF file path |
| `{SOURCE_LANG}` | Source language code (e.g., en, ja, zh) |
| `{TARGET_LANG}` | Target language code (e.g., ko, en) |
| `{OUTPUT_DIR}` | Output directory for final files |
| `{SKILL_DIR}` | Path to pdf-translator skill directory |
| `{WORK_DIR}` | Temporary working directory |
| `{DICT_PATH}` | Custom dictionary JSON path (optional) |

---

## Example: Complete Workflow

```bash
# Setup
SKILL_DIR="/path/to/pdf-translator"
PYTHON="$SKILL_DIR/.venv/bin/python"
WORK_DIR="/tmp/pdf_translate_$(date +%s)"
PDF_PATH="/documents/research_paper.pdf"
OUTPUT_DIR="./translated"

# Phase 1: Extract
$PYTHON $SKILL_DIR/scripts/extract_to_markdown.py \
  --pdf "$PDF_PATH" \
  --output-dir "$WORK_DIR" \
  --source-lang en \
  --target-lang ko

# Phase 2: Check size and split if needed
$PYTHON $SKILL_DIR/scripts/split_markdown.py \
  --input "$WORK_DIR/source.md" \
  --output-dir "$WORK_DIR/sections" \
  --max-tokens 6000

# Phase 3: Translate sections (via Task agents)
mkdir -p $WORK_DIR/translated
# ... spawn Task agents for each section ...

# Phase 4: Merge
cat $WORK_DIR/translated/section_*.md > $WORK_DIR/translated.md

# Phase 5: Generate outputs
mkdir -p "$OUTPUT_DIR"
cp $WORK_DIR/translated.md "$OUTPUT_DIR/research_paper_translated.md"
$PYTHON $SKILL_DIR/scripts/generate_pdf.py \
  --markdown "$WORK_DIR/translated.md" \
  --output "$OUTPUT_DIR/research_paper_translated.pdf"
```
