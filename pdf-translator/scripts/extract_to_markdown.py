#!/usr/bin/env python3
"""PDF to Markdown Extractor - Converts PDF to clean Markdown with images."""

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

try:
    import fitz
except ImportError:
    print("Error: pymupdf not installed. Run: uv pip install pymupdf")
    exit(1)

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


@dataclass
class DocumentMetadata:
    title: str = ""
    author: str = ""
    page_count: int = 0
    source_file: str = ""


def fix_corrupted_chars(text: str) -> str:
    """Fix common character corruption from PDF extraction."""
    text = re.sub(r'●(\w+)\)', r'(\1)', text)
    text = re.sub(r'\((\w+)●', r'(\1)', text)
    text = re.sub(r'●(\w+)●', r'(\1)', text)
    text = re.sub(r'●', '', text)
    text = re.sub(r'([\w.]+)\s+([\w-]+\.(?:com|org|edu|ac|co|net|gov)(?:\.[a-z]{2,})?)\b', r'\1@\2', text)
    return text


def fix_broken_urls(text: str) -> str:
    """Fix URLs broken during PDF extraction."""
    result = re.sub(r'(https?://\w+)\.\s+(\w+)', r'\1.\2', text)
    result = re.sub(r'(https?://[\w.]+)\s*/\s*', r'\1/', result)
    result = re.sub(r'(https?://[\w./]+)\s+(\w+)', r'\1\2', result)
    result = re.sub(r'https?://doi\.\s*org', 'https://doi.org', result)
    return result


def filter_artifact_text(text: str) -> bool:
    """Return True if text is artifact/noise."""
    stripped = text.strip()
    if re.match(r'^[a-z]?\d{5,}(\s+[a-z]?\d{5,})*$', stripped):
        return True
    if len(stripped) < 2:
        return True
    return False


def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ''
    text = fix_corrupted_chars(text)
    text = fix_broken_urls(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def is_heading(block: Dict, page_blocks: List[Dict]) -> bool:
    """Detect if a text block is a heading."""
    if not block.get("lines"):
        return False

    line = block["lines"][0]
    if not line.get("spans"):
        return False

    span = line["spans"][0]
    font_size = span.get("size", 0)
    text = span.get("text", "").strip()

    # Get average font size
    all_sizes = []
    for b in page_blocks:
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                all_sizes.append(s.get("size", 0))

    avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 10

    # Heading criteria
    if font_size > avg_size * 1.2:
        return True
    if span.get("flags", 0) & 2**4:  # Bold
        if len(text) < 100 and not text.endswith('.'):
            return True

    return False


def detect_heading_level(font_size: float, max_size: float) -> int:
    """Determine heading level based on font size."""
    ratio = font_size / max_size if max_size > 0 else 0
    if ratio > 0.9:
        return 1
    elif ratio > 0.7:
        return 2
    elif ratio > 0.5:
        return 3
    return 4


def extract_images(doc: fitz.Document, output_dir: str, min_width: int = 100, min_height: int = 100) -> Dict[int, List[str]]:
    """Extract images from PDF, returns dict of page_num -> image paths."""
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    page_images = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        page_images[page_num + 1] = []

        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)

                if base_image["width"] < min_width or base_image["height"] < min_height:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                image_filename = f"page{page_num + 1:03d}_img{img_idx:03d}.{image_ext}"
                image_path = os.path.join(images_dir, image_filename)

                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                page_images[page_num + 1].append(f"images/{image_filename}")
            except Exception:
                continue

    return page_images


def extract_tables_from_page(page_num: int, pdf_path: str) -> List[str]:
    """Extract tables from a page using pdfplumber."""
    if pdfplumber is None:
        return []

    tables_md = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    md_lines = []
                    # Header
                    header = [str(cell or '').replace('\n', ' ').replace('|', '\\|') for cell in table[0]]
                    md_lines.append('| ' + ' | '.join(header) + ' |')
                    md_lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')

                    # Rows
                    for row in table[1:]:
                        cells = [str(cell or '').replace('\n', ' ').replace('|', '\\|') for cell in row]
                        # Pad if needed
                        while len(cells) < len(header):
                            cells.append('')
                        md_lines.append('| ' + ' | '.join(cells[:len(header)]) + ' |')

                    tables_md.append('\n'.join(md_lines))
    except Exception:
        pass

    return tables_md


