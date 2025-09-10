#!/usr/bin/env python3
"""
Simple script to remove duplicate and corrupt PDF files
Usage: python remove_duplicates.py [directory] [options]
"""

import os
import re
from collections import defaultdict
from loguru import logger

# Configure simple logging
logger.remove()
logger.add(lambda msg: print(msg), format="{message}", level="INFO")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

def is_pdf_corrupt(filepath):
    """Check if PDF is corrupt"""
    if not PYMUPDF_AVAILABLE:
        return False
    
    try:
        doc = fitz.open(filepath)
        if len(doc) == 0:
            doc.close()
            return True
        doc[0].get_text()  # Try to read first page
        doc.close()
        return False
    except:
        return True

def normalize_filename(filename):
    """Remove (1), (2) etc. from filename"""
    name, ext = os.path.splitext(filename)
    normalized = re.sub(r'\(\d+\)$', '', name).strip()
    return normalized + ext

def find_duplicates_and_corrupt(directory, recursive=False, check_corruption=False):
    """Find duplicate and corrupt PDFs"""
    pdf_files = []
    
    # Get all PDF files
    if recursive:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    pdf_files.append(filepath)
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Find duplicates
    name_groups = defaultdict(list)
    for filepath in pdf_files:
        filename = os.path.basename(filepath)
        normalized_name = normalize_filename(filename)
        name_groups[normalized_name].append(filepath)
    
    duplicates = {name: files for name, files in name_groups.items() if len(files) > 1}
    
    # Find corrupt files
    corrupt_files = []
    if check_corruption and PYMUPDF_AVAILABLE:
        print("Checking for corrupt files...")
        for filepath in pdf_files:
            if is_pdf_corrupt(filepath):
                corrupt_files.append(filepath)
    elif check_corruption:
        print("PyMuPDF not available - install with: pip install PyMuPDF")
    
    return duplicates, corrupt_files

def remove_files(duplicates, corrupt_files, keep_strategy='original'):
    """Remove duplicate and corrupt files"""
    total_removed = 0
    total_size = 0
    
    # Remove duplicates
    for name, files in duplicates.items():
        if keep_strategy == 'original':
            # Keep file without (1), (2) suffix
            original = [f for f in files if normalize_filename(os.path.basename(f)) == os.path.basename(f)]
            to_keep = original[0] if original else files[0]
        else:
            to_keep = files[0]
        
        to_remove = [f for f in files if f != to_keep]
        
        for filepath in to_remove:
            try:
                size = os.path.getsize(filepath)
                os.remove(filepath)
                total_removed += 1
                total_size += size
                print(f"Removed duplicate: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"Error removing {filepath}: {e}")
    
    # Remove corrupt files
    for filepath in corrupt_files:
        try:
            size = os.path.getsize(filepath)
            os.remove(filepath)
            total_removed += 1
            total_size += size
            print(f"Removed corrupt: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Error removing {filepath}: {e}")
    
    return total_removed, total_size

def clean_pdfs(directory, recursive=False, check_corruption=False, dry_run=False):
    """Main function to clean PDFs"""
    if not os.path.exists(directory):
        print(f"Directory does not exist: {directory}")
        return
    
    print(f"Scanning: {directory}")
    if recursive:
        print("Recursive scan enabled")
    if check_corruption:
        print("Corruption check enabled")
    
    # Find problems
    duplicates, corrupt_files = find_duplicates_and_corrupt(directory, recursive, check_corruption)
    
    # Report findings
    duplicate_count = sum(len(files) - 1 for files in duplicates.values())
    corrupt_count = len(corrupt_files)
    
    if duplicate_count == 0 and corrupt_count == 0:
        print("No issues found!")
        return
    
    print(f"\nFound:")
    if duplicate_count > 0:
        print(f"  {duplicate_count} duplicate files")
    if corrupt_count > 0:
        print(f"  {corrupt_count} corrupt files")
    
    if dry_run:
        print(f"\nDRY RUN: Would remove {duplicate_count + corrupt_count} files")
        return
    
    # Confirm removal
    try:
        confirm = input(f"\nRemove {duplicate_count + corrupt_count} files? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled")
            return
    except KeyboardInterrupt:
        print("\nCancelled")
        return
    
    # Remove files
    removed, size_saved = remove_files(duplicates, corrupt_files)
    mb_saved = size_saved / (1024 * 1024)
    print(f"\nRemoved {removed} files ({mb_saved:.1f} MB saved)")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove duplicate and corrupt PDF files")
    parser.add_argument("directory", nargs="?", default=".", 
                    help="Directory to clean (default: current)")
    parser.add_argument("--recursive", "-r", action="store_true",
                    help="Scan subdirectories")
    parser.add_argument("--check-corruption", "-c", action="store_true",
                    help="Also check for corrupt PDFs")
    parser.add_argument("--dry-run", "-d", action="store_true",
                    help="Show what would be removed")
    
    args = parser.parse_args()
    
    # Get target directory
    if args.directory == ".":
        target_dir = os.getcwd()
    elif os.path.isabs(args.directory):
        target_dir = args.directory
    else:
        script_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up from src/scraping/ to project root
        target_dir = os.path.join(project_root, args.directory)
    
    clean_pdfs(target_dir, args.recursive, args.check_corruption, args.dry_run)
