"""
pdf_converter.py
Converts PPTX to PDF using LibreOffice (cross-platform: Mac, Windows, Linux).
Falls back with a helpful message if LibreOffice isn't installed.
"""

import subprocess
import sys
import os
from pathlib import Path


def find_soffice():
    """Find LibreOffice soffice binary on Mac, Windows, or Linux."""
    candidates = [
        # Linux
        "soffice",
        "libreoffice",
        # macOS
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        # Windows
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def convert_pptx_to_pdf(pptx_path: str, output_dir: str = None) -> str | None:
    """
    Convert a PPTX file to PDF.
    Returns the PDF path if successful, None if LibreOffice not found.
    """
    pptx_path = Path(pptx_path)
    if output_dir is None:
        output_dir = pptx_path.parent

    soffice = find_soffice()

    if not soffice:
        print("  ⚠️  LibreOffice not found — skipping PDF conversion.")
        print("     To enable PDF export, install LibreOffice from: https://www.libreoffice.org/download/")
        print("     Then re-run and PDF will be generated automatically.")
        return None

    print(f"  📄 Converting to PDF using LibreOffice...")

    try:
        result = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf",
             "--outdir", str(output_dir), str(pptx_path)],
            capture_output=True, text=True, timeout=120
        )

        pdf_path = Path(output_dir) / (pptx_path.stem + ".pdf")
        if pdf_path.exists():
            print(f"  💾 Saved PDF:  {pdf_path}")
            return str(pdf_path)
        else:
            print(f"  ⚠️  PDF conversion may have failed. stderr: {result.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print("  ⚠️  PDF conversion timed out. Try manually opening the PPTX and exporting as PDF.")
        return None
    except Exception as e:
        print(f"  ⚠️  PDF conversion error: {e}")
        return None
