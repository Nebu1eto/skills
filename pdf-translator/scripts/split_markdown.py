#!/usr/bin/env python3
"""Markdown Splitter - Splits large Markdown files into sections for translation."""

import argparse
import os
import re
from typing import List, Tuple


def estimate_tokens(text: str) -> int:
    """Estimate token count (roughly 4 chars per token for English, 2 for CJK)."""
    # Simple estimation: count words and CJK characters
    words = len(re.findall(r'\b\w+\b', text))
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', text))
    return words + cjk_chars


def find_split_points(content: str) -> List[int]:
    """Find good split points (headings)."""
    split_points = [0]

    # Find all heading positions
    for match in re.finditer(r'^(#{1,4})\s+.+$', content, re.MULTILINE):
        split_points.append(match.start())

    split_points.append(len(content))
    return sorted(set(split_points))


def split_markdown(content: str, max_tokens: int = 6000) -> List[Tuple[str, int]]:
    """Split markdown into chunks, respecting heading boundaries.

    Returns list of (chunk_content, estimated_tokens).
    """
    split_points = find_split_points(content)
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for i in range(len(split_points) - 1):
        section = content[split_points[i]:split_points[i + 1]]
        section_tokens = estimate_tokens(section)

        # If single section exceeds max, we need to include it anyway
        if section_tokens > max_tokens and current_chunk:
            chunks.append((current_chunk.strip(), current_tokens))
            current_chunk = section
            current_tokens = section_tokens
        elif current_tokens + section_tokens > max_tokens and current_chunk:
            chunks.append((current_chunk.strip(), current_tokens))
            current_chunk = section
            current_tokens = section_tokens
        else:
            current_chunk += section
            current_tokens += section_tokens

    # Add remaining
    if current_chunk.strip():
        chunks.append((current_chunk.strip(), current_tokens))

    return chunks


def extract_frontmatter(content: str) -> Tuple[str, str]:
    """Separate frontmatter from content."""
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            frontmatter = content[:end + 3]
            body = content[end + 3:].strip()
            return frontmatter, body
    return '', content


def save_chunks(chunks: List[Tuple[str, int]], output_dir: str, frontmatter: str = "") -> List[str]:
    """Save chunks to files."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for i, (chunk, tokens) in enumerate(chunks):
        filename = f"section_{i + 1:03d}.md"
        filepath = os.path.join(output_dir, filename)

        # Add section marker
        content = f"<!-- Section {i + 1} of {len(chunks)} -->\n\n{chunk}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        paths.append(filepath)
        print(f"  {filename}: ~{tokens} tokens")

    return paths


def main():
    parser = argparse.ArgumentParser(description='Split Markdown for translation')
    parser.add_argument('--input', required=True, help='Input Markdown file')
    parser.add_argument('--output-dir', required=True, help='Output directory for sections')
    parser.add_argument('--max-tokens', type=int, default=6000, help='Max tokens per section')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        return 1

    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter, body = extract_frontmatter(content)

    total_tokens = estimate_tokens(body)
    print(f"Total estimated tokens: {total_tokens}")

    if total_tokens <= args.max_tokens:
        print("Document fits in single section, no splitting needed")
        chunks = [(body, total_tokens)]
    else:
        chunks = split_markdown(body, args.max_tokens)
        print(f"Split into {len(chunks)} sections:")

    # Save
    paths = save_chunks(chunks, args.output_dir, frontmatter)

    # Save manifest
    manifest = {
        "source_file": args.input,
        "total_tokens": total_tokens,
        "sections": len(chunks),
        "max_tokens": args.max_tokens,
        "files": [os.path.basename(p) for p in paths]
    }

    import json
    manifest_path = os.path.join(args.output_dir, "sections_manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved: {manifest_path}")
    return 0


if __name__ == '__main__':
    exit(main())
