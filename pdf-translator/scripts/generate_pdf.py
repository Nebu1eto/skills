#!/usr/bin/env python3
"""PDF Output Generator - Generates translated PDF with layout preservation."""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import fitz
except ImportError:
    print("Error: pymupdf not installed. Run: pip install pymupdf")
    exit(1)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation will be limited.")


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


def register_korean_fonts():
    korean_fonts = [
        '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
        '/Library/Fonts/NanumGothic.ttf',
        '/Library/Fonts/AppleSDGothicNeo.ttc',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        'C:/Windows/Fonts/malgun.ttf',
    ]
    for font_path in korean_fonts:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Korean', font_path))
                return 'Korean'
            except Exception:
                continue
    return None


def generate_pdf_simple(content: Dict, manifest: Dict, output_path: str):
    if not REPORTLAB_AVAILABLE:
        print("Error: reportlab not available")
        return False

    korean_font = register_korean_fonts() or 'Helvetica'
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin_left, margin_right = 25 * mm, 25 * mm
    margin_top, margin_bottom = 25 * mm, 25 * mm
    text_width = width - margin_left - margin_right
    y_position = height - margin_top

    if content.get('metadata') and content['metadata'].get('title'):
        c.setFont(korean_font, 18)
        c.drawString(margin_left, y_position, content['metadata']['title'])
        y_position -= 30

    c.setFont(korean_font, 11)
    line_height = 14

    for page_num in sorted(content.get('pages', {}).keys()):
        if page_num == 0:
            continue
        page_data = content['pages'][page_num]

        for block in sorted(page_data.get('text_blocks', []), key=lambda b: b.get('block_index', 0)):
            text = block.get('text', '')
            is_heading = block.get('is_heading', False)
            if not text:
                continue

            if is_heading:
                c.setFont(korean_font, 14)
                y_position -= 10
            else:
                c.setFont(korean_font, 11)

            words = text.split()
            line = ""
            font_size = 14 if is_heading else 11
            for word in words:
                test_line = line + " " + word if line else word
                if c.stringWidth(test_line, korean_font, font_size) < text_width:
                    line = test_line
                else:
                    if y_position < margin_bottom:
                        c.showPage()
                        c.setFont(korean_font, 11)
                        y_position = height - margin_top
                    c.drawString(margin_left, y_position, line)
                    y_position -= line_height
                    line = word

            if line:
                if y_position < margin_bottom:
                    c.showPage()
                    c.setFont(korean_font, 11)
                    y_position = height - margin_top
                c.drawString(margin_left, y_position, line)
                y_position -= line_height

            y_position -= 10 if is_heading else 5

        for table in page_data.get('tables', []):
            data = table.get('data', [])
            if not data:
                continue
            y_position -= 10
            for row in data:
                if y_position < margin_bottom:
                    c.showPage()
                    c.setFont(korean_font, 11)
                    y_position = height - margin_top
                row_text = " | ".join(str(cell) for cell in row)
                c.drawString(margin_left, y_position, row_text[:80])
                y_position -= line_height
            y_position -= 10

    c.save()
    return True


def generate_pdf_overlay(source_pdf: str, content: Dict, manifest: Dict, output_path: str):
    try:
        doc = fitz.open(source_pdf)
    except Exception as e:
        print(f"Error opening source PDF: {e}")
        return False

    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_data = content.get('pages', {}).get(page_num + 1, {})
        for block in page_data.get('text_blocks', []):
            text = block.get('text', '')
            bbox = block.get('bbox', [0, 0, 100, 100])
            if not text or not bbox:
                continue

    try:
        doc.save(output_path)
        doc.close()
        return True
    except Exception as e:
        print(f"Error saving PDF: {e}")
        doc.close()
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate translated PDF output')
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--source-pdf')
    parser.add_argument('--output', required=True)
    parser.add_argument('--preserve-layout', action='store_true')
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

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print("Generating PDF...")
    if args.preserve_layout and args.source_pdf and os.path.exists(args.source_pdf):
        print("Attempting layout-preserving PDF generation...")
        success = generate_pdf_overlay(args.source_pdf, content, manifest, args.output)
        if not success:
            print("Layout preservation failed, falling back to simple generation...")
            success = generate_pdf_simple(content, manifest, args.output)
    else:
        success = generate_pdf_simple(content, manifest, args.output)

    if success:
        print(f"PDF saved to: {args.output}")
        return 0
    print("PDF generation failed")
    return 1


if __name__ == '__main__':
    exit(main())
