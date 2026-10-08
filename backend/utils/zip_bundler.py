"""
ZIP Bundler - Creates project bundles for download

Packages all project files into a single downloadable ZIP archive.
"""

import zipfile
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

class ZipBundler:
    """Creates ZIP bundles of project files."""
    
    def __init__(self, request_id: str, output_dir: Optional[Path] = None):
        """
        Initialize ZIP bundler.
        
        Args:
            request_id: Unique request identifier
            output_dir: Output directory for the bundle
        """
        self.request_id = request_id
        self.output_dir = output_dir or Path(f"output/{request_id}")
        self.bundle_path = self.output_dir / "project_bundle.zip"
        
        # Set up logging
        self.logger = logging.getLogger(f"ZipBundler_{request_id}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)
    
    def create_bundle(
        self,
        captioned_video_path: Optional[Path] = None,
        project_path: Optional[Path] = None,
        original_video_path: Optional[Path] = None,
        script_path: Optional[Path] = None,
        timestamps_path: Optional[Path] = None,
        voiceover_path: Optional[Path] = None,
        caption_style: str = "TikTok Bold",
        additional_files: Optional[Dict[str, Path]] = None
    ) -> Path:
        """
        Create a comprehensive project bundle.
        
        Args:
            captioned_video_path: Path to video with captions
            project_path: Path to CapCut project file
            original_video_path: Path to original video (no captions)
            script_path: Path to script file
            timestamps_path: Path to timestamps JSON
            voiceover_path: Path to voiceover audio file
            caption_style: Caption style used
            additional_files: Additional files to include
        
        Returns:
            Path to created ZIP bundle
        """
        self.logger.info(f"Creating project bundle for {self.request_id}")
        
        try:
            with zipfile.ZipFile(self.bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add main output files
                if captioned_video_path and captioned_video_path.exists():
                    zipf.write(captioned_video_path, 'captioned_video.mp4')
                    self.logger.info("Added captioned video")
                
                if project_path and project_path.exists():
                    zipf.write(project_path, 'project.capcut')
                    self.logger.info("Added CapCut project file")
                
                # Add original assets in assets/ directory
                if original_video_path and original_video_path.exists():
                    zipf.write(original_video_path, f'assets/original_video{original_video_path.suffix}')
                    self.logger.info("Added original video")
                
                if script_path and script_path.exists():
                    zipf.write(script_path, 'assets/script.txt')
                    self.logger.info("Added script")
                
                if timestamps_path and timestamps_path.exists():
                    zipf.write(timestamps_path, 'assets/timestamps.json')
                    self.logger.info("Added timestamps")
                
                if voiceover_path and voiceover_path.exists():
                    zipf.write(voiceover_path, f'assets/voiceover{voiceover_path.suffix}')
                    self.logger.info("Added voiceover")
                
                # Create and add metadata
                metadata = self._create_metadata(
                    caption_style,
                    captioned_video_path,
                    project_path,
                    original_video_path
                )
                
                metadata_path = self.output_dir / 'bundle_metadata.json'
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                zipf.write(metadata_path, 'assets/metadata.json')
                self.logger.info("Added metadata")
                
                # Add logs if they exist
                self._add_logs(zipf)
                
                # Add any additional files
                if additional_files:
                    for name, path in additional_files.items():
                        if path and path.exists():
                            zipf.write(path, f'extras/{name}')
                            self.logger.info(f"Added additional file: {name}")
                
                # Add README
                self._add_readme(zipf, metadata)
            
            # Get bundle size
            bundle_size = self.bundle_path.stat().st_size / (1024 * 1024)
            self.logger.info(f"Bundle created successfully: {bundle_size:.2f} MB")
            
            return self.bundle_path
            
        except Exception as e:
            self.logger.error(f"Failed to create bundle: {e}")
            raise
    
    def _create_metadata(
        self,
        caption_style: str,
        captioned_video_path: Optional[Path],
        project_path: Optional[Path],
        original_video_path: Optional[Path]
    ) -> Dict:
        """Create metadata for the bundle."""
        metadata = {
            'request_id': self.request_id,
            'created_at': datetime.now().isoformat(),
            'caption_style': caption_style,
            'files': {},
            'processing_info': {
                'platform': os.uname().sysname if hasattr(os, 'uname') else 'Unknown',
                'capcut_version': os.getenv('CAPCUT_VERSION', 'unknown')
            }
        }
        
        # Add file information
        if captioned_video_path and captioned_video_path.exists():
            metadata['files']['captioned_video'] = {
                'size_mb': captioned_video_path.stat().st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(captioned_video_path.stat().st_ctime).isoformat()
            }
        
        if project_path and project_path.exists():
            metadata['files']['project'] = {
                'size_mb': project_path.stat().st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(project_path.stat().st_ctime).isoformat()
            }
        
        if original_video_path and original_video_path.exists():
            metadata['files']['original_video'] = {
                'size_mb': original_video_path.stat().st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(original_video_path.stat().st_ctime).isoformat()
            }
        
        return metadata
    
    def _add_logs(self, zipf: zipfile.ZipFile):
        """Add log files to the bundle."""
        log_dir = Path("logs")
        
        if log_dir.exists():
            # Add main processing log
            main_log = log_dir / f"capcut_{self.request_id}.log"
            if main_log.exists():
                zipf.write(main_log, 'logs/processing.log')
                self.logger.info("Added processing log")
            
            # Add error log if exists
            error_log = log_dir / f"capcut_errors_{self.request_id}.log"
            if error_log.exists():
                zipf.write(error_log, 'logs/errors.log')
                self.logger.info("Added error log")
            
            # Add processor log
            processor_log = log_dir / f"capcut_processor_{self.request_id}.log"
            if processor_log.exists():
                zipf.write(processor_log, 'logs/processor.log')
                self.logger.info("Added processor log")
    
    def _add_readme(self, zipf: zipfile.ZipFile, metadata: Dict):
        """Add README file to the bundle."""
        readme_content = f"""# CapCut Project Bundle

## Request ID: {self.request_id}
## Created: {metadata['created_at']}

This bundle contains all files from your CapCut video processing request.

## Contents:

### Main Files:
- `captioned_video.mp4` - Final video with captions applied
- `project.capcut` - CapCut project file (can be opened in CapCut for further editing)

### Assets (Original Files):
- `assets/original_video.*` - Original video without captions
- `assets/script.txt` - Script used for video generation
- `assets/timestamps.json` - Timestamp data for video segments
- `assets/voiceover.*` - Voiceover audio file (if provided)
- `assets/metadata.json` - Processing metadata

### Logs (For Debugging):
- `logs/processing.log` - Main processing log
- `logs/errors.log` - Error log (if any errors occurred)
- `logs/processor.log` - Detailed processor log

## Caption Style Applied: {metadata.get('caption_style', 'Unknown')}

## How to Use:
1. Extract this ZIP file to a folder
2. The `captioned_video.mp4` is ready for upload to TikTok/social media
3. To edit further, open `project.capcut` in CapCut desktop application
4. Original assets are in the `assets/` folder for reference

## Support:
If you encounter any issues, please provide the Request ID and logs from the `logs/` folder.

---
Generated by TikTok Video Ad Automation Tool
"""
        
        # Create temporary README file
        readme_path = self.output_dir / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        zipf.write(readme_path, 'README.md')
        
        # Clean up temporary file
        readme_path.unlink()
    
    def extract_bundle(self, extract_to: Optional[Path] = None) -> Path:
        """
        Extract a bundle for inspection or modification.
        
        Args:
            extract_to: Directory to extract to
        
        Returns:
            Path to extraction directory
        """
        if not self.bundle_path.exists():
            raise FileNotFoundError(f"Bundle not found: {self.bundle_path}")
        
        extract_dir = extract_to or self.output_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(self.bundle_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        self.logger.info(f"Bundle extracted to: {extract_dir}")
        return extract_dir
    
    def get_bundle_info(self) -> Dict:
        """Get information about the bundle without extracting."""
        if not self.bundle_path.exists():
            return {'error': 'Bundle not found'}
        
        info = {
            'path': str(self.bundle_path),
            'size_mb': self.bundle_path.stat().st_size / (1024 * 1024),
            'created': datetime.fromtimestamp(self.bundle_path.stat().st_ctime).isoformat(),
            'files': []
        }
        
        with zipfile.ZipFile(self.bundle_path, 'r') as zipf:
            for file_info in zipf.filelist:
                info['files'].append({
                    'name': file_info.filename,
                    'size': file_info.file_size,
                    'compressed_size': file_info.compress_size
                })
        
        return info


def create_project_bundle(
    request_id: str,
    result: Dict,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Convenience function to create a project bundle from processing results.
    
    Args:
        request_id: Request identifier
        result: Processing result dictionary
        output_dir: Optional output directory
    
    Returns:
        Path to created bundle
    """
    bundler = ZipBundler(request_id, output_dir)
    
    return bundler.create_bundle(
        captioned_video_path=Path(result.get('captioned_video_path')) if result.get('captioned_video_path') else None,
        project_path=Path(result.get('project_path')) if result.get('project_path') else None,
        original_video_path=Path(result.get('video_path')) if result.get('video_path') else None,
        script_path=Path(result.get('script_path')) if result.get('script_path') else None,
        timestamps_path=Path(result.get('timestamps_path')) if result.get('timestamps_path') else None,
        voiceover_path=Path(result.get('voiceover_path')) if result.get('voiceover_path') else None,
        caption_style=result.get('caption_metadata', {}).get('style', 'TikTok Bold')
    )