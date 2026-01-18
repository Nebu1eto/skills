#!/usr/bin/env python3
"""PDF Analyzer - Extracts content and generates translation manifest."""

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import fitz
except ImportError:
    print("Error: pymupdf not installed. Run: pip install pymupdf")
    exit(1)

try:
    import pdfplumber
except ImportError:
    pdfplumber = None
    print("Warning: pdfplumber not installed. Table extraction will be limited.")

URL_PATTERN = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+|'
    r'www\.[^\s<>"{}|\\^`\[\]]+|'
    r'doi\.org/[^\s<>"{}|\\^`\[\]]+'
)
DOI_PATTERN = re.compile(r'(?:doi:|DOI:?\s*)?10\.\d{4,}/[^\s]+')
CITATION_PATTERN = re.compile(r'\[[\d,\s\-–]+\]|\(\s*[A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4}\s*\)')
EMAIL_PATTERN = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')

LANGUAGE_PATTERNS = {
    'ja': {'hiragana': r'[\u3040-\u309F]', 'katakana': r'[\u30A0-\u30FF]', 'kanji': r'[\u4E00-\u9FFF]'},
    'zh': {'cjk': r'[\u4E00-\u9FFF]'},
    'ko': {'hangul': r'[\uAC00-\uD7AF\u1100-\u11FF]'},
    'ar': {'arabic': r'[\u0600-\u06FF]'},
    'he': {'hebrew': r'[\u0590-\u05FF]'},
    'ru': {'cyrillic': r'[\u0400-\u04FF]'},
}


@dataclass
class TextBlock:
    block_id: str
    page_num: int
    block_index: int
    text: str
    bbox: List[float]
    font_size: float = 0
    is_heading: bool = False


@dataclass
class Table:
    table_id: str
    page_num: int
    table_index: int
    data: List[List[str]]
    bbox: List[float]
    row_count: int = 0
    col_count: int = 0


@dataclass
class Image:
    image_id: str
    page_num: int
    image_index: int
    bbox: List[float]
    width: int
    height: int
    path: str = ""


@dataclass
class PageInfo:
    page_num: int
    width: float
    height: float
    text_blocks: List[TextBlock] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    layout: str = "horizontal"
    num_columns: int = 1


@dataclass
class PDFMetadata:
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = ""
    page_count: int = 0
    bookmarks: List[Dict] = field(default_factory=list)


@dataclass
class Task:
    task_id: str
    task_type: str
    page_num: int
    input_path: str
    output_path: str
    status_path: str
    content_preview: str = ""
    priority: int = 1


@dataclass
class Manifest:
    project: Dict[str, Any]
    pdf_info: Dict[str, Any]
    metadata: Dict[str, Any]
    pages: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    statistics: Dict[str, Any]


def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    text_sample = text[:5000]
    scores = {}
    for lang, patterns in LANGUAGE_PATTERNS.items():
        count = sum(len(re.findall(p, text_sample)) for p in patterns.values())
        scores[lang] = count
    if max(scores.values()) > 10:
        return max(scores, key=scores.get)
    return "en"


def detect_layout(text_blocks: List[TextBlock], page_width: float) -> str:
    if not text_blocks:
        return "horizontal"
    all_text = " ".join([b.text for b in text_blocks])
    arabic_count = len(re.findall(r'[\u0600-\u06FF]', all_text))
    hebrew_count = len(re.findall(r'[\u0590-\u05FF]', all_text))
    if arabic_count > 50 or hebrew_count > 50:
        return "rtl"
    narrow_tall_blocks = sum(
        1 for b in text_blocks
        if (b.bbox[3] - b.bbox[1]) > (b.bbox[2] - b.bbox[0]) * 3
    )
    if narrow_tall_blocks > len(text_blocks) * 0.3:
        return "vertical"
    return "horizontal"


def detect_multi_column(text_blocks: List[TextBlock], page_width: float) -> int:
    if not text_blocks or len(text_blocks) < 4:
        return 1
    x_centers = [(b.bbox[0] + b.bbox[2]) / 2 for b in text_blocks]
    mid_x = page_width / 2
    left_count = sum(1 for x in x_centers if x < mid_x * 0.9)
    right_count = sum(1 for x in x_centers if x > mid_x * 1.1)
    if left_count > 3 and right_count > 3:
        third = page_width / 3
        col1 = sum(1 for x in x_centers if x < third * 1.1)
        col2 = sum(1 for x in x_centers if third * 0.9 < x < third * 2.1)
        col3 = sum(1 for x in x_centers if x > third * 1.9)
        if col1 > 2 and col2 > 2 and col3 > 2:
            return 3
        return 2
    return 1


