# EPUB Translator

[한국어](README.ko-KR.md)

Claude Code skill for translating EPUB files between languages.

## Features

- Multi-language support (ja, en, zh, ko, ar, he, etc.)
- Parallel translation with configurable concurrency
- Large file splitting and merging
- Layout conversion (vertical/horizontal, LTR/RTL)
- LLM-based quality validation

## Installation

**Requirements**: Python 3.8+, `zip`, `unzip`

```json
// ~/.claude/settings.json
{
  "skills": ["/path/to/epub-translator"]
}
```

## Usage

```bash
# Japanese to Korean (default)
/epub-translator "novel.epub"

# English to Korean
/epub-translator "book.epub" --source-lang en

# Japanese to Chinese with vertical writing
/epub-translator "novel.epub" --target-lang zh --vertical

# Batch translate with 10 parallel agents
/epub-translator "/books/" --parallel 10

# High-quality translation using Opus
/epub-translator "novel.epub" --high-quality
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source-lang` | Source language | `ja` |
| `--target-lang` | Target language | `ko` |
| `--parallel` | Concurrent agents | `5` |
| `--split-threshold` | Split threshold (KB) | `30` |
| `--split-parts` | Parts per large file | `4` |
| `--high-quality` | Use Opus model | `false` |
| `--vertical` | Vertical writing (ja/zh only) | `false` |
| `--dict` | Custom dictionary (JSON) | none |
| `--output-dir` | Output directory | `./translated` |

## Layout Conversion

Output layout is determined by target language:

| Target | Direction | Writing Mode | Notes |
|--------|-----------|--------------|-------|
| ko, en | ltr | horizontal-tb | |
| ja, zh | ltr | horizontal-tb | Default |
| ja, zh + `--vertical` | rtl | vertical-rl | 縦書き/縱排 |
| ar, he | rtl | horizontal-tb | |

## Quality Validation

Two-stage verification:
1. **Source text check**: Detects remaining source characters
2. **LLM validation**: Assesses naturalness and translationese

Quality scores: 90-100 (excellent), 75-89 (good), 60-74 (acceptable), <60 (re-translate)

## Custom Dictionary

Use only for proper nouns and document-specific terms.

```json
{
  "proper_nouns": {
    "names": { "田中太郎": "Tanaka Taro" }
  },
  "domain_terms": {
    "ProprietaryTech": "Proprietary Technology"
  }
}
```

## Workflow

1. **Analysis**: Extract EPUB, split large files
2. **Translation**: Parallel translation via sub-agents
3. **Metadata**: Translate TOC, title, author
4. **Layout**: Convert writing direction
5. **Validation**: Quality check
6. **Package**: Merge and create EPUB

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Source text remaining | Run `verify.py` |
| Timeout on large files | Lower `--split-threshold` |
| XML errors | Check angle brackets (`<text>` → `〈text〉`) |
