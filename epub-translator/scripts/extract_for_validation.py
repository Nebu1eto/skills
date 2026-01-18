#!/usr/bin/env python3
"""
Token-Efficient Text Extractor for LLM Validation

Extracts text from translated XHTML files in a compact format
optimized for LLM-based quality validation.

Output format is designed to minimize tokens while preserving
context needed for quality assessment.
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


def extract_paragraphs(file_path: str) -> List[Tuple[int, str]]:
    """
    Extract paragraphs from XHTML file.
    Returns list of (paragraph_number, text) tuples.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all paragraph contents
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)

        result = []
        for idx, p in enumerate(paragraphs, 1):
            # Remove nested tags
            text = re.sub(r'<[^>]+>', '', p)
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            # Skip empty or very short paragraphs
            if len(text) > 5:
                result.append((idx, text))

        return result
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []


def format_for_validation(files_data: Dict[str, List[Tuple[int, str]]]) -> str:
    """
    Format extracted text in token-efficient format for LLM.
    """
    output_lines = []

    for file_name, paragraphs in files_data.items():
        if not paragraphs:
            continue

        output_lines.append(f"[FILE: {file_name}]")
        output_lines.append("<paragraphs>")

        for para_num, text in paragraphs:
            # Truncate very long paragraphs to save tokens
            if len(text) > 500:
                text = text[:500] + "..."
            output_lines.append(f"{para_num}: {text}")

        output_lines.append("</paragraphs>")
        output_lines.append("")  # Empty line between files

    return "\n".join(output_lines)


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation.
    For Korean/Japanese: ~1.5 chars per token
    For English: ~4 chars per token
    """
    # Simple heuristic based on character types
    cjk_chars = len(re.findall(r'[\u3000-\u9fff\uac00-\ud7af]', text))
    other_chars = len(text) - cjk_chars

    return int(cjk_chars / 1.5 + other_chars / 4)


def split_into_chunks(files_data: Dict[str, List[Tuple[int, str]]],
                      max_tokens: int = 8000) -> List[Dict[str, List[Tuple[int, str]]]]:
    """
    Split files into chunks that fit within token limit.
    Each chunk can be processed by a separate validation agent.
    """
    chunks = []
    current_chunk = {}
    current_tokens = 0

    for file_name, paragraphs in files_data.items():
        file_text = " ".join([p[1] for p in paragraphs])
        file_tokens = estimate_tokens(file_text)

        # If single file exceeds limit, it goes in its own chunk
        if file_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = {}
                current_tokens = 0
            chunks.append({file_name: paragraphs})
            continue

        # Check if adding this file exceeds limit
        if current_tokens + file_tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = {}
            current_tokens = 0

        current_chunk[file_name] = paragraphs
        current_tokens += file_tokens

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def extract_directory(dir_path: str) -> Dict[str, List[Tuple[int, str]]]:
    """
    Extract text from all XHTML files in directory.
    """
    files_data = {}

    xhtml_files = sorted(Path(dir_path).rglob('*.xhtml'))

    for xhtml_file in xhtml_files:
        file_name = xhtml_file.name
        paragraphs = extract_paragraphs(str(xhtml_file))

        if paragraphs:
            files_data[file_name] = paragraphs

    return files_data


def generate_validation_manifest(chunks: List[Dict], output_dir: str) -> Dict:
    """
    Generate manifest for parallel validation agents.
    """
    manifest = {
        "total_chunks": len(chunks),
        "validation_tasks": []
    }

    for idx, chunk in enumerate(chunks):
        task_id = f"validate_{idx + 1:03d}"
        input_file = os.path.join(output_dir, f"{task_id}_input.txt")
        output_file = os.path.join(output_dir, f"{task_id}_result.json")
        status_file = os.path.join(output_dir, f"{task_id}.status")

        # Write chunk to input file
        chunk_text = format_for_validation(chunk)
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(chunk_text)

        manifest["validation_tasks"].append({
            "task_id": task_id,
            "input_file": input_file,
            "output_file": output_file,
            "status_file": status_file,
            "files_included": list(chunk.keys()),
            "estimated_tokens": estimate_tokens(chunk_text)
        })

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description='Extract text from translated files for LLM validation'
    )
    parser.add_argument('--dir', required=True,
                        help='Directory with translated XHTML files')
    parser.add_argument('--output-dir', required=True,
                        help='Output directory for validation files')
    parser.add_argument('--max-tokens', type=int, default=8000,
                        help='Maximum tokens per validation chunk (default: 8000)')
    parser.add_argument('--single-file', action='store_true',
                        help='Output as single file instead of chunks')

    args = parser.parse_args()

    if not os.path.exists(args.dir):
        print(f"Error: Directory not found: {args.dir}")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Extracting text from: {args.dir}")
    files_data = extract_directory(args.dir)

    if not files_data:
        print("No XHTML files found or no text extracted")
        return 1

    total_paragraphs = sum(len(p) for p in files_data.values())
    print(f"Found {len(files_data)} files with {total_paragraphs} paragraphs")

    if args.single_file:
        # Single file output
        output_text = format_for_validation(files_data)
        output_path = os.path.join(args.output_dir, "validation_input.txt")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)

        print(f"Output written to: {output_path}")
        print(f"Estimated tokens: {estimate_tokens(output_text)}")
    else:
        # Chunked output for parallel processing
        chunks = split_into_chunks(files_data, args.max_tokens)
        manifest = generate_validation_manifest(chunks, args.output_dir)

        # Save manifest
        manifest_path = os.path.join(args.output_dir, "validation_manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"\nCreated {len(chunks)} validation chunks")
        print(f"Manifest saved to: {manifest_path}")

        for task in manifest["validation_tasks"]:
            print(f"  - {task['task_id']}: {len(task['files_included'])} files, "
                  f"~{task['estimated_tokens']} tokens")

    return 0


if __name__ == '__main__':
    exit(main())
