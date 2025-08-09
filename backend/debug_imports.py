#!/usr/bin/env python3
"""
Debug script - pārbauda PDF imports
"""

import sys
sys.path.insert(0, '.')

print("=== PDF IMPORTS DEBUG ===")

print("1. Testing PyMuPDF...")
try:
    import fitz  # PyMuPDF
    print(f"✅ PyMuPDF successful: {fitz.__version__}")
    PYMUPDF_AVAILABLE = True
except ImportError as e:
    print(f"❌ PyMuPDF failed: {e}")
    PYMUPDF_AVAILABLE = False

print("2. Testing pdf2image...")
try:
    from pdf2image import convert_from_path
    print("✅ pdf2image successful")
    PDF2IMAGE_AVAILABLE = True
except ImportError as e:
    print(f"❌ pdf2image failed: {e}")
    PDF2IMAGE_AVAILABLE = False

print(f"\nResult:")
print(f"PYMUPDF_AVAILABLE: {PYMUPDF_AVAILABLE}")
print(f"PDF2IMAGE_AVAILABLE: {PDF2IMAGE_AVAILABLE}")

print("\n3. Testing PDF Processor import...")
try:
    from app.services.ocr.pdf_processor import PDFProcessor
    processor = PDFProcessor()
    print(f"✅ PDF Processor OK, methods: {processor.available_methods}")
except Exception as e:
    print(f"❌ PDF Processor failed: {e}")

print("\n=== DEBUG COMPLETE ===")
