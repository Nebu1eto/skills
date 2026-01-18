#!/usr/bin/env python3
"""
Translation Verification Script

Verifies translated EPUB files for quality:
- Checks for remaining source language characters
- Validates XML structure
- Verifies metadata changes
"""

import argparse
import json
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET


# Unicode ranges for different languages
LANGUAGE_RANGES = {
    'ja': {
        'hiragana': ('\u3040', '\u309F'),
        'katakana': ('\u30A0', '\u30FF'),
        'kanji': ('\u4E00', '\u9FFF'),
    },
    'zh': {
        'cjk_unified': ('\u4E00', '\u9FFF'),
        'cjk_ext_a': ('\u3400', '\u4DBF'),
    },
    'ko': {
        'hangul_syllables': ('\uAC00', '\uD7AF'),
        'hangul_jamo': ('\u1100', '\u11FF'),
    },
    'ru': {
        'cyrillic': ('\u0400', '\u04FF'),
    },
    'ar': {
        'arabic': ('\u0600', '\u06FF'),
    },
    'th': {
        'thai': ('\u0E00', '\u0E7F'),
    },
    'vi': {
        # Vietnamese uses Latin with diacritics - harder to detect
        'latin_ext': ('\u1E00', '\u1EFF'),
    },
}


def count_language_chars(text: str, lang: str) -> dict:
    """
    Count characters from a specific language in text.

    Args:
        text: Text to analyze
        lang: Language code (ja, zh, ko, ru, ar, th, vi, en)

    Returns:
        Dictionary with character counts by type
    """
    if lang not in LANGUAGE_RANGES:
        # For languages like English that use basic Latin
        return {'total': 0}

    ranges = LANGUAGE_RANGES[lang]
    counts = {}
    total = 0

    for range_name, (start, end) in ranges.items():
        count = sum(1 for c in text if start <= c <= end)
        counts[range_name] = count
        total += count

    counts['total'] = total
    return counts


def validate_xml(file_path: str) -> tuple:
    """
    Validate XML structure of a file.

    Returns:
        (is_valid, error_message)
    """
    try:
        ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        return False, str(e)


def check_language_attribute(file_path: str, target_lang: str) -> bool:
    """Check if xml:lang attribute is set to target language."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for xml:lang attribute
        pattern = rf'xml:lang="{target_lang}"'
        return bool(re.search(pattern, content))
    except Exception:
        return False


def check_writing_mode(css_path: str) -> tuple:
    """
    Check writing-mode in CSS file.

    Returns:
        (is_horizontal, writing_mode_value)
    """
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for writing-mode property
        match = re.search(r'writing-mode:\s*([^;]+)', content)
        if match:
            mode = match.group(1).strip()
            is_horizontal = 'horizontal' in mode or mode == 'lr-tb'
            return is_horizontal, mode

        return True, 'not specified (default horizontal)'
    except Exception:
        return True, 'file not found'


def check_page_direction(opf_path: str) -> tuple:
    """
    Check page-progression-direction in content.opf.

    Returns:
        (is_ltr, direction_value)
    """
    try:
        with open(opf_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'page-progression-direction="([^"]+)"', content)
        if match:
            direction = match.group(1)
            return direction == 'ltr', direction

        return True, 'not specified (default ltr)'
    except Exception:
        return True, 'file not found'


def verify_volume(volume_dir: str, source_lang: str, target_lang: str) -> dict:
    """
    Verify a translated volume.

    Returns:
        Verification report dictionary
    """
    report = {
        'volume_dir': volume_dir,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'files_checked': 0,
        'files_with_source_chars': [],
        'xml_errors': [],
        'lang_attr_issues': [],
        'total_source_chars': 0,
        'passed': True
    }

    # Find XHTML files
    xhtml_files = list(Path(volume_dir).rglob('*.xhtml'))

    for xhtml_file in xhtml_files:
        report['files_checked'] += 1
        file_path = str(xhtml_file)
        relative_path = str(xhtml_file.relative_to(volume_dir))

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            report['xml_errors'].append({
                'file': relative_path,
                'error': f'Read error: {e}'
            })
            report['passed'] = False
            continue

        # Check for remaining source language characters
        char_counts = count_language_chars(content, source_lang)
        if char_counts.get('total', 0) > 0:
            report['files_with_source_chars'].append({
                'file': relative_path,
                'counts': char_counts
            })
            report['total_source_chars'] += char_counts['total']
            report['passed'] = False

        # Validate XML
        is_valid, error = validate_xml(file_path)
        if not is_valid:
            report['xml_errors'].append({
                'file': relative_path,
                'error': error
            })
            report['passed'] = False

        # Check language attribute
        if not check_language_attribute(file_path, target_lang):
            report['lang_attr_issues'].append(relative_path)

    # Check CSS writing-mode (for Japanese source)
    css_files = list(Path(volume_dir).rglob('*.css'))
    for css_file in css_files:
        is_horizontal, mode = check_writing_mode(str(css_file))
        if not is_horizontal and source_lang == 'ja':
            report['writing_mode_issue'] = {
                'file': str(css_file.relative_to(volume_dir)),
                'current_mode': mode
            }
            report['passed'] = False

    # Check content.opf page direction
    opf_files = list(Path(volume_dir).rglob('*.opf'))
    for opf_file in opf_files:
        is_ltr, direction = check_page_direction(str(opf_file))
        if not is_ltr and source_lang == 'ja':
            report['page_direction_issue'] = {
                'file': str(opf_file.relative_to(volume_dir)),
                'current_direction': direction
            }
            report['passed'] = False

    return report


def verify_from_manifest(manifest_path: str, work_dir: str) -> dict:
    """
    Verify all volumes from manifest.

    Returns:
        Complete verification report
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    source_lang = manifest['project']['source_language']
    target_lang = manifest['project']['target_language']

    full_report = {
        'source_lang': source_lang,
        'target_lang': target_lang,
        'volumes': [],
        'summary': {
            'total_volumes': 0,
            'passed_volumes': 0,
            'total_files': 0,
            'files_with_issues': 0,
            'total_source_chars': 0
        }
    }

    for volume in manifest.get('volumes', []):
        volume_id = volume['volume_id']
        translated_dir = os.path.join(work_dir, 'translated', volume_id)

        if not os.path.exists(translated_dir):
            # Try original extracted location
            translated_dir = volume['work_dir']

        print(f"Verifying: {volume_id}")
        report = verify_volume(translated_dir, source_lang, target_lang)
        report['volume_id'] = volume_id

        full_report['volumes'].append(report)
        full_report['summary']['total_volumes'] += 1
        full_report['summary']['total_files'] += report['files_checked']
        full_report['summary']['total_source_chars'] += report['total_source_chars']

        if report['passed']:
            full_report['summary']['passed_volumes'] += 1
        else:
            full_report['summary']['files_with_issues'] += len(report['files_with_source_chars'])

    return full_report


