#!/usr/bin/env python3
"""
EPUB Analyzer

Analyzes EPUB files and generates a work manifest for translation.
Handles multiple EPUBs, identifies large files for splitting, and creates
a comprehensive task list for parallel processing.
"""

import argparse
import json
import os
import re
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET


# File size thresholds (in KB) - Conservative defaults
DEFAULT_SPLIT_THRESHOLD = 30  # Files larger than this will be split
MEDIUM_FILE_THRESHOLD = 15

# Number of sections to split large files into
DEFAULT_SPLIT_PARTS = 4

# Global config (set by command line args)
CONFIG = {
    'split_threshold': DEFAULT_SPLIT_THRESHOLD,
    'split_parts': DEFAULT_SPLIT_PARTS
}


@dataclass
class Task:
    """Represents a single translation task."""
    task_id: str
    volume_id: str
    task_type: str  # 'single' or 'section'
    input_path: str
    output_path: str
    status_path: str
    size_kb: float
    parent_file: Optional[str] = None
    section_index: Optional[int] = None
    total_sections: Optional[int] = None


@dataclass
class Volume:
    """Represents an EPUB volume."""
    volume_id: str
    source_epub: str
    title: str
    work_dir: str
    tasks: list


@dataclass
class Manifest:
    """Work manifest for the translation project."""
    project: dict
    dictionaries: dict
    volumes: list
    statistics: dict


def extract_epub(epub_path: str, extract_dir: str) -> bool:
    """Extract EPUB file to directory."""
    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        return True
    except Exception as e:
        print(f"Error extracting {epub_path}: {e}")
        return False


def get_epub_title(extract_dir: str) -> str:
    """Extract title from EPUB metadata."""
    opf_files = list(Path(extract_dir).rglob("*.opf"))
    if not opf_files:
        return "Unknown"

    try:
        tree = ET.parse(opf_files[0])
        root = tree.getroot()

        # Handle namespace
        ns = {'dc': 'http://purl.org/dc/elements/1.1/',
              'opf': 'http://www.idpf.org/2007/opf'}

        title_elem = root.find('.//{http://purl.org/dc/elements/1.1/}title')
        if title_elem is not None and title_elem.text:
            return title_elem.text
    except Exception:
        pass

    return Path(extract_dir).name


def find_xhtml_files(extract_dir: str) -> list:
    """Find all XHTML files in extracted EPUB."""
    xhtml_files = []

    # Common EPUB content directories
    for pattern in ["OEBPS/*.xhtml", "OEBPS/**/*.xhtml",
                    "OPS/*.xhtml", "OPS/**/*.xhtml",
                    "*.xhtml", "**/*.xhtml"]:
        xhtml_files.extend(Path(extract_dir).glob(pattern))

    # Remove duplicates and sort by size (descending)
    xhtml_files = list(set(xhtml_files))
    xhtml_files.sort(key=lambda f: f.stat().st_size, reverse=True)

    return xhtml_files


def analyze_file(file_path: Path) -> dict:
    """Analyze a single XHTML file."""
    size_bytes = file_path.stat().st_size
    size_kb = size_bytes / 1024

    # Count paragraphs for splitting estimation
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        paragraph_count = len(re.findall(r'<p[^>]*>.*?</p>', content, re.DOTALL))
    except Exception:
        paragraph_count = 0

    return {
        'path': str(file_path),
        'size_kb': round(size_kb, 2),
        'paragraph_count': paragraph_count,
        'needs_split': size_kb >= CONFIG['split_threshold']
    }