def fix_hyphenated_words(text: str) -> str:
    """Fix words broken by hyphenation at line endings."""
    result = re.sub(r'(\w+)-\s*\n\s*([a-z])', r'\1\2', text)
    return re.sub(r'(\w+)-\s+([a-z])', r'\1\2', result)


def fix_line_breaks(text: str) -> str:
    """Normalize line breaks within paragraphs."""
    text = re.sub(r'\n\s*\n', '\n\n', text)
    lines = text.split('\n')
    result = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append("")
        elif buffer:
            if buffer[-1] in '.!?:':
                result.append(buffer)
                buffer = line
            else:
                buffer = buffer + " " + line
        else:
            buffer = line
    if buffer:
        result.append(buffer)
    return '\n'.join(result)


def preserve_special_elements(text: str) -> tuple:
    """Extract and preserve URLs, DOIs, emails before processing."""
    preserved = {'urls': [], 'dois': [], 'emails': [], 'citations': []}
    for match in URL_PATTERN.finditer(text):
        url = match.group()
        placeholder = f"__URL_{len(preserved['urls'])}__"
        preserved['urls'].append((placeholder, url))
        text = text.replace(url, placeholder, 1)
    for match in DOI_PATTERN.finditer(text):
        doi = match.group()
        if not doi.startswith('http'):
            placeholder = f"__DOI_{len(preserved['dois'])}__"
            preserved['dois'].append((placeholder, doi))
            text = text.replace(doi, placeholder, 1)
    for match in EMAIL_PATTERN.finditer(text):
        email = match.group()
        placeholder = f"__EMAIL_{len(preserved['emails'])}__"
        preserved['emails'].append((placeholder, email))
        text = text.replace(email, placeholder, 1)
    return text, preserved


def restore_special_elements(text: str, preserved: dict) -> str:
    for key in ['urls', 'dois', 'emails', 'citations']:
        for placeholder, original in preserved.get(key, []):
            text = text.replace(placeholder, original)
    return text


def is_header_footer(text: str, bbox: List[float], page_height: float, page_num: int) -> bool:
    y_top, y_bottom = bbox[1], bbox[3]
    margin = page_height * 0.08
    if y_top < margin or y_bottom > page_height - margin:
        text_lower = text.lower().strip()
        if re.match(r'^[\d\s\-–]+$', text_lower):
            return True
        if len(text) < 50:
            if re.search(r'\b\d+\b', text) and len(text) < 20:
                return True
            if re.match(r'^(page\s*\d+|vol\.?\s*\d+|no\.?\s*\d+)', text_lower):
                return True
    return False


def preprocess_text(text: str) -> str:
    text, preserved = preserve_special_elements(text)
    text = fix_hyphenated_words(text)
    text = fix_line_breaks(text)
    text = restore_special_elements(text, preserved)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def extract_text_blocks(page: fitz.Page, page_num: int, filter_headers: bool = True) -> List[TextBlock]:
    blocks = []
    page_height = page.rect.height
    page_width = page.rect.width
    text_dict = page.get_text("dict")
    raw_blocks = []

    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            lines = block.get("lines", [])
            text_parts = []
            font_sizes = []
            for line in lines:
                for span in line.get("spans", []):
                    text_parts.append(span.get("text", ""))
                    font_sizes.append(span.get("size", 12))
            text = "\n".join(text_parts)
            if not text.strip():
                continue
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
            raw_blocks.append({
                'text': text,
                'bbox': block.get("bbox", [0, 0, 0, 0]),
                'font_size': avg_font_size
            })

    if filter_headers:
        raw_blocks = [
            b for b in raw_blocks
            if not is_header_footer(b['text'], b['bbox'], page_height, page_num)
        ]

    if raw_blocks:
        temp_blocks = [
            TextBlock("", page_num, i, b['text'], b['bbox'], b['font_size'], False)
            for i, b in enumerate(raw_blocks)
        ]
        num_columns = detect_multi_column(temp_blocks, page_width)
        if num_columns > 1:
            col_width = page_width / num_columns
            raw_blocks.sort(key=lambda b: (
                int(((b['bbox'][0] + b['bbox'][2]) / 2) / col_width),
                b['bbox'][1]
            ))

    block_index = 0
    for raw_block in raw_blocks:
        text = preprocess_text(raw_block['text'])
        if not text:
            continue
        avg_font_size = raw_block['font_size']
        is_heading = (
            avg_font_size > 14 or
            (len(text) < 100 and avg_font_size > 12) or
            (len(text) < 80 and text.isupper())
        )
        blocks.append(TextBlock(
            block_id=f"page{page_num:03d}_block{block_index:03d}",
            page_num=page_num,
            block_index=block_index,
            text=text,
            bbox=raw_block['bbox'],
            font_size=avg_font_size,
            is_heading=is_heading
        ))
        block_index += 1
    return blocks