def print_report(report: dict):
    """Print verification report to console."""
    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)

    summary = report['summary']
    print(f"\nSource Language: {report['source_lang']}")
    print(f"Target Language: {report['target_lang']}")
    print(f"\nVolumes: {summary['passed_volumes']}/{summary['total_volumes']} passed")
    print(f"Files checked: {summary['total_files']}")
    print(f"Remaining source characters: {summary['total_source_chars']}")

    if summary['total_source_chars'] == 0:
        print("\n✅ All source text has been translated!")
    else:
        print(f"\n⚠️  {summary['files_with_issues']} file(s) still contain source text")

    for vol_report in report['volumes']:
        print(f"\n--- {vol_report.get('volume_id', 'Unknown')} ---")

        if vol_report['passed']:
            print("  ✅ Passed")
        else:
            print("  ❌ Issues found:")

            if vol_report['files_with_source_chars']:
                print(f"    - {len(vol_report['files_with_source_chars'])} file(s) with source chars")
                for item in vol_report['files_with_source_chars'][:5]:
                    print(f"      · {item['file']}: {item['counts']['total']} chars")

            if vol_report['xml_errors']:
                print(f"    - {len(vol_report['xml_errors'])} XML error(s)")

            if vol_report.get('writing_mode_issue'):
                print(f"    - Writing mode not horizontal")

            if vol_report.get('page_direction_issue'):
                print(f"    - Page direction not LTR")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Verify translated EPUB files')
    parser.add_argument('--work-dir', required=True, help='Work directory')
    parser.add_argument('--source-lang', default='ja', help='Source language code')
    parser.add_argument('--target-lang', default='ko', help='Target language code')
    parser.add_argument('--manifest', help='Manifest file path')
    parser.add_argument('--output-report', help='Output report file (JSON)')
    parser.add_argument('--volume-dir', help='Single volume directory to verify')

    args = parser.parse_args()

    # Single volume mode
    if args.volume_dir:
        report = verify_volume(args.volume_dir, args.source_lang, args.target_lang)
        full_report = {
            'source_lang': args.source_lang,
            'target_lang': args.target_lang,
            'volumes': [report],
            'summary': {
                'total_volumes': 1,
                'passed_volumes': 1 if report['passed'] else 0,
                'total_files': report['files_checked'],
                'files_with_issues': len(report['files_with_source_chars']),
                'total_source_chars': report['total_source_chars']
            }
        }
    # Manifest mode
    elif args.manifest:
        full_report = verify_from_manifest(args.manifest, args.work_dir)
    else:
        # Auto-detect manifest
        manifest_path = os.path.join(args.work_dir, 'manifest.json')
        if os.path.exists(manifest_path):
            full_report = verify_from_manifest(manifest_path, args.work_dir)
        else:
            print("Error: No manifest found. Specify --manifest or --volume-dir")
            return 1

    # Print report
    print_report(full_report)

    # Save report if requested
    if args.output_report:
        with open(args.output_report, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {args.output_report}")

    # Return exit code based on pass/fail
    return 0 if full_report['summary']['total_source_chars'] == 0 else 1


if __name__ == '__main__':
    exit(main())
