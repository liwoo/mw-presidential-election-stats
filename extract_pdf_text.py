#!/usr/bin/env python3
"""
PDF Text Extraction Utility
Extracts text from PDF files for parliamentary data processing
"""

import sys
import os
from pathlib import Path

def extract_with_basic_method(pdf_path, output_path):
    """Try basic PDF text extraction"""
    try:
        # Try using PyPDF2 first
        import PyPDF2
        
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
        
        with open(output_path, 'w', encoding='utf-8') as text_file:
            text_file.write(text_content)
        
        return True, "Success with PyPDF2"
    
    except ImportError:
        return False, "PyPDF2 not available"
    except Exception as e:
        return False, f"PyPDF2 error: {str(e)}"

def extract_with_pdfplumber(pdf_path, output_path):
    """Try PDF text extraction with pdfplumber"""
    try:
        import pdfplumber
        
        text_content = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content += text + "\n"
        
        with open(output_path, 'w', encoding='utf-8') as text_file:
            text_file.write(text_content)
        
        return True, "Success with pdfplumber"
    
    except ImportError:
        return False, "pdfplumber not available"
    except Exception as e:
        return False, f"pdfplumber error: {str(e)}"

def extract_with_pdftotext(pdf_path, output_path):
    """Try using system pdftotext command if available"""
    try:
        import subprocess
        
        # Try using pdftotext system command
        result = subprocess.run(['pdftotext', pdf_path, output_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "Success with pdftotext"
        else:
            return False, f"pdftotext error: {result.stderr}"
    
    except FileNotFoundError:
        return False, "pdftotext command not found"
    except Exception as e:
        return False, f"pdftotext error: {str(e)}"

def main():
    """Main function to extract PDF text"""
    pdf_path = Path(r"C:\Users\lacso\Git\mw-presidential-election-stats\data\2019-Parliamentary-results.pdf")
    output_path = Path(r"C:\Users\lacso\Git\mw-presidential-election-stats\data\2019-Parliamentary-results.pdf.txt")
    
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"🔍 Extracting text from: {pdf_path.name}")
    print("Trying different extraction methods...")
    
    # Try different extraction methods
    methods = [
        ("pdfplumber", extract_with_pdfplumber),
        ("PyPDF2", extract_with_basic_method),
        ("pdftotext", extract_with_pdftotext)
    ]
    
    for method_name, method_func in methods:
        print(f"\n⏳ Trying {method_name}...")
        success, message = method_func(pdf_path, output_path)
        
        if success:
            print(f"✅ {message}")
            
            # Verify the output
            if output_path.exists():
                file_size = output_path.stat().st_size
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                
                print(f"📄 Text file created: {output_path.name}")
                print(f"📊 File size: {file_size:,} bytes")
                print(f"📝 Lines: {lines:,}")
                
                # Show first few lines as preview
                preview_lines = content.split('\n')[:10]
                print(f"\n📖 Preview (first 10 lines):")
                for i, line in enumerate(preview_lines, 1):
                    if line.strip():
                        print(f"{i:2}: {line[:80]}{'...' if len(line) > 80 else ''}")
                
                return
            else:
                print(f"❌ Output file was not created")
        else:
            print(f"❌ {message}")
    
    print("\n❌ All extraction methods failed.")
    print("📝 Manual extraction required:")
    print("1. Open the PDF file manually")
    print("2. Select all text (Ctrl+A)")
    print("3. Copy (Ctrl+C)")
    print("4. Paste into a text editor")
    print(f"5. Save as: {output_path}")

if __name__ == "__main__":
    main()