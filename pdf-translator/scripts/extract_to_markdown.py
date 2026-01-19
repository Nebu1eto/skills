#!/usr/bin/env python3
"""PDF to Markdown Extractor - Converts PDF to clean Markdown with images."""

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

try:
    import fitz
except ImportError:
    print("Error: pymupdf not installed. Run: uv pip install pymupdf")
    exit(1)

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import wordninja
except ImportError:
    wordninja = None

# Common English words for reverse text detection
COMMON_WORDS = {
    # Basic words
    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
    'her', 'was', 'one', 'our', 'out', 'has', 'his', 'how', 'its', 'may',
    'new', 'now', 'old', 'see', 'way', 'who', 'did', 'get', 'let', 'put',
    'say', 'she', 'too', 'use', 'from', 'have', 'been', 'more', 'when',
    'will', 'with', 'what', 'this', 'that', 'they', 'which', 'their',
    # Academic/paper terms
    'collection', 'modification', 'merge', 'questions', 'identification',
    'patient', 'medical', 'clinical', 'disease', 'treatment', 'diagnosis',
    'average', 'confidence', 'accuracy', 'high', 'medium', 'low', 'recall',
    # Additional common words found in PDFs
    'lower', 'border', 'fiber', 'alter', 'left', 'right', 'upper',
    'sternal', 'cardiac', 'original', 'valid', 'random', 'select',
    'content', 'missing', 'malformed', 'fictional', 'benchmark',
    # More common words
    'further', 'imaging', 'within', 'given', 'following', 'shows',
    'presents', 'elevated', 'levels', 'reveals', 'irregular', 'patterns'
}



@dataclass
class DocumentMetadata:
    title: str = ""
    author: str = ""
    page_count: int = 0
    source_file: str = ""


def fix_corrupted_chars(text: str) -> str:
    """Fix common character corruption from PDF extraction."""
    text = re.sub(r'●(\w+)\)', r'(\1)', text)
    text = re.sub(r'\((\w+)●', r'(\1)', text)
    text = re.sub(r'●(\w+)●', r'(\1)', text)
    text = re.sub(r'●', '', text)
    text = re.sub(r'([\w.]+)\s+([\w-]+\.(?:com|org|edu|ac|co|net|gov)(?:\.[a-z]{2,})?)\b', r'\1@\2', text)
    return text


def is_reversed_text(text: str) -> bool:
    """Check if text appears to be reversed (mirrored) text.

    Returns True if the reversed version looks more like English.
    Only considers text reversed if the original is NOT a valid English word.
    """
    if not text or len(text) < 4:
        return False

    # Only check alphabetic text
    if not text.isalpha():
        return False

    text_lower = text.lower()
    reversed_lower = text_lower[::-1]

    # If the original word is already a known English word, it's NOT reversed
    if text_lower in COMMON_WORDS:
        return False

    # Check if reversed version is a known word (and original is not)
    if reversed_lower in COMMON_WORDS:
        return True

    # Check if reversed starts with common prefixes (only if original doesn't look English)
    # Be very conservative - only apply if original has NO common prefix
    common_prefixes = ['pre', 'pro', 'con', 'dis', 'mis', 'un', 're', 'in', 'ex', 'de', 'en', 'em']
    common_suffixes = ['tion', 'ing', 'ness', 'ment', 'able', 'ible', 'ous', 'ive', 'ful', 'less', 'ly', 'er', 'ed']

    # If original has common English patterns, don't treat as reversed
    for suffix in common_suffixes:
        if text_lower.endswith(suffix):
            return False

    for prefix in common_prefixes:
        if text_lower.startswith(prefix):
            return False

    # Now check if reversed looks more like English
    for prefix in common_prefixes:
        if reversed_lower.startswith(prefix):
            return True

    return False


def fix_reversed_text(text: str) -> str:
    """Fix reversed text in a string by detecting and flipping reversed words."""
    if not text:
        return text

    words = text.split()
    fixed_words = []

    for word in words:
        # Check if this word is reversed
        if is_reversed_text(word):
            fixed_words.append(word[::-1])
        else:
            fixed_words.append(word)

    return ' '.join(fixed_words)


def split_concatenated_text(text: str) -> str:
    """Split concatenated text using wordninja library.

    This handles cases where words are joined without spaces.
    Uses quality heuristics to avoid bad splits.
    """
    if wordninja is None:
        return text

    if not text or ' ' in text:
        # Already has spaces, skip
        return text

    # Only process long text without spaces
    if len(text) < 15:
        return text

    # Skip if starts with capital and has CamelCase pattern (likely proper noun)
    # e.g., "Glianorex", "MetaMedQA", "iPhone"
    if text[0].isupper():
        # Check for CamelCase: has internal capitals
        if any(c.isupper() for c in text[1:]):
            return text
        # Single capital word - might be proper noun, be conservative
        # Only split if very long (>20 chars)
        if len(text) < 20:
            return text

    # Skip if mostly non-alphabetic
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count / len(text) < 0.7:
        return text

    # Use wordninja to split
    words = wordninja.split(text)

    if len(words) > 1:
        # Quality check: evaluate if the split is good
        avg_word_len = sum(len(w) for w in words) / len(words)

        # If average word length is too short, split is likely bad
        # e.g., "Glianorex" -> ["Glia", "no", "rex"] avg=3.3 - bad
        # e.g., "comestothephysician" -> ["comes", "to", "the", "physician"] avg=4.5 - ok
        if avg_word_len < 3.5:
            return text

        # Count very short words (1-2 chars)
        short_words = sum(1 for w in words if len(w) <= 2)
        # If more than 30% are very short, likely bad split
        if short_words / len(words) > 0.3:
            return text

        return ' '.join(words)

    return text


