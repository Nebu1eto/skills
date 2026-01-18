#!/bin/bash
# PDF Translation Skill - Environment Setup
# Automatically uses uv if available, otherwise falls back to python venv + pip

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${PROJECT_DIR}/.venv"
REQUIREMENTS="pymupdf pdfplumber reportlab"

echo "Setting up PDF translation environment..."

# Check if virtual environment already exists and has packages
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ]; then
    if "$VENV_DIR/bin/python" -c "import fitz, pdfplumber, reportlab" 2>/dev/null; then
        echo "Environment already set up at $VENV_DIR"
        echo "Python: $VENV_DIR/bin/python"
        exit 0
    fi
fi

# Detect package manager
if command -v uv &> /dev/null; then
    echo "Using uv..."

    # Create venv if not exists
    if [ ! -d "$VENV_DIR" ]; then
        uv venv "$VENV_DIR"
    fi

    # Install dependencies
    uv pip install --python "$VENV_DIR/bin/python" $REQUIREMENTS

elif command -v python3 &> /dev/null; then
    echo "Using python3 venv + pip..."

    # Create venv if not exists
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi

    # Upgrade pip and install dependencies
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install $REQUIREMENTS

elif command -v python &> /dev/null; then
    echo "Using python venv + pip..."

    # Create venv if not exists
    if [ ! -d "$VENV_DIR" ]; then
        python -m venv "$VENV_DIR"
    fi

    # Upgrade pip and install dependencies
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install $REQUIREMENTS

else
    echo "Error: No Python installation found."
    echo "Please install Python 3.8+ or uv first."
    exit 1
fi

# Verify installation
echo ""
echo "Verifying installation..."
if "$VENV_DIR/bin/python" -c "import fitz, pdfplumber, reportlab; print('All packages installed successfully')" 2>/dev/null; then
    echo ""
    echo "Environment setup complete!"
    echo "Virtual environment: $VENV_DIR"
    echo "Python executable: $VENV_DIR/bin/python"
else
    echo "Error: Package verification failed."
    exit 1
fi
