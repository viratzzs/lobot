#!/usr/bin/env python3
"""
Script to remove duplicate PDF files within a directory
Uses file hashing to identify identical files and removes duplicates
"""

import os
import hashlib
from collections import defaultdict
from loguru import logger

def calculate_file_hash(filepath, chunk_size=8192):
    """Calculate SHA-256 hash of a file"""
    try:
        hash_sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {filepath}: {str(e)}")
        return None

def find_duplicate_pdfs_by_name(directory):
    """Find duplicate PDF files by analyzing filename patterns"""
    name_to_files = defaultdict(list)
    pdf_files = []
    
    # Get all PDF files in the directory
    try:
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    pdf_files.append(filepath)
    except Exception as e:
        logger.error(f"Error listing directory {directory}: {str(e)}")
        return {}
    
    logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
    
    # Group files by base name (removing duplicate indicators)
    for filepath in pdf_files:
        filename = os.path.basename(filepath)
        
        # Remove common duplicate indicators like (1), (2), etc.
        base_name = filename
        
        # Remove patterns like (1), (2), (3) etc. at the end before .pdf
        import re
        base_name = re.sub(r'\(\d+\)\.PDF$', '.PDF', base_name, flags=re.IGNORECASE)
        base_name = re.sub(r'\(\d+\)\.pdf$', '.pdf', base_name, flags=re.IGNORECASE)
        
        name_to_files[base_name].append(filepath)
    
    # Find duplicates (base names with more than one file)
    duplicates = {base_name: files for base_name, files in name_to_files.items() if len(files) > 1}
    
    return duplicates

def remove_duplicates(duplicates, keep_strategy='original'):
    """
    Remove duplicate files based on strategy
    
    Args:
        duplicates: Dictionary of base_name -> list of file paths
        keep_strategy: 'original', 'first', 'last', 'shortest_name', 'longest_name'
    """
    total_removed = 0
    total_space_saved = 0
    
    for base_name, file_list in duplicates.items():
        logger.info(f"Found {len(file_list)} duplicate files for: {base_name}")
        
        # Sort files based on strategy to determine which to keep
        if keep_strategy == 'original':
            # Keep the file without (1), (2) etc. suffix (the original)
            original_files = [f for f in file_list if not any(f.endswith(f'({i}).pdf') or f.endswith(f'({i}).PDF') for i in range(1, 20))]
            if original_files:
                files_to_keep = [original_files[0]]
                files_to_remove = [f for f in file_list if f not in files_to_keep]
            else:
                # If no original found, keep first
                files_to_keep = [file_list[0]]
                files_to_remove = file_list[1:]
        elif keep_strategy == 'first':
            files_to_keep = [file_list[0]]
            files_to_remove = file_list[1:]
        elif keep_strategy == 'last':
            files_to_keep = [file_list[-1]]
            files_to_remove = file_list[:-1]
        elif keep_strategy == 'shortest_name':
            sorted_files = sorted(file_list, key=lambda x: len(os.path.basename(x)))
            files_to_keep = [sorted_files[0]]
            files_to_remove = sorted_files[1:]
        elif keep_strategy == 'longest_name':
            sorted_files = sorted(file_list, key=lambda x: len(os.path.basename(x)), reverse=True)
            files_to_keep = [sorted_files[0]]
            files_to_remove = sorted_files[1:]
        else:
            files_to_keep = [file_list[0]]
            files_to_remove = file_list[1:]
        
        # Log which file we're keeping
        logger.info(f"Keeping: {os.path.basename(files_to_keep[0])}")
        
        # Remove duplicate files
        for filepath in files_to_remove:
            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                total_removed += 1
                total_space_saved += file_size
                logger.info(f"Removed: {os.path.basename(filepath)} ({file_size:,} bytes)")
            except Exception as e:
                logger.error(f"Error removing {filepath}: {str(e)}")
    
    return total_removed, total_space_saved

def format_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def remove_duplicates_from_directory(directory, keep_strategy='first', dry_run=False):
    """
    Main function to remove duplicates from a directory
    
    Args:
        directory: Path to directory to clean
        keep_strategy: Which file to keep when duplicates found
        dry_run: If True, only show what would be removed without actually removing
    """
    if not os.path.exists(directory):
        logger.error(f"Directory does not exist: {directory}")
        return
    
    if not os.path.isdir(directory):
        logger.error(f"Path is not a directory: {directory}")
        return
    
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Scanning for duplicate PDFs in: {directory}")
    logger.info(f"Keep strategy: {keep_strategy}")
    
    # Find duplicates using filename patterns
    duplicates = find_duplicate_pdfs_by_name(directory)
    
    if not duplicates:
        logger.success("No duplicate PDF files found!")
        return
    
    # Count total duplicates
    total_duplicate_files = sum(len(files) - 1 for files in duplicates.values())
    logger.warning(f"Found {len(duplicates)} sets of duplicates involving {total_duplicate_files} files")
    
    # Show duplicate sets
    for i, (base_name, file_list) in enumerate(duplicates.items(), 1):
        logger.info(f"\nDuplicate set {i} (base name: {base_name}):")
        for filepath in file_list:
            size = os.path.getsize(filepath)
            logger.info(f"  - {os.path.basename(filepath)} ({format_size(size)})")
    
    if dry_run:
        logger.info(f"\nDRY RUN: Would remove {total_duplicate_files} duplicate files")
        return
    
    # Confirm removal
    try:
        confirm = input(f"\nRemove {total_duplicate_files} duplicate files? (y/N): ").strip().lower()
        if confirm != 'y':
            logger.info("Operation cancelled")
            return
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled")
        return
    
    # Remove duplicates
    logger.info("Removing duplicate files...")
    removed_count, space_saved = remove_duplicates(duplicates, keep_strategy)
    
    logger.success(f"Successfully removed {removed_count} duplicate files")
    logger.success(f"Space saved: {format_size(space_saved)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove duplicate PDF files from a directory")
    parser.add_argument("directory", nargs="?", default="sc", 
                       help="Directory to scan for duplicates (default: sc)")
    parser.add_argument("--strategy", choices=['original', 'first', 'last', 'shortest_name', 'longest_name'],
                       default='original', help="Which file to keep when duplicates found (default: original)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be removed without actually removing")
    
    args = parser.parse_args()
    
    # Get the directory path relative to script location
    script_dir = os.path.dirname(__file__)
    target_dir = os.path.join(script_dir, args.directory)
    
    remove_duplicates_from_directory(target_dir, args.strategy, args.dry_run)