def merge_broken_words(text: str) -> str:
    """Merge words that were incorrectly split by PDF extraction.

    PDF extraction with x_tolerance sometimes splits proper nouns or
    technical terms into multiple short fragments.
    e.g., "Glia no rex" -> "Glianorex"
    """
    if not text or ' ' not in text:
        return text

    words = text.split()
    if len(words) < 2:
        return text

    result = []
    i = 0

    while i < len(words):
        current = words[i]

        # Look ahead for potential merge candidates
        # Merge if: current word is short (<=3 chars) AND next word is also short
        # AND they form a capitalized sequence (proper noun pattern)
        merge_buffer = [current]

        j = i + 1
        while j < len(words):
            next_word = words[j]

            # Check if this looks like a broken proper noun
            # Pattern: short fragments that could be part of a longer word
            if len(merge_buffer[-1]) <= 4 and len(next_word) <= 4:
                # Both are short - potential broken word
                combined = ''.join(merge_buffer) + next_word

                # Check if combined word looks reasonable
                # (mostly alphabetic, not a known multi-word phrase)
                if combined.isalpha() and len(combined) >= 6:
                    merge_buffer.append(next_word)
                    j += 1
                    continue

            break

        if len(merge_buffer) > 1:
            # We have multiple short words to merge
            merged = ''.join(merge_buffer)
            result.append(merged)
            i = j
        else:
            result.append(current)
            i += 1

    return ' '.join(result)


def fix_broken_spaces(text: str) -> str:
    """Fix text with incorrectly inserted spaces from PDF extraction.

    PDF sometimes stores characters individually, causing extraction to insert
    spaces between characters. This function detects and fixes such patterns.

    Examples:
        "Gli an orex" -> "Glianorex"
        "c ont a ining" -> "containing"
        "Aver agec onfidence" -> "Averageconfidence"
    """
    if not text or ' ' not in text:
        return text

    result = text

    # Pattern 1: Detect if text has EXTREMELY many short word fragments
    # This indicates broken text like "A ve ra ge con fi den ce"
    # Normal English has short words but NOT 80%+ being 1-2 chars
    words = result.split()
    if len(words) > 3:
        alpha_words = [w for w in words if w.isalpha()]
        if alpha_words:
            # Count very short words (1-2 chars only)
            very_short_count = sum(1 for w in alpha_words if len(w) <= 2)
            very_short_ratio = very_short_count / len(alpha_words)
            if very_short_ratio >= 0.8:
                # Almost all words are 1-2 chars - clearly broken text
                result = result.replace(' ', '')
                return result

    # Pattern 2: Fix only clearly broken patterns (NOT normal text)
    # Be very conservative to avoid breaking valid sentences
    # Only fix patterns where a SINGLE letter appears between spaces
    # and it looks like a broken word fragment

    # "M edical" -> "Medical" (single uppercase followed by space and lowercase)
    # but NOT "A physician" (valid article)
    # Only apply if the uppercase letter is NOT a common article/word
    result = re.sub(r'\b([B-HJ-Z])\s+([a-z]{2,})', r'\1\2', result)

    # "accurac y" -> "accuracy" (letter before single trailing letter)
    # Only if the trailing letter makes sense as part of the word
    result = re.sub(r'([a-z]{3,})\s+([a-z])\b', r'\1\2', result)

    return result


def add_spaces_to_concatenated_text(text: str) -> str:
    """Add spaces to text where words are concatenated without spaces.

    This handles PDF extraction issues where words are joined together.
    Uses conservative heuristics to avoid breaking valid words.
    """
    if not text or len(text) < 3:
        return text

    result = text

    # 1. Add space before capital letters following lowercase (camelCase)
    # e.g., "AverageConfidence" -> "Average Confidence"
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)

    # 2. Add space between number and letter transitions (conservative)
    # Only for clear cases like "7patients" -> "7 patients"
    # Skip patterns that look like model names (GPT-4o) or versions
    result = re.sub(r'(\d)([a-z]{3,})', r'\1 \2', result)  # digit followed by 3+ lowercase

    # 3. Add space after common sentence-ending patterns
    result = re.sub(r'\.([A-Z])', r'. \1', result)
    result = re.sub(r'\?([A-Z])', r'? \1', result)

    # 4. Add space after closing parentheses/brackets followed by letters
    result = re.sub(r'\)([A-Za-z])', r') \1', result)
    result = re.sub(r'\]([A-Za-z])', r'] \1', result)

    # 5. Add space before opening parentheses preceded by letters
    result = re.sub(r'([a-z])\(', r'\1 (', result)

    # 6. Handle specific known concatenation patterns (conservative)
    # Only use words that are 4+ characters to avoid false positives
    boundary_words = [
        'confidence', 'accuracy', 'recall', 'precision',
        'average', 'medium', 'high', 'low',
        'patient', 'presents', 'history', 'symptoms',
        'treatment', 'diagnosis', 'question', 'answer'
    ]
    for word in boundary_words:
        # Add space before word if preceded by lowercase letter
        pattern = rf'([a-z])({word})'
        result = re.sub(pattern, rf'\1 \2', result, flags=re.IGNORECASE)

    return result


def is_valid_table_cell(text: str) -> bool:
    """Check if cell content looks like valid table data."""
    if not text or not text.strip():
        return True  # Empty cells are valid

    text = text.strip()

    # Very long text without spaces is likely concatenated text, not valid table cell
    if len(text) > 50 and ' ' not in text:
        return False

    return True