def extract_page_text(page: fitz.Page, page_num: int) -> Tuple[str, List[Dict]]:
    """Extract text from a page as Markdown."""
    text_dict = page.get_text("dict")
    blocks = text_dict.get("blocks", [])

    # Filter text blocks only
    text_blocks = [b for b in blocks if b.get("type") == 0]

    # Get max font size for heading detection
    max_font_size = 0
    for block in text_blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                max_font_size = max(max_font_size, span.get("size", 0))

    lines = []
    block_info = []

    for block in text_blocks:
        block_text = ""
        block_font_size = 0

        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                line_text += span.get("text", "")
                block_font_size = max(block_font_size, span.get("size", 0))
            block_text += line_text + "\n"

        block_text = block_text.strip()
        if not block_text or filter_artifact_text(block_text):
            continue

        block_text = clean_text(block_text)
        if not block_text:
            continue

        # Check if heading
        is_head = is_heading(block, text_blocks)

        if is_head:
            level = detect_heading_level(block_font_size, max_font_size)
            lines.append(f"\n{'#' * level} {block_text}\n")
        else:
            lines.append(f"\n{block_text}\n")

        block_info.append({
            "text": block_text,
            "is_heading": is_head,
            "bbox": block.get("bbox", [])
        })

    return '\n'.join(lines), block_info


def extract_metadata(doc: fitz.Document, pdf_path: str) -> DocumentMetadata:
    """Extract document metadata."""
    meta = doc.metadata or {}

    title = meta.get("title", "")
    if not title:
        # Try to get title from first page
        if len(doc) > 0:
            page = doc[0]
            text_dict = page.get_text("dict")
            blocks = [b for b in text_dict.get("blocks", []) if b.get("type") == 0]

            max_size = 0
            title_candidate = ""
            for block in blocks[:5]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("size", 0) > max_size:
                            max_size = span.get("size", 0)
                            title_candidate = span.get("text", "").strip()

            title = title_candidate

    return DocumentMetadata(
        title=title,
        author=meta.get("author", ""),
        page_count=len(doc),
        source_file=os.path.basename(pdf_path)
    )


def generate_frontmatter(metadata: DocumentMetadata, source_lang: str, target_lang: str) -> str:
    """Generate YAML frontmatter."""
    return f'''---
title: "{metadata.title}"
author: "{metadata.author}"
pages: {metadata.page_count}
source_file: "{metadata.source_file}"
source_language: {source_lang}
target_language: {target_lang}
---

'''


def extract_to_markdown(pdf_path: str, output_dir: str, source_lang: str = "auto", target_lang: str = "ko") -> Dict[str, Any]:
    """Extract PDF to Markdown with images."""

    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)

    # Extract metadata
    metadata = extract_metadata(doc, pdf_path)
    print(f"Title: {metadata.title}")
    print(f"Pages: {metadata.page_count}")

    # Extract images
    print("Extracting images...")
    page_images = extract_images(doc, output_dir)
    image_count = sum(len(imgs) for imgs in page_images.values())
    print(f"Extracted {image_count} images")

    # Extract text and build markdown
    print("Extracting text...")
    markdown_parts = [generate_frontmatter(metadata, source_lang, target_lang)]

    if metadata.title:
        markdown_parts.append(f"# {metadata.title}\n\n")

    for page_num in range(1, len(doc) + 1):
        page = doc[page_num - 1]

        # Page anchor
        markdown_parts.append(f'\n<!-- Page {page_num} -->\n')

        # Extract tables first (to avoid duplication with text)
        tables = extract_tables_from_page(page_num, pdf_path)

        # Extract text
        page_text, _ = extract_page_text(page, page_num)
        markdown_parts.append(page_text)

        # Add tables
        for table_md in tables:
            markdown_parts.append(f"\n{table_md}\n")

        # Add images
        for img_path in page_images.get(page_num, []):
            markdown_parts.append(f"\n![Image]({img_path})\n")

    # Combine and clean
    markdown = '\n'.join(markdown_parts)
    markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)

    # Save markdown
    output_path = os.path.join(output_dir, "source.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    # Save metadata
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)

    doc.close()

    print(f"Saved: {output_path}")

    return {
        "markdown_path": output_path,
        "metadata": asdict(metadata),
        "image_count": image_count,
        "page_count": metadata.page_count
    }


def main():
    parser = argparse.ArgumentParser(description='Extract PDF to Markdown')
    parser.add_argument('--pdf', required=True, help='Input PDF file')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--source-lang', default='auto', help='Source language')
    parser.add_argument('--target-lang', default='ko', help='Target language')
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Error: PDF not found: {args.pdf}")
        return 1

    result = extract_to_markdown(
        args.pdf,
        args.output_dir,
        args.source_lang,
        args.target_lang
    )

    print(f"\nExtraction complete:")
    print(f"  Pages: {result['page_count']}")
    print(f"  Images: {result['image_count']}")
    print(f"  Output: {result['markdown_path']}")

    return 0


if __name__ == '__main__':
    exit(main())
