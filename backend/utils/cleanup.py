#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary files and free up disk space.

This script safely removes temporary files, old logs, and cache files
without affecting the functionality of the application.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import argparse


class ProjectCleaner:
    """Handles cleanup of unnecessary files in the project."""
    
    def __init__(self, dry_run=False):
        """Initialize cleaner with project paths."""
        self.dry_run = dry_run
        self.backend_dir = Path(__file__).parent
        self.project_dir = self.backend_dir.parent
        self.freed_space = 0
        
    def format_size(self, bytes_size):
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    def get_dir_size(self, path):
        """Calculate total size of a directory."""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_dir_size(entry.path)
        except (OSError, PermissionError):
            pass
        return total
    
    def clean_temp_files(self):
        """Remove temporary video and processing files."""
        print("\n🧹 Cleaning temporary files...")
        temp_dir = self.backend_dir / 'temp'
        
        if not temp_dir.exists():
            return
            
        patterns = [
            'merged_full_*.mp4',
            'merged_compressed_*.mp4', 
            'temp_segment_*.mp4',
            'concat_*.txt',
            'temp_*.mp4',
            '*.tmp'
        ]
        
        for pattern in patterns:
            for file in temp_dir.glob(pattern):
                size = file.stat().st_size
                if self.dry_run:
                    print(f"  Would remove: {file.name} ({self.format_size(size)})")
                else:
                    file.unlink()
                    print(f"  Removed: {file.name} ({self.format_size(size)})")
                self.freed_space += size
    
    def clean_logs(self, days_to_keep=7):
        """Remove old log files."""
        print(f"\n📝 Cleaning log files older than {days_to_keep} days...")
        logs_dir = self.backend_dir / 'logs'
        
        if not logs_dir.exists():
            return
            
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_file in logs_dir.glob('*.log'):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                size = log_file.stat().st_size
                if self.dry_run:
                    print(f"  Would remove: {log_file.name} ({self.format_size(size)})")
                else:
                    log_file.unlink()
                    print(f"  Removed: {log_file.name} ({self.format_size(size)})")
                self.freed_space += size
    
    def clean_python_cache(self):
        """Remove Python cache files and directories."""
        print("\n🐍 Cleaning Python cache...")
        
        # Remove __pycache__ directories
        for cache_dir in self.backend_dir.rglob('__pycache__'):
            size = self.get_dir_size(cache_dir)
            if self.dry_run:
                print(f"  Would remove: {cache_dir.relative_to(self.backend_dir)} ({self.format_size(size)})")
            else:
                shutil.rmtree(cache_dir, ignore_errors=True)
                print(f"  Removed: {cache_dir.relative_to(self.backend_dir)} ({self.format_size(size)})")
            self.freed_space += size
        
        # Remove .pyc files
        for pyc_file in self.backend_dir.rglob('*.pyc'):
            size = pyc_file.stat().st_size
            if self.dry_run:
                print(f"  Would remove: {pyc_file.name}")
            else:
                pyc_file.unlink()
            self.freed_space += size
    
    def clean_backup_files(self):
        """Remove backup and duplicate files."""
        print("\n💾 Cleaning backup files...")
        
        patterns = [
            '*.backup',
            '*.bak',
            '*_old.py',
            '*_original.py',
            '*.orig'
        ]
        
        for pattern in patterns:
            for file in self.backend_dir.rglob(pattern):
                size = file.stat().st_size
                if self.dry_run:
                    print(f"  Would remove: {file.relative_to(self.backend_dir)} ({self.format_size(size)})")
                else:
                    file.unlink()
                    print(f"  Removed: {file.relative_to(self.backend_dir)} ({self.format_size(size)})")
                self.freed_space += size
    
    def clean_debug_files(self):
        """Remove debug response files."""
        print("\n🐛 Cleaning debug files...")
        debug_dir = self.backend_dir / 'debug_responses'
        
        if debug_dir.exists():
            size = self.get_dir_size(debug_dir)
            if self.dry_run:
                print(f"  Would remove: debug_responses/ ({self.format_size(size)})")
            else:
                shutil.rmtree(debug_dir, ignore_errors=True)
                print(f"  Removed: debug_responses/ ({self.format_size(size)})")
            self.freed_space += size
    
    def clean_output_files(self, keep_recent=True):
        """Optionally clean old output files."""
        print("\n📦 Checking output files...")
        output_dir = self.project_dir / 'output'
        
        if not output_dir.exists():
            return
        
        if keep_recent:
            print("  Keeping all output files (use --clean-outputs to remove)")
            return
            
        # Only remove debug directories
        for debug_dir in output_dir.glob('debug_*'):
            size = self.get_dir_size(debug_dir)
            if self.dry_run:
                print(f"  Would remove: {debug_dir.name} ({self.format_size(size)})")
            else:
                shutil.rmtree(debug_dir, ignore_errors=True)
                print(f"  Removed: {debug_dir.name} ({self.format_size(size)})")
            self.freed_space += size
    
    def clean_all(self, clean_outputs=False, log_days=7):
        """Run all cleanup operations."""
        print("🚀 Starting cleanup process...")
        if self.dry_run:
            print("  (DRY RUN - no files will be deleted)")
        
        self.clean_temp_files()
        self.clean_logs(days_to_keep=log_days)
        self.clean_python_cache()
        self.clean_backup_files()
        self.clean_debug_files()
        self.clean_output_files(keep_recent=not clean_outputs)
        
        print(f"\n✅ Cleanup complete!")
        print(f"   Space {'would be' if self.dry_run else ''} freed: {self.format_size(self.freed_space)}")


def main():
    """Main entry point for cleanup script."""
    parser = argparse.ArgumentParser(description='Clean up unnecessary files from the project')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--clean-outputs', action='store_true',
                       help='Also clean old output files (default: keep all outputs)')
    parser.add_argument('--log-days', type=int, default=7,
                       help='Keep logs from the last N days (default: 7)')
    
    args = parser.parse_args()
    
    cleaner = ProjectCleaner(dry_run=args.dry_run)
    cleaner.clean_all(
        clean_outputs=args.clean_outputs,
        log_days=args.log_days
    )


if __name__ == '__main__':
    main()