def validate_table(table_data: list) -> bool:
    """Validate if extracted table data represents a real table.

    Returns False if the table appears to be misidentified content.
    """
    if not table_data or len(table_data) < 2:
        return False

    # Count cells with valid content
    total_cells = 0
    non_empty_cells = 0
    invalid_cells = 0
    long_concat_cells = 0
    very_long_cells = 0

    for row in table_data:
        for cell in row:
            total_cells += 1
            if cell:
                cell_text = str(cell).strip()
                if cell_text:
                    non_empty_cells += 1

                    # Check for very long concatenated text (likely not a table)
                    if len(cell_text) > 80 and ' ' not in cell_text:
                        long_concat_cells += 1

                    # Check for extremely long cells (paragraphs, not table data)
                    if len(cell_text) > 200:
                        very_long_cells += 1

                    if not is_valid_table_cell(cell_text):
                        invalid_cells += 1

    if total_cells == 0 or non_empty_cells == 0:
        return False

    # If any cell has very long concatenated text without spaces, probably not a real table
    if long_concat_cells > 0:
        # Allow if it's a small percentage of a large table
        if long_concat_cells / non_empty_cells > 0.2:
            return False

    # If many cells are extremely long (paragraph-like), not a table
    if very_long_cells / non_empty_cells > 0.3:
        return False

    # If more than 50% of cells are invalid, reject the table
    if invalid_cells / non_empty_cells > 0.5:
        return False

    # Table should have more than one column with content
    if len(table_data) > 0 and len(table_data[0]) == 1:
        # Single column - check if it's just a list or figure element
        first_cell = str(table_data[0][0] or '').strip()
        if len(first_cell) > 150 and ' ' not in first_cell:
            return False

    return True


# Generic header/footer patterns (journal-agnostic)
HEADER_FOOTER_PATTERNS = [
    # DOI patterns (universal)
    r'^https?://doi\.org/10\.\d+/[\w\-\.]+$',  # Standalone DOI URLs
    r'^(Article|Paper|Research)?\s*https?://doi\.org',  # DOI with optional prefix

    # Page number patterns
    r'^\d{1,4}$',  # Standalone page numbers (1-4 digits)
    r'^Page\s+\d+(\s+of\s+\d+)?$',  # "Page 1" or "Page 1 of 10"

    # Journal volume/issue patterns (generic)
    r'^.{0,50}\|\s*\(\d{4}\)\s*\d+:\d+',  # "Journal| (2024) 16:642" pattern
    r'^\w+\s+\d+,?\s+\d{4}$',  # "Month Day, Year" or "Journal Vol, Year"
    r'^Vol\.?\s*\d+.*No\.?\s*\d+',  # "Vol. 1, No. 2" pattern

    # PDF artifacts
    r'^[\d\s():,;]+$',  # Number sequences with punctuation (like "1234567890():,;")
    r'^[✱\*†‡§¶]+[\s✱\*†‡§¶]*$',  # Footnote/significance markers

    # Common header/footer text (language-agnostic)
    r'^(Article|Paper|Research|Letter|Review|Original)\s*$',
    r'^Check for updates$',
    r'^(Received|Accepted|Published|Submitted|Revised):\s*\d{1,2}\s+\w+\s+\d{4}$',
    r'^(Copyright|©)\s*\d{4}',
    r'^\d{4}\s*(©|Copyright)',
]

HEADER_FOOTER_COMPILED = [re.compile(p, re.IGNORECASE) for p in HEADER_FOOTER_PATTERNS]


def is_header_footer(text: str) -> bool:
    """Check if text is a page header or footer using generic patterns."""
    text = text.strip()

    # Very short text at page boundaries is likely header/footer
    if len(text) < 3:
        return True

    for pattern in HEADER_FOOTER_COMPILED:
        if pattern.match(text):
            return True

    return False


def merge_superscripts(text: str) -> str:
    """Merge superscript numbers (like author affiliations and references) with preceding text."""
    # Fix author affiliations: "Name\n1,2" -> "Name^1,2"
    text = re.sub(r'(\w+)\n(\d+(?:,\d+)*)\n,\s*', r'\1^[\2], ', text)
    text = re.sub(r'(\w+)\n(\d+(?:,\d+)*)\s*$', r'\1^[\2]', text)
    text = re.sub(r'(\w+)\n(\d+(?:,\d+)*)\s+', r'\1^[\2] ', text)

    # Fix inline reference numbers: "word1" -> "word^[1]"
    text = re.sub(r'(\w+)(\d{1,2})([,.\s])', r'\1^[\2]\3', text)
    text = re.sub(r'(\w+)(\d{1,2}–\d{1,2})([,.\s])', r'\1^[\2]\3', text)

    return text


def fix_broken_urls(text: str) -> str:
    """Fix URLs broken during PDF extraction."""
    result = re.sub(r'(https?://\w+)\.\s+(\w+)', r'\1.\2', text)
    result = re.sub(r'(https?://[\w.]+)\s*/\s*', r'\1/', result)
    result = re.sub(r'(https?://[\w./]+)\s+(\w+)', r'\1\2', result)
    result = re.sub(r'https?://doi\.\s*org', 'https://doi.org', result)
    return result


def filter_artifact_text(text: str) -> bool:
    """Return True if text is artifact/noise."""
    stripped = text.strip()

    # Very short text
    if len(stripped) < 2:
        return True

    # Number sequences (often PDF artifacts)
    if re.match(r'^[a-z]?\d{5,}(\s+[a-z]?\d{5,})*$', stripped):
        return True

    # PDF artifact patterns like "1234567890():,;"
    if re.match(r'^[\d\s():,;]+$', stripped) and len(stripped) > 5:
        return True

    # Header/footer check
    if is_header_footer(stripped):
        return True

    return False