def extract_tables(pdf_path: str, page_num: int, work_dir: str) -> List[Table]:
    if pdfplumber is None:
        return []
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]
                for idx, table_data in enumerate(page.extract_tables()):
                    if not table_data:
                        continue
                    cleaned_data = [[cell if cell else "" for cell in row] for row in table_data]
                    if cleaned_data:
                        tables.append(Table(
                            table_id=f"page{page_num:03d}_table{idx:03d}",
                            page_num=page_num,
                            table_index=idx,
                            data=cleaned_data,
                            bbox=[0, 0, 0, 0],
                            row_count=len(cleaned_data),
                            col_count=len(cleaned_data[0]) if cleaned_data else 0
                        ))
    except Exception as e:
        print(f"Warning: Table extraction failed for page {page_num}: {e}")
    return tables


def extract_images(page: fitz.Page, page_num: int, work_dir: str) -> List[Image]:
    images = []
    image_dir = os.path.join(work_dir, "images")
    os.makedirs(image_dir, exist_ok=True)
    for idx, img in enumerate(page.get_images()):
        try:
            base_image = page.parent.extract_image(img[0])
            if base_image:
                image_path = os.path.join(image_dir, f"page{page_num:03d}_img{idx:03d}.{base_image['ext']}")
                with open(image_path, "wb") as f:
                    f.write(base_image["image"])
                images.append(Image(
                    image_id=f"page{page_num:03d}_img{idx:03d}",
                    page_num=page_num,
                    image_index=idx,
                    bbox=[0, 0, 0, 0],
                    width=base_image.get("width", 0),
                    height=base_image.get("height", 0),
                    path=image_path
                ))
        except Exception as e:
            print(f"Warning: Image extraction failed for page {page_num}, image {idx}: {e}")
    return images


def extract_metadata(doc: fitz.Document) -> PDFMetadata:
    meta = doc.metadata or {}
    bookmarks = [{"level": level, "title": title, "page": page} for level, title, page in doc.get_toc()]
    return PDFMetadata(
        title=meta.get("title", ""),
        author=meta.get("author", ""),
        subject=meta.get("subject", ""),
        keywords=meta.get("keywords", ""),
        creator=meta.get("creator", ""),
        producer=meta.get("producer", ""),
        creation_date=meta.get("creationDate", ""),
        page_count=doc.page_count,
        bookmarks=bookmarks
    )


def create_tasks(pages: List[PageInfo], metadata: PDFMetadata, work_dir: str) -> List[Task]:
    tasks = []
    extracted_dir = os.path.join(work_dir, "extracted")
    translated_dir = os.path.join(work_dir, "translated")
    status_dir = os.path.join(work_dir, "status")
    os.makedirs(extracted_dir, exist_ok=True)
    os.makedirs(translated_dir, exist_ok=True)
    os.makedirs(status_dir, exist_ok=True)

    for page in pages:
        for block in page.text_blocks:
            task_id = block.block_id
            input_path = os.path.join(extracted_dir, f"{task_id}.json")
            output_path = os.path.join(translated_dir, f"{task_id}.json")
            status_path = os.path.join(status_dir, f"{task_id}.status")
            with open(input_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(block), f, ensure_ascii=False, indent=2)
            tasks.append(Task(
                task_id=task_id,
                task_type="text_block",
                page_num=page.page_num,
                input_path=input_path,
                output_path=output_path,
                status_path=status_path,
                content_preview=block.text[:100] + "..." if len(block.text) > 100 else block.text,
                priority=2 if block.is_heading else 1
            ))

        for table in page.tables:
            task_id = table.table_id
            input_path = os.path.join(extracted_dir, f"{task_id}.json")
            output_path = os.path.join(translated_dir, f"{task_id}.json")
            status_path = os.path.join(status_dir, f"{task_id}.status")
            with open(input_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(table), f, ensure_ascii=False, indent=2)
            tasks.append(Task(
                task_id=task_id,
                task_type="table",
                page_num=page.page_num,
                input_path=input_path,
                output_path=output_path,
                status_path=status_path,
                content_preview=f"Table with {table.row_count} rows, {table.col_count} columns",
                priority=1
            ))

    if metadata.title or metadata.bookmarks:
        task_id = "metadata"
        input_path = os.path.join(extracted_dir, f"{task_id}.json")
        output_path = os.path.join(translated_dir, f"{task_id}.json")
        status_path = os.path.join(status_dir, f"{task_id}.status")
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)
        tasks.append(Task(
            task_id=task_id,
            task_type="metadata",
            page_num=0,
            input_path=input_path,
            output_path=output_path,
            status_path=status_path,
            content_preview=f"Title: {metadata.title}, {len(metadata.bookmarks)} bookmarks",
            priority=1
        ))
    return tasks


