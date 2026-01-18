#!/bin/bash
#
# EPUB Packaging Script
#
# Packages translated EPUB contents back into valid EPUB files.
# Handles multiple volumes and validates structure.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Usage
usage() {
    echo "Usage: $0 <work_dir> <output_dir>"
    echo ""
    echo "Arguments:"
    echo "  work_dir    - Work directory containing translated files"
    echo "  output_dir  - Directory to save final EPUB files"
    echo ""
    echo "Example:"
    echo "  $0 /tmp/epub_translate_123456 /output/translated"
    exit 1
}

# Check arguments
if [ $# -lt 2 ]; then
    usage
fi

WORK_DIR="$1"
OUTPUT_DIR="$2"

# Validate work directory
if [ ! -d "$WORK_DIR" ]; then
    echo -e "${RED}Error: Work directory not found: $WORK_DIR${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "==========================================="
echo "EPUB Packaging"
echo "==========================================="
echo ""
echo "Work directory: $WORK_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Function to package a single volume
package_volume() {
    local vol_id="$1"
    local vol_dir="$2"
    local output_file="$3"

    echo -e "${YELLOW}Packaging: $vol_id${NC}"

    # Check required files
    if [ ! -f "$vol_dir/mimetype" ]; then
        echo "  Creating mimetype file..."
        echo -n "application/epub+zip" > "$vol_dir/mimetype"
    fi

    # Ensure META-INF/container.xml exists
    if [ ! -f "$vol_dir/META-INF/container.xml" ]; then
        echo "  Creating META-INF/container.xml..."
        mkdir -p "$vol_dir/META-INF"
        cat > "$vol_dir/META-INF/container.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
EOF
    fi

    # Remove old epub if exists
    rm -f "$output_file"

    # Change to volume directory
    cd "$vol_dir"

    # Create EPUB (mimetype must be first, uncompressed)
    zip -X0 "$output_file" mimetype

    # Add META-INF
    if [ -d "META-INF" ]; then
        zip -rX "$output_file" META-INF -x "*.DS_Store" -x "*.bak"
    fi

    # Add OEBPS or OPS (main content)
    if [ -d "OEBPS" ]; then
        zip -rX "$output_file" OEBPS -x "*.DS_Store" -x "*.bak" -x "*.swp" -x "*.tmp"
    elif [ -d "OPS" ]; then
        zip -rX "$output_file" OPS -x "*.DS_Store" -x "*.bak" -x "*.swp" -x "*.tmp"
    fi

    # Add root-level files (if they exist and aren't in OEBPS)
    for file in *.opf *.ncx *.css *.xhtml; do
        if [ -f "$file" ]; then
            zip "$output_file" "$file"
        fi
    done

    # Add images at root level if they exist
    for ext in jpeg jpg png gif svg; do
        for img in *.$ext; do
            if [ -f "$img" ]; then
                zip "$output_file" "$img"
            fi
        done
    done

    # Get file size
    local size=$(du -h "$output_file" | cut -f1)
    echo -e "  ${GREEN}✓ Created: $output_file ($size)${NC}"

    return 0
}

# Read manifest if it exists
MANIFEST="$WORK_DIR/manifest.json"
PACKAGED_COUNT=0

if [ -f "$MANIFEST" ]; then
    echo "Reading manifest..."
    echo ""

    # Extract volume info using Python (more reliable JSON parsing)
    python3 << EOF
import json
import os

manifest_path = "$MANIFEST"
work_dir = "$WORK_DIR"
output_dir = "$OUTPUT_DIR"

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

for volume in manifest.get('volumes', []):
    vol_id = volume['volume_id']
    vol_dir = volume['work_dir']

    # Check if translated directory exists
    translated_dir = os.path.join(work_dir, 'translated', vol_id)
    if os.path.exists(translated_dir):
        # Copy translated files back to original structure
        import shutil
        for root, dirs, files in os.walk(translated_dir):
            for file in files:
                src = os.path.join(root, file)
                rel_path = os.path.relpath(src, translated_dir)
                dst = os.path.join(vol_dir, rel_path)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

    print(f"VOLUME:{vol_id}:{vol_dir}")
EOF

    # Package each volume
    python3 << EOF | while read line; do
import json

with open("$MANIFEST", 'r') as f:
    manifest = json.load(f)

for volume in manifest.get('volumes', []):
    vol_id = volume['volume_id']
    vol_dir = volume['work_dir']
    print(f"{vol_id}|{vol_dir}")
EOF
        vol_id=$(echo "$line" | cut -d'|' -f1)
        vol_dir=$(echo "$line" | cut -d'|' -f2)

        if [ -d "$vol_dir" ]; then
            output_file="$OUTPUT_DIR/${vol_id}_KO.epub"
            package_volume "$vol_id" "$vol_dir" "$output_file"
            PACKAGED_COUNT=$((PACKAGED_COUNT + 1))
        else
            echo -e "${RED}Warning: Volume directory not found: $vol_dir${NC}"
        fi
    done
else
    echo "No manifest found. Looking for extracted directories..."
    echo ""

    # Find and package any extracted volumes
    for vol_dir in "$WORK_DIR/extracted"/*; do
        if [ -d "$vol_dir" ]; then
            vol_id=$(basename "$vol_dir")
            output_file="$OUTPUT_DIR/${vol_id}_KO.epub"
            package_volume "$vol_id" "$vol_dir" "$output_file"
            PACKAGED_COUNT=$((PACKAGED_COUNT + 1))
        fi
    done
fi

echo ""
echo "==========================================="
echo -e "${GREEN}Packaging Complete!${NC}"
echo "==========================================="
echo ""
echo "Packaged: $PACKAGED_COUNT volume(s)"
echo "Output: $OUTPUT_DIR"
echo ""

# List created files
if [ -d "$OUTPUT_DIR" ]; then
    echo "Created files:"
    ls -lh "$OUTPUT_DIR"/*.epub 2>/dev/null || echo "  (no files created)"
fi

echo ""

# Validate with epubcheck if available
if command -v epubcheck &> /dev/null; then
    echo "Running EPUB validation..."
    for epub in "$OUTPUT_DIR"/*.epub; do
        if [ -f "$epub" ]; then
            echo ""
            echo "Validating: $(basename $epub)"
            epubcheck "$epub" 2>&1 | head -20 || true
        fi
    done
else
    echo -e "${YELLOW}Note: epubcheck not installed. Skipping validation.${NC}"
    echo "Install with: brew install epubcheck (macOS) or apt install epubcheck (Linux)"
fi

exit 0