def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ''
    text = fix_corrupted_chars(text)
    text = fix_broken_urls(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def is_figure_label(text: str, font_size: float, avg_size: float, block_bbox: list) -> bool:
    """Detect if text is likely a figure/chart label using generic heuristics."""
    text = text.strip()

    # Pure numbers or percentages (axis labels)
    if re.match(r'^[\d.,]+%?$', text):
        return True

    # Very short text with small font (likely axis/legend labels)
    words = text.split()
    if len(words) <= 2 and font_size < avg_size * 0.9:
        return True

    # Common chart/figure label patterns (language-agnostic)
    # - Single words followed by numbers (e.g., "Model 1", "Group A")
    # - Percentage labels
    # - Axis unit labels
    if re.match(r'^[\w\-\.]+\s*\d*[A-Za-z]?$', text) and len(text) < 20:
        if font_size < avg_size:
            return True

    return False


def is_chart_element(text: str, font_size: float, avg_size: float, block_bbox: list,
                     page_width: float, page_height: float, drawing_rects: List[Tuple]) -> bool:
    """Detect if text block is part of a chart/figure element.

    Uses multiple heuristics:
    1. Text is near or inside graphic regions
    2. Text matches common chart patterns (axis labels, legend, model names)
    3. Small font size with short content
    """
    text = text.strip()

    if not text:
        return False

    # Basic figure label check
    if is_figure_label(text, font_size, avg_size, block_bbox):
        return True

    # Check if text is inside or near a drawing/graphic region
    if len(block_bbox) >= 4 and drawing_rects:
        bx0, by0, bx1, by1 = block_bbox[:4]
        for rect in drawing_rects:
            rx0, ry0, rx1, ry1 = rect
            # Check if block is inside or overlaps with drawing
            # with 20px margin for tolerance
            margin = 20
            if (bx0 >= rx0 - margin and bx1 <= rx1 + margin and
                by0 >= ry0 - margin and by1 <= ry1 + margin):
                # Text is inside graphic region - likely chart element
                return True

    # Model names pattern (common in ML papers)
    # e.g., "GPT-4o", "Llama 3 70B", "Yi 1.5 9B", "Qwen2 72B"
    model_pattern = r'^(GPT|Llama|Yi|Qwen|Mistral|Mixtral|Meerkat|Internist|Claude|Gemini|PaLM)[\s\-]?[\d\.]+[a-zA-Z]*(\s+\d+[BbMmKk])?$'
    if re.match(model_pattern, text, re.IGNORECASE):
        return True

    # Axis labels - numbers with units
    # e.g., "20", "60", "Accuracy (%)", "Missing answer recall (%)"
    if re.match(r'^\d{1,3}$', text):  # Standalone numbers (axis ticks)
        return True

    # Short text with parentheses containing % often axis label
    if re.match(r'^[\w\s]+\s*\(%\)$', text) and len(text) < 30:
        return True

    # Sequence of reference numbers that look like axis ticks
    # e.g., "^[30] ^[40] ^[50] ^[60] ^[70] ^[80]"
    if re.match(r'^(\^?\[\d+\]\s*)+$', text):
        return True

    # Just reference numbers separated by spaces
    if re.match(r'^(\d{1,3}\s+)+\d{1,3}$', text):
        return True

    # Very small font with short content = likely legend/label
    if font_size < avg_size * 0.85 and len(text) < 25:
        words = text.split()
        if len(words) <= 3:
            return True

    return False


def get_drawing_regions(page: 'fitz.Page') -> List[Tuple[float, float, float, float]]:
    """Extract bounding boxes of drawing/graphic regions from page.

    Returns list of (x0, y0, x1, y1) tuples for graphic areas.
    """
    drawing_rects = []

    try:
        # Get all drawings from the page
        drawings = page.get_drawings()

        if not drawings:
            return []

        # Group nearby drawings into regions
        rect_points = []
        for d in drawings:
            if 'rect' in d:
                r = d['rect']
                rect_points.append((r.x0, r.y0, r.x1, r.y1))
            elif 'items' in d:
                for item in d['items']:
                    if len(item) >= 2 and hasattr(item[1], 'x0'):
                        r = item[1]
                        rect_points.append((r.x0, r.y0, r.x1, r.y1))

        # Merge overlapping/nearby rectangles into regions
        if rect_points:
            # Simple clustering: find bounding boxes of grouped drawings
            # For simplicity, we'll identify large drawing regions
            merged = []
            for rect in rect_points:
                x0, y0, x1, y1 = rect
                # Only consider reasonably sized drawings (likely figures)
                width = x1 - x0
                height = y1 - y0
                if width > 50 and height > 50:
                    merged.append(rect)

            # Merge overlapping rectangles
            if merged:
                drawing_rects = merge_overlapping_rects(merged)

    except Exception:
        pass

    return drawing_rects


def merge_overlapping_rects(rects: List[Tuple], margin: float = 30) -> List[Tuple[float, float, float, float]]:
    """Merge overlapping or nearby rectangles into larger regions."""
    if not rects:
        return []

    # Sort by y0, then x0
    sorted_rects = sorted(rects, key=lambda r: (r[1], r[0]))

    merged = []
    current = list(sorted_rects[0])

    for rect in sorted_rects[1:]:
        x0, y0, x1, y1 = rect

        # Check if this rect overlaps with or is near current
        if (x0 <= current[2] + margin and x1 >= current[0] - margin and
            y0 <= current[3] + margin and y1 >= current[1] - margin):
            # Merge
            current[0] = min(current[0], x0)
            current[1] = min(current[1], y0)
            current[2] = max(current[2], x1)
            current[3] = max(current[3], y1)
        else:
            merged.append(tuple(current))
            current = list(rect)

    merged.append(tuple(current))
    return merged


def is_heading(block: Dict, page_blocks: List[Dict]) -> bool:
    """Detect if a text block is a heading using generic heuristics."""
    if not block.get("lines"):
        return False

    line = block["lines"][0]
    if not line.get("spans"):
        return False

    span = line["spans"][0]
    font_size = span.get("size", 0)
    text = span.get("text", "").strip()

    # Skip very short text
    if len(text) < 3:
        return False

    # Get average and max font sizes
    all_sizes = []
    for b in page_blocks:
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                size = s.get("size", 0)
                if size > 0:
                    all_sizes.append(size)

    avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 10

    # Skip figure/chart labels
    block_bbox = block.get("bbox", [])
    if is_figure_label(text, font_size, avg_size, block_bbox):
        return False

    # Heading criteria - must be significantly larger than average
    if font_size > avg_size * 1.3:
        # Additional check: headings should have meaningful content
        # At least 2 words or starts with capital letter
        words = text.split()
        if len(words) >= 2 or (len(text) >= 5 and text[0].isupper()):
            return True

    # Bold text can be heading, but with stricter criteria
    if span.get("flags", 0) & 2**4:  # Bold
        # Must be reasonable length and not end with period (not a sentence)
        if 10 <= len(text) < 100 and not text.endswith('.'):
            return True

    return False


def detect_heading_level(font_size: float, max_size: float) -> int:
    """Determine heading level based on font size."""
    ratio = font_size / max_size if max_size > 0 else 0
    if ratio > 0.9:
        return 1
    elif ratio > 0.7:
        return 2
    elif ratio > 0.5:
        return 3
    return 4


def extract_images(doc: fitz.Document, output_dir: str, min_width: int = 100, min_height: int = 100) -> Dict[int, List[str]]:
    """Extract images from PDF, returns dict of page_num -> image paths."""
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    page_images = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        page_images[page_num + 1] = []

        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)

                if base_image["width"] < min_width or base_image["height"] < min_height:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                image_filename = f"page{page_num + 1:03d}_img{img_idx:03d}.{image_ext}"
                image_path = os.path.join(images_dir, image_filename)

                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                page_images[page_num + 1].append(f"images/{image_filename}")
            except Exception:
                continue

    return page_images


