#!/usr/bin/env python3
"""Markdown Output Generator - Merges translated PDF content into Markdown."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_translated_content(work_dir: str, manifest: Dict) -> Dict[str, Any]:
    translated_dir = os.path.join(work_dir, 'translated')
    content = {'metadata': None, 'pages': {}}

    metadata_path = os.path.join(translated_dir, 'metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            content['metadata'] = json.load(f)

    for task in manifest.get('tasks', []):
        output_path = task.get('output_path', '')
        if not os.path.exists(output_path):
            continue
        with open(output_path, 'r', encoding='utf-8') as f:
            translated = json.load(f)
        page_num = task.get('page_num', 0)
        task_type = task.get('task_type', '')
        if page_num not in content['pages']:
            content['pages'][page_num] = {'text_blocks': [], 'tables': []}
        if task_type == 'text_block':
            content['pages'][page_num]['text_blocks'].append(translated)
        elif task_type == 'table':
            content['pages'][page_num]['tables'].append(translated)
    return content


def generate_frontmatter(metadata: Dict, manifest: Dict) -> str:
    project = manifest.get('project', {})
    title = metadata.get('title', '') if metadata else ''
    author = metadata.get('author', '') if metadata else ''
    lines = [
        '---',
        f'title: "{title}"',
        f'author: "{author}"',
        f'source_language: {project.get("source_language", "unknown")}',
        f'target_language: {project.get("target_language", "ko")}',
        f'translated_date: {datetime.now().strftime("%Y-%m-%d")}',
        f'source_file: {os.path.basename(project.get("source_file", ""))}',
        '---',
        ''
    ]
    return '\n'.join(lines)


def generate_table_of_contents(metadata: Dict) -> str:
    if not metadata or not metadata.get('bookmarks'):
        return ''
    lines = ['## 목차\n']
    for bookmark in metadata.get('bookmarks', []):
        level = bookmark.get('level', 1)
        title = bookmark.get('title', '')
        page = bookmark.get('page', 0)
        indent = '  ' * (level - 1)
        lines.append(f'{indent}- [{title}](#page-{page})')
    lines.append('')
    return '\n'.join(lines)


def format_text_block(block: Dict) -> str:
    text = block.get('text', '')
    if not text:
        return ''
    if block.get('is_heading', False):
        return f'\n## {text}\n'
    return f'\n{text}\n'


def format_table(table: Dict) -> str:
    if 'markdown' in table:
        return f'\n{table["markdown"]}\n'
    data = table.get('data', [])
    if not data:
        return ''
    lines = []
    if len(data) > 0:
        header = data[0]
        lines.append('| ' + ' | '.join(str(cell) for cell in header) + ' |')
        lines.append('|' + '|'.join(['---'] * len(header)) + '|')
    for row in data[1:]:
        lines.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')
    return '\n' + '\n'.join(lines) + '\n'


def generate_page_content(page_num: int, page_data: Dict) -> str:
    lines = [f'\n<a id="page-{page_num}"></a>']
    text_blocks = sorted(page_data.get('text_blocks', []), key=lambda b: b.get('block_index', 0))
    tables = sorted(page_data.get('tables', []), key=lambda t: t.get('table_index', 0))
    for block in text_blocks:
        formatted = format_text_block(block)
        if formatted:
            lines.append(formatted)
    for table in tables:
        formatted = format_table(table)
        if formatted:
            lines.append(formatted)
    return ''.join(lines)


def generate_markdown(content: Dict, manifest: Dict) -> str:
    parts = [generate_frontmatter(content.get('metadata'), manifest)]
    if content.get('metadata') and content['metadata'].get('title'):
        parts.append(f'# {content["metadata"]["title"]}\n')
    toc = generate_table_of_contents(content.get('metadata'))
    if toc:
        parts.append(toc)
    pages = content.get('pages', {})
    for page_num in sorted(pages.keys()):
        if page_num == 0:
            continue
        page_content = generate_page_content(page_num, pages[page_num])
        if page_content.strip():
            parts.append(page_content)
    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(description='Generate Markdown from translated PDF content')
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    manifest_path = args.manifest
    if not os.path.isabs(manifest_path):
        manifest_path = os.path.join(args.work_dir, manifest_path)
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found: {manifest_path}")
        return 1

    manifest = load_manifest(manifest_path)
    print(f"Loading translated content from: {args.work_dir}")
    content = load_translated_content(args.work_dir, manifest)
    print("Generating Markdown...")
    markdown = generate_markdown(content, manifest)

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(markdown)

    page_count = len([p for p in content.get('pages', {}).keys() if p > 0])
    total_blocks = sum(len(p.get('text_blocks', [])) for p in content.get('pages', {}).values())
    total_tables = sum(len(p.get('tables', [])) for p in content.get('pages', {}).values())
    print(f"Saved: {args.output} (Pages: {page_count}, Blocks: {total_blocks}, Tables: {total_tables})")
    return 0


if __name__ == '__main__':
    exit(main())
