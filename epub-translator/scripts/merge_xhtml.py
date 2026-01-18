#!/usr/bin/env python3
"""
XHTML File Merger

Merges translated section files back into complete XHTML files.
Reconstructs the original file structure after parallel translation.
"""

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path


def merge_xhtml_sections(section_files: list, output_path: str) -> bool:
    """
    Merge multiple XHTML section files into one.

    Args:
        section_files: List of section file paths (in order)
        output_path: Path to save merged file

    Returns:
        True if successful, False otherwise
    """
    if not section_files:
        print("Error: No section files provided")
        return False

    # Sort section files by part number
    def get_part_num(path):
        match = re.search(r'_part(\d+)\.xhtml$', path)
        return int(match.group(1)) if match else 0

    section_files = sorted(section_files, key=get_part_num)

    # Read first file to get header and footer structure
    with open(section_files[0], 'r', encoding='utf-8') as f:
        first_content = f.read()

    # Extract XML declaration and doctype
    prefix = ''
    content = first_content

    xml_match = re.match(r'(<\?xml[^?]*\?>)\s*', content)
    if xml_match:
        prefix += xml_match.group(1) + '\n'
        content = content[xml_match.end():]

    doctype_match = re.match(r'(<!DOCTYPE[^>]*>)\s*', content)
    if doctype_match:
        prefix += doctype_match.group(1) + '\n'
        content = content[doctype_match.end():]

    # Extract header
    header_match = re.match(r'(.*?<body[^>]*>)', content, re.DOTALL)
    if not header_match:
        print(f"Error: Could not find <body> tag in {section_files[0]}")
        return False

    # Extract footer
    footer_match = re.search(r'(</body>\s*</html>\s*)$', first_content, re.DOTALL)
    if not footer_match:
        print(f"Error: Could not find </body></html> in {section_files[0]}")
        return False

    header = header_match.group(1)
    footer = footer_match.group(1)

    # Collect body content from all sections
    all_body_content = []

    for section_file in section_files:
        with open(section_file, 'r', encoding='utf-8') as f:
            section_content = f.read()

        # Extract body content
        body_start = re.search(r'<body[^>]*>', section_content)
        body_end = re.search(r'</body>', section_content)

        if body_start and body_end:
            body_content = section_content[body_start.end():body_end.start()]
            all_body_content.append(body_content.strip())

    # Merge all content
    merged_body = '\n\n'.join(all_body_content)
    merged_content = f"{prefix}{header}\n{merged_body}\n{footer}"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write merged file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)

    return True


def process_manifest(manifest_path: str, work_dir: str) -> int:
    """
    Process manifest and merge all split files.

    Args:
        manifest_path: Path to manifest.json
        work_dir: Work directory

    Returns:
        Number of files merged
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    merged_count = 0

    for volume in manifest.get('volumes', []):
        volume_id = volume['volume_id']
        volume_work_dir = volume['work_dir']

        # Group section tasks by parent file
        sections_by_parent = defaultdict(list)

        for task in volume.get('tasks', []):
            if task['task_type'] == 'section':
                parent_file = task['parent_file']
                sections_by_parent[parent_file].append(task)

        # Merge each group of sections
        for parent_file, section_tasks in sections_by_parent.items():
            # Sort by section index
            section_tasks.sort(key=lambda t: t.get('section_index', 0))

            # Get translated section file paths
            section_files = [t['output_path'] for t in section_tasks]

            # Check all sections are translated
            missing = [f for f in section_files if not os.path.exists(f)]
            if missing:
                print(f"Warning: Missing translated sections for {parent_file}:")
                for m in missing:
                    print(f"  - {m}")
                continue

            # Determine output path (same as original location in translated dir)
            output_path = os.path.join(
                work_dir, 'translated', volume_id, parent_file
            )

            print(f"Merging {len(section_files)} sections -> {output_path}")

            if merge_xhtml_sections(section_files, output_path):
                merged_count += 1
                print(f"  Success!")
            else:
                print(f"  Failed!")

    return merged_count


def main():
    parser = argparse.ArgumentParser(description='Merge translated XHTML sections')
    parser.add_argument('--work-dir', required=True, help='Work directory')
    parser.add_argument('--manifest', required=True, help='Manifest file path')

    # Alternative: merge specific files
    parser.add_argument('--sections', nargs='+', help='Section files to merge (manual mode)')
    parser.add_argument('--output', help='Output file path (manual mode)')

    args = parser.parse_args()

    # Manual mode: merge specific files
    if args.sections and args.output:
        print(f"Merging {len(args.sections)} sections -> {args.output}")
        success = merge_xhtml_sections(args.sections, args.output)
        return 0 if success else 1

    # Auto mode: process manifest
    if not os.path.exists(args.manifest):
        print(f"Error: Manifest not found: {args.manifest}")
        return 1

    print(f"Processing manifest: {args.manifest}")
    merged_count = process_manifest(args.manifest, args.work_dir)

    print(f"\nMerge complete! {merged_count} file(s) merged.")
    return 0


if __name__ == '__main__':
    exit(main())