def process_table_cell(cell_text: str) -> str:
    """Process a table cell: clean, add spaces, and format."""
    if not cell_text:
        return ''

    text = str(cell_text).replace('\n', ' ').replace('|', '\\|')

    # Step 1: Fix reversed text (e.g., "noitcelloC" -> "Collection")
    text = fix_reversed_text(text)

    # Step 1.5: Merge broken words (e.g., "Glia no rex" -> "Glianorex")
    text = merge_broken_words(text)

    # Step 2: Check if this looks like broken text (most words are 1-2 chars)
    # Normal English has short words like "to", "the", "a" mixed with longer words
    # Broken text looks like "A ve ra ge con fi den ce" (almost all 1-2 char words)
    words = text.split()
    if len(words) > 3:
        # Count words that are very short (1-2 chars) and alphabetic
        alpha_words = [w for w in words if w.isalpha()]
        if alpha_words:
            very_short_count = sum(1 for w in alpha_words if len(w) <= 2)
            very_short_ratio = very_short_count / len(alpha_words)
            # Only fix if 80%+ of alphabetic words are 1-2 chars (clearly broken)
            if very_short_ratio >= 0.8:
                # Aggressive fix: remove all spaces from alphabetic sequences
                # but preserve spaces around numbers and special chars
                parts = re.split(r'(\d[\d.,%()+\-±]*|\s+)', text)
                fixed_parts = []
                for part in parts:
                    if part and not re.match(r'^[\d.,%()+\-±\s]+$', part):
                        # Alphabetic part - remove internal spaces
                        part = part.replace(' ', '')
                    fixed_parts.append(part)
                text = ''.join(fixed_parts)
                # Now add proper spaces back
                text = add_spaces_to_concatenated_text(text)

    # Step 3: Apply fix_broken_spaces for remaining issues
    text = fix_broken_spaces(text)

    # Step 4: Process each word individually - some may still be concatenated
    words = text.split()
    processed_words = []
    for word in words:
        # Skip numbers and very short words
        if len(word) < 6 or re.match(r'^[\d.,%()+\-±]+$', word):
            processed_words.append(word)
            continue

        # Try wordninja for potentially concatenated words
        # Only for purely alphabetic words
        if wordninja is not None and word.isalpha():
            split_words = wordninja.split(word)
            # Only accept split if:
            # 1. Actually split into multiple words
            # 2. Short words (2 chars) must be valid English words, not suffix artifacts
            # 3. Average word length is reasonable (3+)
            if len(split_words) > 1:
                # Valid 1-2 letter English words (not suffix artifacts)
                valid_1char = {'a', 'i'}  # Valid single-letter words
                valid_2char = {'is', 'as', 'no', 'to', 'be', 'we', 'he', 'me', 'it', 'in', 'on',
                               'or', 'an', 'at', 'by', 'do', 'go', 'if', 'of', 'so', 'up', 'my'}
                # Suffix artifacts that indicate bad splits
                suffix_artifacts = {'al', 'ed', 'er', 'ly', 'es', 'en', 'le', 'el', 'ic', 'ty'}
                # Check each word: must be 3+ chars OR a valid 1-2 char word
                all_valid = all(
                    len(w) >= 3 or
                    (len(w) == 2 and w.lower() in valid_2char) or
                    (len(w) == 1 and w.lower() in valid_1char)  # Allow "a", "A", "i", "I"
                    for w in split_words
                )
                # Reject if any word is a suffix artifact
                has_artifact = any(len(w) == 2 and w.lower() in suffix_artifacts for w in split_words)
                # First word should be 2+ chars (or 1 char if uppercase)
                first_ok = len(split_words[0]) >= 2 or (len(split_words[0]) == 1 and split_words[0].isupper())
                # Last word should NOT be a suffix artifact
                last_ok = len(split_words[-1]) >= 3 or split_words[-1].lower() in valid_2char
                if all_valid and not has_artifact and first_ok and last_ok:
                    word = ' '.join(split_words)
                    processed_words.append(word)
                    continue

        # For long words (15+) with mixed content (letters + hyphens/numbers/punctuation)
        # Try to split alphabetic parts individually
        if len(word) > 15 and wordninja is not None:
            # Split on hyphens, numbers, and common punctuation, process each alphabetic part
            parts = re.split(r'(-|\d+|[,.:;])', word)
            new_parts = []
            for part in parts:
                if part and part.isalpha() and len(part) > 10:
                    # Try wordninja on this alphabetic part
                    split_result = wordninja.split(part)
                    if len(split_result) > 1:
                        # Apply same quality checks
                        valid_1char = {'a', 'i'}
                        valid_2char = {'is', 'as', 'no', 'to', 'be', 'we', 'he', 'me', 'it', 'in', 'on',
                                       'or', 'an', 'at', 'by', 'do', 'go', 'if', 'of', 'so', 'up', 'my'}
                        suffix_artifacts = {'al', 'ed', 'er', 'ly', 'es', 'en', 'le', 'el', 'ic', 'ty'}
                        all_valid = all(
                            len(w) >= 3 or
                            (len(w) == 2 and w.lower() in valid_2char) or
                            (len(w) == 1 and w.lower() in valid_1char)
                            for w in split_result
                        )
                        has_artifact = any(len(w) == 2 and w.lower() in suffix_artifacts for w in split_result)
                        if all_valid and not has_artifact:
                            part = ' '.join(split_result)
                new_parts.append(part)
            word = ''.join(new_parts)

        # Fall back to pattern-based splitting for very long words
        if len(word) > 20 and ' ' not in word:
            word = add_spaces_to_concatenated_text(word)

        processed_words.append(word)

    text = ' '.join(processed_words)

    # Post-processing: Add space after punctuation if missing
    # "accident.Soon" -> "accident. Soon"
    # "hospitalization,he" -> "hospitalization, he"
    text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([,;:])([A-Za-z])', r'\1 \2', text)

    # Add space between letter and number when directly adjacent
    # "A58" -> "A 58" (but preserve patterns like "COVID-19")
    text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)

    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def extract_table_text_with_tolerance(page, bbox: Tuple, x_tolerance: float = 1.5) -> List[List[str]]:
    """Extract table text using custom x_tolerance for better word separation.

    Args:
        page: pdfplumber page object
        bbox: Table bounding box (x0, y0, x1, y1)
        x_tolerance: Character spacing threshold for word separation

    Returns:
        List of rows, each row is a list of cell texts
    """
    cropped = page.crop(bbox)
    text = cropped.extract_text(x_tolerance=x_tolerance, y_tolerance=3)

    if not text:
        return []

    # Split into lines and return as single-column table
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return [[line] for line in lines]