def split_large_file(file_path: str, output_dir: str, num_parts: int = DEFAULT_SPLIT_PARTS) -> list:
    """
    Split a large XHTML file into multiple sections.
    Returns list of section file paths.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract header and footer
    header_match = re.match(r'(.*?<body[^>]*>)', content, re.DOTALL)
    footer_match = re.search(r'(</body>\s*</html>)', content, re.DOTALL)

    if not header_match or not footer_match:
        print(f"Warning: Could not parse structure of {file_path}")
        return []

    header = header_match.group(1)
    footer = footer_match.group(1)

    body_start = header_match.end()
    body_end = footer_match.start()
    body_content = content[body_start:body_end]

    # Split by paragraphs
    paragraphs = re.findall(r'<p[^>]*>.*?</p>', body_content, re.DOTALL)

    if len(paragraphs) < num_parts:
        num_parts = max(1, len(paragraphs))

    part_size = len(paragraphs) // num_parts
    section_files = []

    basename = Path(file_path).stem
    os.makedirs(output_dir, exist_ok=True)

    for i in range(num_parts):
        start_idx = i * part_size
        end_idx = len(paragraphs) if i == num_parts - 1 else (i + 1) * part_size

        part_content = header + '\n' + '\n'.join(paragraphs[start_idx:end_idx]) + '\n' + footer
        output_path = os.path.join(output_dir, f"{basename}_part{i+1}.xhtml")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(part_content)

        section_files.append(output_path)

    return section_files


def create_tasks_for_volume(volume_id: str, extract_dir: str, work_dir: str,
                           sections_dir: str, status_dir: str) -> list:
    """Create translation tasks for a volume."""
    tasks = []
    xhtml_files = find_xhtml_files(extract_dir)

    for xhtml_file in xhtml_files:
        file_info = analyze_file(xhtml_file)
        relative_path = xhtml_file.relative_to(extract_dir)

        if file_info['needs_split']:
            # Split large file
            section_files = split_large_file(
                str(xhtml_file),
                os.path.join(sections_dir, volume_id),
                CONFIG['split_parts']
            )

            for idx, section_file in enumerate(section_files):
                task_id = f"{volume_id}_{xhtml_file.stem}_p{idx+1}"
                section_basename = os.path.basename(section_file)

                tasks.append(Task(
                    task_id=task_id,
                    volume_id=volume_id,
                    task_type='section',
                    input_path=section_file,
                    output_path=os.path.join(sections_dir, volume_id, f"translated_{section_basename}"),
                    status_path=os.path.join(status_dir, f"{task_id}.status"),
                    size_kb=round(file_info['size_kb'] / len(section_files), 2),
                    parent_file=str(relative_path),
                    section_index=idx + 1,
                    total_sections=len(section_files)
                ))
        else:
            # Single file task
            task_id = f"{volume_id}_{xhtml_file.stem}"

            tasks.append(Task(
                task_id=task_id,
                volume_id=volume_id,
                task_type='single',
                input_path=str(xhtml_file),
                output_path=os.path.join(work_dir, 'translated', volume_id, str(relative_path)),
                status_path=os.path.join(status_dir, f"{task_id}.status"),
                size_kb=file_info['size_kb']
            ))

    return tasks


def load_dictionary(dict_path: str) -> dict:
    """Load custom dictionary file."""
    if not dict_path or not os.path.exists(dict_path):
        return {'characters': {}, 'terms': {}}

    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load dictionary {dict_path}: {e}")
        return {'characters': {}, 'terms': {}}


def analyze_epub(epub_path: str, work_dir: str, source_lang: str,
                dict_path: Optional[str] = None) -> Optional[Volume]:
    """Analyze a single EPUB and create volume info."""

    # Generate volume ID from filename
    volume_id = Path(epub_path).stem
    volume_id = re.sub(r'[^\w\-]', '_', volume_id)[:50]  # Sanitize and limit length

    # Extract EPUB
    extract_dir = os.path.join(work_dir, 'extracted', volume_id)
    os.makedirs(extract_dir, exist_ok=True)

    if not extract_epub(epub_path, extract_dir):
        return None

    # Get title
    title = get_epub_title(extract_dir)

    # Create tasks
    tasks = create_tasks_for_volume(
        volume_id=volume_id,
        extract_dir=extract_dir,
        work_dir=work_dir,
        sections_dir=os.path.join(work_dir, 'sections'),
        status_dir=os.path.join(work_dir, 'status')
    )

    return Volume(
        volume_id=volume_id,
        source_epub=epub_path,
        title=title,
        work_dir=extract_dir,
        tasks=tasks
    )


def main():
    parser = argparse.ArgumentParser(description='Analyze EPUB files for translation')
    parser.add_argument('--epub', required=True, help='EPUB file or directory path')
    parser.add_argument('--work-dir', required=True, help='Work directory')
    parser.add_argument('--source-lang', default='ja',
                       help='Source language (default: ja)')
    parser.add_argument('--target-lang', default='ko',
                       help='Target language (default: ko)')
    parser.add_argument('--dict', help='Custom dictionary file (JSON)')
    parser.add_argument('--output-manifest', help='Output manifest path')
    parser.add_argument('--split-threshold', type=int, default=DEFAULT_SPLIT_THRESHOLD,
                       help=f'File size threshold for splitting in KB (default: {DEFAULT_SPLIT_THRESHOLD})')
    parser.add_argument('--split-parts', type=int, default=DEFAULT_SPLIT_PARTS,
                       help=f'Number of parts to split large files into (default: {DEFAULT_SPLIT_PARTS})')

    args = parser.parse_args()

    # Update global config
    CONFIG['split_threshold'] = args.split_threshold
    CONFIG['split_parts'] = args.split_parts

    print(f"Configuration:")
    print(f"  Split threshold: {CONFIG['split_threshold']} KB")
    print(f"  Split parts: {CONFIG['split_parts']}")
    print()

    # Find EPUB files
    epub_path = Path(args.epub)
    if epub_path.is_file():
        epub_files = [str(epub_path)]
    elif epub_path.is_dir():
        epub_files = [str(f) for f in epub_path.glob('*.epub')]
    else:
        print(f"Error: {args.epub} is not a valid file or directory")
        return 1

    if not epub_files:
        print(f"Error: No EPUB files found in {args.epub}")
        return 1

    # Create work directory structure
    work_dir = args.work_dir
    for subdir in ['extracted', 'sections', 'translated', 'status', 'logs']:
        os.makedirs(os.path.join(work_dir, subdir), exist_ok=True)

    # Load dictionary
    dictionaries = load_dictionary(args.dict)

    # Analyze each EPUB
    volumes = []
    total_tasks = 0
    single_count = 0
    section_count = 0

    for epub_file in epub_files:
        print(f"Analyzing: {epub_file}")
        volume = analyze_epub(epub_file, work_dir, args.source_lang, args.dict)

        if volume:
            volumes.append(volume)
            for task in volume.tasks:
                total_tasks += 1
                if task.task_type == 'single':
                    single_count += 1
                else:
                    section_count += 1

    # Create manifest
    manifest = Manifest(
        project={
            'source_language': args.source_lang,
            'target_language': args.target_lang,
            'work_dir': work_dir,
            'split_threshold_kb': CONFIG['split_threshold'],
            'split_parts': CONFIG['split_parts'],
            'created_at': datetime.now().isoformat()
        },
        dictionaries=dictionaries,
        volumes=[{
            'volume_id': v.volume_id,
            'source_epub': v.source_epub,
            'title': v.title,
            'work_dir': v.work_dir,
            'tasks': [asdict(t) for t in v.tasks]
        } for v in volumes],
        statistics={
            'total_volumes': len(volumes),
            'total_tasks': total_tasks,
            'single_file_tasks': single_count,
            'section_tasks': section_count,
            'completed': 0,
            'in_progress': 0,
            'failed': 0
        }
    )

    # Save manifest
    manifest_path = args.output_manifest or os.path.join(work_dir, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(manifest), f, indent=2, ensure_ascii=False)

    print(f"\nAnalysis complete!")
    print(f"  Volumes: {len(volumes)}")
    print(f"  Total tasks: {total_tasks}")
    print(f"    - Single files: {single_count}")
    print(f"    - Split sections: {section_count}")
    print(f"  Manifest saved to: {manifest_path}")

    return 0


if __name__ == '__main__':
    exit(main())
