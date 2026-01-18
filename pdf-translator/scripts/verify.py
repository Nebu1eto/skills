#!/usr/bin/env python3
"""Translation Verification - Checks translation quality and completeness."""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

LANGUAGE_RANGES = {
    'ja': {'hiragana': ('\u3040', '\u309F'), 'katakana': ('\u30A0', '\u30FF'), 'kanji': ('\u4E00', '\u9FFF')},
    'zh': {'cjk_unified': ('\u4E00', '\u9FFF'), 'cjk_ext_a': ('\u3400', '\u4DBF')},
    'ko': {'hangul_syllables': ('\uAC00', '\uD7AF'), 'hangul_jamo': ('\u1100', '\u11FF')},
    'ru': {'cyrillic': ('\u0400', '\u04FF')},
    'ar': {'arabic': ('\u0600', '\u06FF')},
    'he': {'hebrew': ('\u0590', '\u05FF')},
    'th': {'thai': ('\u0E00', '\u0E7F')},
}


def count_language_chars(text: str, lang: str) -> Dict[str, int]:
    if lang not in LANGUAGE_RANGES:
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


def verify_json_file(file_path: str) -> Tuple[bool, str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'text' not in data and 'data' not in data:
            return False, "Missing 'text' or 'data' field"
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"
    except Exception as e:
        return False, str(e)


def verify_translation(file_path: str, source_lang: str, target_lang: str) -> Dict:
    report = {
        'file': file_path,
        'valid_json': False,
        'source_chars_found': 0,
        'target_chars_found': 0,
        'issues': [],
        'passed': True
    }

    is_valid, error = verify_json_file(file_path)
    report['valid_json'] = is_valid
    if not is_valid:
        report['issues'].append(f"Invalid JSON: {error}")
        report['passed'] = False
        return report

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    text = data.get('text', '')
    if 'data' in data:
        text = ' '.join(' '.join(str(cell) for cell in row) for row in data['data'])

    source_counts = count_language_chars(text, source_lang)
    report['source_chars_found'] = source_counts.get('total', 0)
    if report['source_chars_found'] > 0:
        report['issues'].append(f"Found {report['source_chars_found']} source language characters")
        if report['source_chars_found'] > 50:
            report['passed'] = False

    target_counts = count_language_chars(text, target_lang)
    report['target_chars_found'] = target_counts.get('total', 0)
    if len(text) > 20 and report['target_chars_found'] == 0 and source_lang != target_lang:
        report['issues'].append("No target language characters found")

    return report


def verify_directory(work_dir: str, source_lang: str, target_lang: str) -> Dict:
    translated_dir = os.path.join(work_dir, 'translated')
    if not os.path.exists(translated_dir):
        return {'error': f"Translated directory not found: {translated_dir}", 'passed': False}

    full_report = {
        'source_lang': source_lang,
        'target_lang': target_lang,
        'files': [],
        'summary': {
            'total_files': 0,
            'passed_files': 0,
            'failed_files': 0,
            'total_source_chars': 0,
            'total_target_chars': 0
        }
    }

    for json_file in Path(translated_dir).glob('*.json'):
        full_report['summary']['total_files'] += 1
        file_report = verify_translation(str(json_file), source_lang, target_lang)
        full_report['files'].append(file_report)
        full_report['summary']['total_source_chars'] += file_report['source_chars_found']
        full_report['summary']['total_target_chars'] += file_report['target_chars_found']
        if file_report['passed']:
            full_report['summary']['passed_files'] += 1
        else:
            full_report['summary']['failed_files'] += 1

    full_report['passed'] = full_report['summary']['failed_files'] == 0
    return full_report


def print_report(report: Dict):
    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)

    if 'error' in report:
        print(f"\nError: {report['error']}")
        return

    summary = report['summary']
    print(f"\nSource: {report['source_lang']} -> Target: {report['target_lang']}")
    print(f"Files: {summary['passed_files']}/{summary['total_files']} passed")
    print(f"Remaining source chars: {summary['total_source_chars']}")
    print(f"Target chars found: {summary['total_target_chars']}")

    if summary['total_source_chars'] == 0:
        print("\n✅ All source text has been translated!")
    else:
        print("\n⚠️  Some source text may remain")

    failed_files = [f for f in report['files'] if not f['passed']]
    if failed_files:
        print(f"\nFiles with issues ({len(failed_files)}):")
        for f in failed_files[:10]:
            print(f"  - {os.path.basename(f['file'])}")
            for issue in f['issues'][:3]:
                print(f"    · {issue}")
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Verify translated PDF content')
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--source-lang', default='ja')
    parser.add_argument('--target-lang', default='ko')
    parser.add_argument('--manifest')
    parser.add_argument('--output-report')
    args = parser.parse_args()

    source_lang, target_lang = args.source_lang, args.target_lang
    if args.manifest:
        manifest_path = args.manifest
        if not os.path.isabs(manifest_path):
            manifest_path = os.path.join(args.work_dir, manifest_path)
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            source_lang = manifest.get('project', {}).get('source_language', source_lang)
            target_lang = manifest.get('project', {}).get('target_language', target_lang)

    print(f"Verifying translations in: {args.work_dir}")
    report = verify_directory(args.work_dir, source_lang, target_lang)
    print_report(report)

    if args.output_report:
        with open(args.output_report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {args.output_report}")

    return 0 if report.get('passed', False) else 1


if __name__ == '__main__':
    exit(main())
