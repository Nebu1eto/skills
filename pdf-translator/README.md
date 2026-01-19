# PDF Translate Skill

Translate PDF documents with high-quality Markdown and PDF output.

[한국어](README.ko-KR.md)

## Setup

```bash
bash scripts/setup_env.sh
```

## Usage

```bash
/pdf-translator document.pdf --target-lang ko
/pdf-translator paper.pdf --source-lang ja --academic
/pdf-translator paper.pdf --high-quality
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source-lang` | Source language (auto-detect) | `auto` |
| `--target-lang` | Target language | `ko` |
| `--output-format` | markdown / pdf / both | `both` |
| `--academic` | Include original terms | `false` |
| `--high-quality` | Use Opus model | `false` |
| `--dict` | Custom dictionary JSON | - |

## Features

- Table text spacing with x_tolerance parameter
- Reversed text detection and correction
- Concatenated word splitting (wordninja)
- Automatic punctuation spacing
- Complex term correction during translation

## Architecture

```
PDF → extract_to_markdown.py → source.md → split (if large) → translate → generate_pdf.py → output
```

