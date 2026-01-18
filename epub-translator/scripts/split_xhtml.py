#!/usr/bin/env python3
"""
XHTML File Splitter

Splits large XHTML files into smaller sections for parallel translation.
Preserves XML structure and allows clean merging after translation.
"""

import argparse
import os
import re
from pathlib import Path


def split_xhtml_file(input_path: str, output_dir: str, num_parts: int = 4) -> list:
    """
    Split an XHTML file into multiple parts.

    Args:
        input_path: Path to the XHTML file to split
        output_dir: Directory to save split files
        num_parts: Number of parts to split into

    Returns:
        List of paths to created section files
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract XML declaration and doctype if present
    xml_decl = ''
    doctype = ''

    xml_match = re.match(r'(<\?xml[^?]*\?>)\s*', content)
    if xml_match:
        xml_decl = xml_match.group(1)
        content = content[xml_match.end():]

    doctype_match = re.match(r'(<!DOCTYPE[^>]*>)\s*', content)
    if doctype_match:
        doctype = doctype_match.group(1)
        content = content[doctype_match.end():]

    # Extract header (html tag to body opening)
    header_match = re.match(r'(.*?<body[^>]*>)', content, re.DOTALL)
    if not header_match:
        print(f"Error: Could not find <body> tag in {input_path}")
        return []

    # Extract footer (body closing to end)
    footer_match = re.search(r'(</body>\s*</html>\s*)$', content, re.DOTALL)
    if not footer_match:
        print(f"Error: Could not find </body></html> in {input_path}")
        return []

    header = header_match.group(1)
    footer = footer_match.group(1)

    # Extract body content
    body_start = header_match.end()
    body_end = footer_match.start()
    body_content = content[body_start:body_end]

    # Find all paragraphs and block elements
    # This regex captures paragraphs and other block elements
    block_pattern = r'(<(?:p|div|h[1-6]|blockquote|ul|ol|table|section|article)[^>]*>.*?</(?:p|div|h[1-6]|blockquote|ul|ol|table|section|article)>)'
    blocks = re.findall(block_pattern, body_content, re.DOTALL)

    if not blocks:
        # Fallback: split by any tags
        blocks = re.findall(r'(<[^/][^>]*>.*?</[^>]+>)', body_content, re.DOTALL)

    if len(blocks) == 0:
        print(f"Warning: No block elements found in {input_path}")
        return []

    # Adjust num_parts if we have fewer blocks
    if len(blocks) < num_parts:
        num_parts = max(1, len(blocks))

    part_size = len(blocks) // num_parts
    section_files = []

    basename = Path(input_path).stem
    os.makedirs(output_dir, exist_ok=True)

    # Build prefix (XML declaration + doctype)
    prefix = ''
    if xml_decl:
        prefix += xml_decl + '\n'
    if doctype:
        prefix += doctype + '\n'

    for i in range(num_parts):
        start_idx = i * part_size
        end_idx = len(blocks) if i == num_parts - 1 else (i + 1) * part_size

        part_blocks = blocks[start_idx:end_idx]
        part_body = '\n'.join(part_blocks)

        # Construct complete XHTML
        part_content = f"{prefix}{header}\n{part_body}\n{footer}"

        output_path = os.path.join(output_dir, f"{basename}_part{i+1}.xhtml")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(part_content)

        section_files.append(output_path)
        print(f"  Created: {output_path} ({len(part_blocks)} blocks)")

    return section_files


def main():
    parser = argparse.ArgumentParser(description='Split large XHTML files')
    parser.add_argument('--input', '-i', required=True, help='Input XHTML file')
    parser.add_argument('--output-dir', '-o', required=True, help='Output directory')
    parser.add_argument('--parts', '-n', type=int, default=4, help='Number of parts')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1

    print(f"Splitting {args.input} into {args.parts} parts...")
    sections = split_xhtml_file(args.input, args.output_dir, args.parts)

    if sections:
        print(f"\nSuccessfully created {len(sections)} section(s)")
        return 0
    else:
        print("\nFailed to split file")
        return 1


if __name__ == '__main__':
    exit(main())