def extract_tables_from_page(page_num: int, pdf_path: str) -> Tuple[List[str], List[Tuple[float, float, float, float]]]:
    """Extract tables from a page using pdfplumber.
    Returns (table_markdowns, table_bboxes) where bbox is (x0, y0, x1, y1)."""
    if pdfplumber is None:
        return [], []

    tables_md = []
    table_bboxes = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]

                tables = page.find_tables()

                for table in tables:
                    # Get table bounding box
                    bbox = table.bbox  # (x0, y0, x1, y1)

                    # Try x_tolerance-based extraction first (better word separation)
                    table_data = extract_table_text_with_tolerance(page, bbox, x_tolerance=1.5)

                    # Fall back to default extraction if x_tolerance method fails
                    if not table_data or len(table_data) < 2:
                        table_data = table.extract()

                    # Validate table before processing
                    if not validate_table(table_data):
                        # Still add bbox to exclude from text extraction
                        # but don't generate markdown for invalid tables
                        table_bboxes.append(bbox)
                        continue

                    table_bboxes.append(bbox)

                    md_lines = []
                    # Header - process each cell
                    header = [process_table_cell(cell) for cell in table_data[0]]

                    # Skip tables with all empty headers
                    if all(not h for h in header):
                        continue

                    md_lines.append('| ' + ' | '.join(header) + ' |')
                    md_lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')

                    # Rows
                    for row in table_data[1:]:
                        cells = [process_table_cell(cell) for cell in row]
                        # Pad if needed
                        while len(cells) < len(header):
                            cells.append('')
                        md_lines.append('| ' + ' | '.join(cells[:len(header)]) + ' |')

                    tables_md.append('\n'.join(md_lines))
    except Exception:
        pass

    return tables_md, table_bboxes


def bbox_overlaps(bbox1: Tuple[float, float, float, float], bbox2: Tuple[float, float, float, float], margin: float = 5.0) -> bool:
    """Check if two bounding boxes overlap (with margin for tolerance)."""
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2

    # Add margin tolerance
    x0_2 -= margin
    y0_2 -= margin
    x1_2 += margin
    y1_2 += margin

    # Check if boxes overlap
    return not (x1_1 < x0_2 or x0_1 > x1_2 or y1_1 < y0_2 or y0_1 > y1_2)


