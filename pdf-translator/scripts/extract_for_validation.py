#!/usr/bin/env python3
"""Token-Efficient Text Extractor for LLM Validation."""

import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


def extract_text_from_json(file_path: str) -> Tuple[str, str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'text' in data:
            return 'text_block', data['text']
        elif 'data' in data:
            rows = [' | '.join(str(cell) for cell in row) for row in data['data']]
            return 'table', '\n'.join(rows)
        elif 'title' in data:
            parts = []
            if data.get('title'):
                parts.append(f"Title: {data['title']}")
            if data.get('author'):
                parts.append(f"Author: {data['author']}")
            if data.get('bookmarks'):
                parts.append("Bookmarks:")
                for bm in data['bookmarks'][:10]:
                    parts.append(f"  - {bm.get('title', '')}")
            return 'metadata', '\n'.join(parts)
        return 'unknown', ''
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 'error', ''


def format_for_validation(files_data: Dict[str, Dict]) -> str:
    output_lines = []
    pages = {}
    for file_name, info in files_data.items():
        page_num = info.get('page_num', 0)
        if page_num not in pages:
            pages[page_num] = []
        pages[page_num].append(info)

    for page_num in sorted(pages.keys()):
        output_lines.append(f"[PAGE: {page_num}]")
        output_lines.append("<blocks>")
        for idx, info in enumerate(pages[page_num], 1):
            text = info.get('text', '')
            if len(text) > 500:
                text = text[:500] + "..."
            output_lines.append(f"{idx}: {text}")
        output_lines.append("</blocks>")
        output_lines.append("")
    return "\n".join(output_lines)


def estimate_tokens(text: str) -> int:
    cjk_chars = len(re.findall(r'[\u3000-\u9fff\uac00-\ud7af]', text))
    other_chars = len(text) - cjk_chars
    return int(cjk_chars / 1.5 + other_chars / 4)


def split_into_chunks(files_data: Dict[str, Dict], max_tokens: int = 8000) -> List[Dict[str, Dict]]:
    chunks = []
    current_chunk = {}
    current_tokens = 0

    for file_name, info in files_data.items():
        file_tokens = estimate_tokens(info.get('text', ''))
        if file_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = {}
                current_tokens = 0
            chunks.append({file_name: info})
            continue
        if current_tokens + file_tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = {}
            current_tokens = 0
        current_chunk[file_name] = info
        current_tokens += file_tokens

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def extract_directory(dir_path: str) -> Dict[str, Dict]:
    files_data = {}
    for json_file in sorted(Path(dir_path).glob('*.json')):
        file_type, text = extract_text_from_json(str(json_file))
        if text:
            page_match = re.search(r'page(\d+)', json_file.stem)
            page_num = int(page_match.group(1)) if page_match else 0
            files_data[json_file.name] = {
                'file_type': file_type,
                'text': text,
                'page_num': page_num
            }
    return files_data


def generate_validation_manifest(chunks: List[Dict], output_dir: str) -> Dict:
    manifest = {"total_chunks": len(chunks), "validation_tasks": []}
    for idx, chunk in enumerate(chunks):
        task_id = f"validate_{idx + 1:03d}"
        input_file = os.path.join(output_dir, f"{task_id}_input.txt")
        output_file = os.path.join(output_dir, f"{task_id}_result.json")
        status_file = os.path.join(output_dir, f"{task_id}.status")

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
    parser = argparse.ArgumentParser(description='Extract text for LLM validation')
    parser.add_argument('--dir', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-tokens', type=int, default=8000)
    parser.add_argument('--single-file', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        print(f"Error: Directory not found: {args.dir}")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Extracting text from: {args.dir}")
    files_data = extract_directory(args.dir)

    if not files_data:
        print("No JSON files found or no text extracted")
        return 1

    print(f"Found {len(files_data)} files")

    if args.single_file:
        output_text = format_for_validation(files_data)
        output_path = os.path.join(args.output_dir, "validation_input.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"Output: {output_path} (~{estimate_tokens(output_text)} tokens)")
    else:
        chunks = split_into_chunks(files_data, args.max_tokens)
        manifest = generate_validation_manifest(chunks, args.output_dir)
        manifest_path = os.path.join(args.output_dir, "validation_manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"\nCreated {len(chunks)} validation chunks")
        print(f"Manifest: {manifest_path}")
        for task in manifest["validation_tasks"]:
            print(f"  - {task['task_id']}: {len(task['files_included'])} files, ~{task['estimated_tokens']} tokens")
    return 0


if __name__ == '__main__':
    exit(main())
