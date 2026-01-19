#!/usr/bin/env python3
"""PDF Output Generator - Converts Markdown to PDF via pandoc + weasyprint."""

import argparse
import os
import subprocess

try:
    from weasyprint import HTML
except ImportError:
    print("Error: weasyprint not installed. Run: uv pip install weasyprint")
    exit(1)

CSS_STYLE = """
@page {
    size: A4;
    margin: 2.5cm 2cm;
    @bottom-center {
        content: counter(page);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #333;
}

h1 {
    font-size: 20pt;
    font-weight: 600;
    margin-top: 0;
    margin-bottom: 1em;
    color: #1a1a1a;
    border-bottom: 2px solid #333;
    padding-bottom: 0.3em;
}

h2 {
    font-size: 14pt;
    font-weight: 600;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    color: #1a1a1a;
}

h3 {
    font-size: 12pt;
    font-weight: 600;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
}

p {
    margin: 0.8em 0;
    text-align: justify;
}

a {
    color: #0066cc;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

ul, ol {
    margin: 0.8em 0;
    padding-left: 2em;
}

li {
    margin: 0.3em 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 10pt;
}

th, td {
    border: 1px solid #ccc;
    padding: 8px 10px;
    text-align: left;
}

th {
    background-color: #f5f5f5;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: #fafafa;
}

blockquote {
    margin: 1em 0;
    padding: 0.5em 1em;
    border-left: 4px solid #ddd;
    color: #666;
    background-color: #f9f9f9;
}

code {
    font-family: "SF Mono", "Menlo", monospace;
    font-size: 9pt;
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 3px;
}

pre {
    background-color: #f4f4f4;
    padding: 1em;
    overflow-x: auto;
    border-radius: 4px;
}

pre code {
    background: none;
    padding: 0;
}

del, s {
    text-decoration: line-through;
    color: #999;
}

strong {
    font-weight: 600;
}

em {
    font-style: italic;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

.page-break {
    page-break-after: always;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}
"""


def check_pandoc():
    """Check if pandoc is available."""
    try:
        result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def markdown_to_html(markdown_path: str) -> str:
    """Convert Markdown to HTML using pandoc."""
    # Use markdown+strikeout to support ~~strikethrough~~ syntax
    result = subprocess.run(
        ['pandoc', markdown_path, '-f', 'markdown+strikeout', '-t', 'html5'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"pandoc failed: {result.stderr}")

    # Wrap in complete HTML document with our styles
    html_body = result.stdout
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{CSS_STYLE}</style>
</head>
<body>
{html_body}
</body>
</html>'''


def generate_pdf(markdown_path: str, output_path: str):
    """Generate PDF from Markdown via pandoc + weasyprint."""
    if not check_pandoc():
        print("Error: pandoc not found. Install with: brew install pandoc")
        return False

    print(f"Converting: {markdown_path}")

    # Convert Markdown to HTML
    html_content = markdown_to_html(markdown_path)

    # Get base directory for resolving relative image paths
    base_dir = os.path.dirname(os.path.abspath(markdown_path))
    base_url = f'file://{base_dir}/'

    # Create PDF with weasyprint
    print("Generating PDF with weasyprint...")
    html = HTML(string=html_content, base_url=base_url)
    html.write_pdf(output_path)

    print(f"PDF saved: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Generate PDF from Markdown')
    parser.add_argument('--markdown', required=True, help='Input Markdown file')
    parser.add_argument('--output', required=True, help='Output PDF file')
    args = parser.parse_args()

    if not os.path.exists(args.markdown):
        print(f"Error: Markdown file not found: {args.markdown}")
        return 1

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    success = generate_pdf(args.markdown, args.output)
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