def is_superscript_span(span: Dict, base_font_size: float) -> bool:
    """Check if a span is a superscript based on font size and flags."""
    span_size = span.get("size", 0)
    flags = span.get("flags", 0)

    # Significantly smaller font indicates superscript
    if span_size < base_font_size * 0.75:
        return True

    # Check superscript flag (bit 0)
    if flags & 1:
        return True

    return False


def extract_line_with_superscripts(line: Dict, base_font_size: float) -> str:
    """Extract line text with proper superscript handling."""
    result_parts = []
    spans = line.get("spans", [])

    for i, span in enumerate(spans):
        text = span.get("text", "")
        if not text:
            continue

        if is_superscript_span(span, base_font_size):
            # Check if it's a reference number (digits only)
            if re.match(r'^[\d,–-]+$', text.strip()):
                # Format as reference: ^[1] or ^[1,2]
                result_parts.append(f"^[{text.strip()}]")
            else:
                result_parts.append(text)
        else:
            result_parts.append(text)

    return ''.join(result_parts)


def extract_page_text(page: fitz.Page, page_num: int, exclude_bboxes: List[Tuple[float, float, float, float]] = None) -> Tuple[str, List[Dict]]:
    """Extract text from a page as Markdown, excluding text in specified bounding boxes."""
    if exclude_bboxes is None:
        exclude_bboxes = []

    text_dict = page.get_text("dict")
    blocks = text_dict.get("blocks", [])
    page_height = page.rect.height
    page_width = page.rect.width

    # Get drawing regions for chart/figure detection
    drawing_rects = get_drawing_regions(page)

    # Filter text blocks only
    text_blocks = [b for b in blocks if b.get("type") == 0]

    # Calculate base font size (most common size)
    font_sizes = []
    for block in text_blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                size = span.get("size", 0)
                if size > 0:
                    font_sizes.append(size)

    base_font_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 10
    max_font_size = max(font_sizes) if font_sizes else 12

    lines = []
    block_info = []

    # Header/footer margin (top/bottom 8% of page)
    header_margin = page_height * 0.08
    footer_margin = page_height * 0.92

    for block in text_blocks:
        block_bbox = block.get("bbox", [0, 0, 0, 0])

        # Skip blocks in header/footer region
        if len(block_bbox) >= 4:
            block_top = block_bbox[1]
            block_bottom = block_bbox[3]

            # Check if block is in header region (top 8%)
            if block_top < header_margin:
                # Only filter if it looks like header text
                block_text_check = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text_check += span.get("text", "")
                if is_header_footer(block_text_check):
                    continue

            # Check if block is in footer region (bottom 8%)
            if block_bottom > footer_margin:
                block_text_check = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text_check += span.get("text", "")
                if is_header_footer(block_text_check):
                    continue

            # Check overlap with table bboxes
            skip_block = False
            for table_bbox in exclude_bboxes:
                if bbox_overlaps(tuple(block_bbox), table_bbox, margin=10.0):
                    skip_block = True
                    break
            if skip_block:
                continue

        # Extract text with superscript handling
        block_lines = []
        block_font_size = 0

        for line in block.get("lines", []):
            line_text = extract_line_with_superscripts(line, base_font_size)
            if line_text:
                block_lines.append(line_text)
            for span in line.get("spans", []):
                block_font_size = max(block_font_size, span.get("size", 0))

        block_text = ' '.join(block_lines)  # Join lines with space instead of newline
        block_text = block_text.strip()

        if not block_text or filter_artifact_text(block_text):
            continue

        block_text = clean_text(block_text)
        if not block_text:
            continue

        # Filter out chart/figure elements (axis labels, legend text, model names in charts)
        if is_chart_element(block_text, block_font_size, base_font_size, block_bbox,
                           page_width, page_height, drawing_rects):
            continue

        # Check if heading
        is_head = is_heading(block, text_blocks)

        if is_head:
            level = detect_heading_level(block_font_size, max_font_size)
            lines.append(f"\n{'#' * level} {block_text}\n")
        else:
            lines.append(f"\n{block_text}\n")

        block_info.append({
            "text": block_text,
            "is_heading": is_head,
            "bbox": block.get("bbox", [])
        })

    return '\n'.join(lines), block_info


def extract_metadata(doc: fitz.Document, pdf_path: str) -> DocumentMetadata:
    """Extract document metadata."""
    meta = doc.metadata or {}

    title = meta.get("title", "")
    if not title:
        # Try to get title from first page
        if len(doc) > 0:
            page = doc[0]
            text_dict = page.get_text("dict")
            blocks = [b for b in text_dict.get("blocks", []) if b.get("type") == 0]

            max_size = 0
            title_candidate = ""
            for block in blocks[:5]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("size", 0) > max_size:
                            max_size = span.get("size", 0)
                            title_candidate = span.get("text", "").strip()

            title = title_candidate

    return DocumentMetadata(
        title=title,
        author=meta.get("author", ""),
        page_count=len(doc),
        source_file=os.path.basename(pdf_path)
    )


def generate_frontmatter(metadata: DocumentMetadata, source_lang: str, target_lang: str) -> str:
    """Generate YAML frontmatter."""
    return f'''---
title: "{metadata.title}"
author: "{metadata.author}"
pages: {metadata.page_count}
source_file: "{metadata.source_file}"
source_language: {source_lang}
target_language: {target_lang}
---

'''