def load_dictionary(dict_path: str) -> Dict:
    if not dict_path or not os.path.exists(dict_path):
        return {"characters": {}, "terms": {}}
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load dictionary {dict_path}: {e}")
        return {"characters": {}, "terms": {}}


def analyze_pdf(pdf_path: str, work_dir: str, source_lang: str,
                target_lang: str, academic: bool = False,
                dict_path: Optional[str] = None) -> Manifest:
    print(f"Analyzing: {pdf_path}")
    doc = fitz.open(pdf_path)
    metadata = extract_metadata(doc)
    pages = []
    all_text = ""

    for page_num in range(1, doc.page_count + 1):
        page = doc[page_num - 1]
        text_blocks = extract_text_blocks(page, page_num)
        tables = extract_tables(pdf_path, page_num, work_dir)
        images = extract_images(page, page_num, work_dir)
        layout = detect_layout(text_blocks, page.rect.width)
        num_columns = detect_multi_column(text_blocks, page.rect.width)
        pages.append(PageInfo(
            page_num=page_num,
            width=page.rect.width,
            height=page.rect.height,
            text_blocks=text_blocks,
            tables=tables,
            images=images,
            layout=layout,
            num_columns=num_columns
        ))
        all_text += " ".join([b.text for b in text_blocks])

    doc.close()
    detected_lang = detect_language(all_text) if source_lang == "auto" else source_lang
    load_dictionary(dict_path)
    tasks = create_tasks(pages, metadata, work_dir)

    total_text_blocks = sum(len(p.text_blocks) for p in pages)
    total_tables = sum(len(p.tables) for p in pages)
    total_images = sum(len(p.images) for p in pages)

    layout_counts = {"horizontal": 0, "vertical": 0, "rtl": 0}
    column_counts = {1: 0, 2: 0, 3: 0}
    for page in pages:
        layout_counts[page.layout] += 1
        column_counts[page.num_columns] = column_counts.get(page.num_columns, 0) + 1
    overall_layout = max(layout_counts, key=layout_counts.get)
    dominant_columns = max(column_counts, key=column_counts.get)

    return Manifest(
        project={
            "source_file": pdf_path,
            "source_language": detected_lang,
            "target_language": target_lang,
            "work_dir": work_dir,
            "academic_mode": academic,
            "created_at": datetime.now().isoformat()
        },
        pdf_info={
            "filename": os.path.basename(pdf_path),
            "page_count": len(pages),
            "overall_layout": overall_layout,
            "dominant_columns": dominant_columns,
            "has_vertical_text": layout_counts["vertical"] > 0,
            "has_rtl_text": layout_counts["rtl"] > 0,
            "has_multi_column": dominant_columns > 1
        },
        metadata=asdict(metadata),
        pages=[{
            "page_num": p.page_num,
            "width": p.width,
            "height": p.height,
            "layout": p.layout,
            "num_columns": p.num_columns,
            "text_block_count": len(p.text_blocks),
            "table_count": len(p.tables),
            "image_count": len(p.images)
        } for p in pages],
        tasks=[asdict(t) for t in tasks],
        statistics={
            "total_pages": len(pages),
            "total_tasks": len(tasks),
            "text_block_tasks": total_text_blocks,
            "table_tasks": total_tables,
            "image_count": total_images,
            "has_metadata": bool(metadata.title or metadata.bookmarks),
            "completed": 0,
            "in_progress": 0,
            "failed": 0
        }
    )


def main():
    parser = argparse.ArgumentParser(description='Analyze PDF files for translation')
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--source-lang', default='auto')
    parser.add_argument('--target-lang', default='ko')
    parser.add_argument('--academic', action='store_true')
    parser.add_argument('--dict')
    parser.add_argument('--output-manifest')
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        return 1

    for subdir in ['extracted', 'tables', 'images', 'translated', 'status', 'logs', 'output', 'validation']:
        os.makedirs(os.path.join(args.work_dir, subdir), exist_ok=True)

    manifest = analyze_pdf(
        pdf_path=args.pdf,
        work_dir=args.work_dir,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        academic=args.academic,
        dict_path=args.dict
    )

    manifest_path = args.output_manifest or os.path.join(args.work_dir, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(manifest), f, indent=2, ensure_ascii=False)

    print(f"\nAnalysis complete!")
    print(f"  Source: {manifest.project['source_language']} -> {manifest.project['target_language']}")
    print(f"  Pages: {manifest.statistics['total_pages']}, Tasks: {manifest.statistics['total_tasks']}")
    print(f"  Layout: {manifest.pdf_info['overall_layout']}")
    if manifest.pdf_info['has_multi_column']:
        print(f"  Columns: {manifest.pdf_info['dominant_columns']}")
    print(f"  Manifest: {manifest_path}")
    return 0


if __name__ == '__main__':
    exit(main())