def post_process_references(markdown: str) -> str:
    """Post-process the References section for better formatting.

    Supports multiple languages and heading formats:
    - English: References, Bibliography, Works Cited
    - Korean: 참고문헌, 참고 문헌
    - German: Literatur, Literaturverzeichnis
    - French: Références, Bibliographie
    - Spanish: Referencias, Bibliografía
    - Chinese: 参考文献
    - Japanese: 参考文献, 引用文献
    """
    # Multi-language reference section headers
    ref_headers = [
        r'References', r'Bibliography', r'Works\s+Cited', r'Literature',
        r'참고문헌', r'참고\s*문헌',
        r'Literatur(?:verzeichnis)?',
        r'Références', r'Bibliographie',
        r'Referencias', r'Bibliografía',
        r'参考文献', r'引用文献',
    ]

    # Build pattern to match any reference header
    header_pattern = '|'.join(ref_headers)
    ref_pattern = rf'(#{{1,3}}\s*(?:{header_pattern})\s*\n)(.*?)(?=\n#{{1,3}}\s|\Z)'
    match = re.search(ref_pattern, markdown, re.DOTALL | re.IGNORECASE)

    if not match:
        return markdown

    ref_header = match.group(1)
    ref_content = match.group(2)

    # Fix reference entries where number is on separate line
    # Pattern: "\n1.\n" or "\n12.\n" followed by text
    ref_content = re.sub(r'\n(\d{1,3})\.\s*\n', r'\n\1. ', ref_content)

    # Merge lines within a reference entry (lines not starting with number)
    lines = ref_content.split('\n')
    merged_lines = []
    current_ref = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_ref:
                merged_lines.append(current_ref)
                current_ref = ""
            merged_lines.append("")
            continue

        # Check if line starts a new reference (number followed by dot)
        if re.match(r'^\d{1,3}\.\s', stripped):
            if current_ref:
                merged_lines.append(current_ref)
            current_ref = stripped
        else:
            # Continue previous reference
            if current_ref:
                current_ref += " " + stripped
            else:
                current_ref = stripped

    if current_ref:
        merged_lines.append(current_ref)

    new_ref_content = '\n'.join(merged_lines)

    # Replace the references section
    return markdown[:match.start()] + ref_header + new_ref_content + markdown[match.end():]


def post_process_markdown(markdown: str) -> str:
    """Apply all post-processing to the extracted markdown."""
    # Process references section
    markdown = post_process_references(markdown)

    # Remove duplicate page markers
    markdown = re.sub(r'(<!-- Page \d+ -->)\s*\1', r'\1', markdown)

    # Clean up excessive whitespace around headings
    markdown = re.sub(r'\n{3,}(#)', r'\n\n\1', markdown)

    # Remove orphaned superscript numbers at start of paragraphs
    markdown = re.sub(r'\n\^?\[?\d{1,2}\]?\s*\n', '\n', markdown)

    return markdown


def extract_to_markdown(pdf_path: str, output_dir: str, source_lang: str = "auto", target_lang: str = "ko") -> Dict[str, Any]:
    """Extract PDF to Markdown with images."""

    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)

    # Extract metadata
    metadata = extract_metadata(doc, pdf_path)
    print(f"Title: {metadata.title}")
    print(f"Pages: {metadata.page_count}")

    # Extract images
    print("Extracting images...")
    page_images = extract_images(doc, output_dir)
    image_count = sum(len(imgs) for imgs in page_images.values())
    print(f"Extracted {image_count} images")

    # Extract text and build markdown
    print("Extracting text...")
    markdown_parts = [generate_frontmatter(metadata, source_lang, target_lang)]

    if metadata.title:
        markdown_parts.append(f"# {metadata.title}\n\n")

    for page_num in range(1, len(doc) + 1):
        page = doc[page_num - 1]

        # Page anchor
        markdown_parts.append(f'\n<!-- Page {page_num} -->\n')

        # Extract tables first and get their bounding boxes
        tables, table_bboxes = extract_tables_from_page(page_num, pdf_path)

        # Extract text, excluding text that overlaps with table regions
        page_text, _ = extract_page_text(page, page_num, exclude_bboxes=table_bboxes)
        markdown_parts.append(page_text)

        # Add tables (already extracted, no duplication)
        for table_md in tables:
            markdown_parts.append(f"\n{table_md}\n")

        # Add images
        for img_path in page_images.get(page_num, []):
            markdown_parts.append(f"\n![Image]({img_path})\n")

    # Combine and clean
    markdown = '\n'.join(markdown_parts)
    markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)

    # Apply post-processing
    markdown = post_process_markdown(markdown)

    # Save markdown
    output_path = os.path.join(output_dir, "source.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    # Save metadata
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)

    doc.close()

    print(f"Saved: {output_path}")

    return {
        "markdown_path": output_path,
        "metadata": asdict(metadata),
        "image_count": image_count,
        "page_count": metadata.page_count
    }


def main():
    parser = argparse.ArgumentParser(description='Extract PDF to Markdown')
    parser.add_argument('--pdf', required=True, help='Input PDF file')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--source-lang', default='auto', help='Source language')
    parser.add_argument('--target-lang', default='ko', help='Target language')
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Error: PDF not found: {args.pdf}")
        return 1

    result = extract_to_markdown(
        args.pdf,
        args.output_dir,
        args.source_lang,
        args.target_lang
    )

    print(f"\nExtraction complete:")
    print(f"  Pages: {result['page_count']}")
    print(f"  Images: {result['image_count']}")
    print(f"  Output: {result['markdown_path']}")

    return 0


if __name__ == '__main__':
    exit(main())
