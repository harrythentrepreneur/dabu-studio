"""
Debug data collector for TikTok Video Ad Automation pipeline.

This module collects comprehensive debugging information at each stage
of the processing pipeline to help diagnose timing and synchronization issues.
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess

from .logger import get_logger

logger = get_logger(__name__)


class DebugCollector:
    """Collects and organizes debug data throughout the processing pipeline."""
    
    def __init__(self, request_id: str, output_dir: Optional[Path] = None):
        """
        Initialize debug collector with a unique session.
        
        Args:
            request_id: Unique identifier for this processing session
            output_dir: Base directory for debug output
        """
        self.request_id = request_id
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create debug folder structure
        base_dir = output_dir or Path(__file__).parent.parent / 'debug_output'
        self.debug_dir = base_dir / f"debug_{self.timestamp}_{request_id}"
        
        # Create subdirectories
        self.dirs = {
            'root': self.debug_dir,
            'whisper': self.debug_dir / '01_whisper_analysis',
            'gemini': self.debug_dir / '02_gemini_response',
            'extraction': self.debug_dir / '03_segment_extraction',
            'compilation': self.debug_dir / '04_compilation',
            'validation': self.debug_dir / '05_validation',
            'segments': self.debug_dir / 'extracted_segments',
            'commands': self.debug_dir / 'ffmpeg_commands'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize data collection
        self.data = {
            'request_id': request_id,
            'timestamp': self.timestamp,
            'stages': {},
            'errors': [],
            'warnings': [],
            'ffmpeg_commands': []
        }
        
        logger.info(f"Debug collector initialized: {self.debug_dir}")
        
        # Create initial info file
        self._write_json('session_info.json', {
            'request_id': request_id,
            'started_at': self.timestamp,
            'debug_directory': str(self.debug_dir)
        })
    
    def collect_whisper_data(self, 
                            voiceover_path: Path,
                            voiceover_duration: float,
                            raw_segments: List[Dict],
                            processed_segments: List[Dict]) -> None:
        """
        Collect Whisper API analysis data.
        
        Args:
            voiceover_path: Path to voiceover file
            voiceover_duration: Total duration of voiceover
            raw_segments: Raw segments from Whisper
            processed_segments: Processed/merged segments
        """
        whisper_data = {
            'voiceover_file': str(voiceover_path),
            'voiceover_duration': voiceover_duration,
            'raw_segments_count': len(raw_segments),
            'processed_segments_count': len(processed_segments),
            'raw_segments': raw_segments,
            'processed_segments': processed_segments
        }
        
        # Calculate timing statistics
        if processed_segments:
            durations = [seg['duration'] for seg in processed_segments]
            whisper_data['statistics'] = {
                'total_duration': sum(durations),
                'average_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'segments': []
            }
            
            # Add per-segment analysis
            for i, seg in enumerate(processed_segments, 1):
                whisper_data['statistics']['segments'].append({
                    'number': i,
                    'text': seg['text'][:50] + '...' if len(seg['text']) > 50 else seg['text'],
                    'start': seg['start'],
                    'end': seg['end'],
                    'duration': seg['duration']
                })
        
        self.data['stages']['whisper'] = whisper_data
        self._write_json('01_whisper_analysis/whisper_data.json', whisper_data)
        
        # Create readable summary
        self._write_summary('01_whisper_analysis/summary.txt', 
                          self._format_whisper_summary(whisper_data))
        
        logger.info(f"Collected Whisper data: {len(processed_segments)} segments")
    
    def collect_gemini_response(self,
                               gemini_response: Dict,
                               voiceover_segments: Optional[List[Dict]] = None) -> None:
        """
        Collect Gemini API response data.
        
        Args:
            gemini_response: Full Gemini response
            voiceover_segments: Original voiceover segments for comparison
        """
        gemini_data = {
            'total_duration': gemini_response.get('total_duration'),
            'target_duration': gemini_response.get('target_duration'),
            'segments_count': len(gemini_response.get('script_segments', [])),
            'segments': []
        }
        
        # Analyze each segment
        for seg in gemini_response.get('script_segments', []):
            segment_analysis = {
                'segment_number': seg.get('segment_number'),
                'text': seg.get('segment_text'),
                'video_start': seg.get('start_timestamp'),
                'video_end': seg.get('end_timestamp'),
                'duration': seg.get('duration_seconds'),
                'confidence': seg.get('confidence'),
                'description': seg.get('visual_description', '')[:100]
            }
            
            # Compare with voiceover if available
            if voiceover_segments and seg.get('segment_number'):
                idx = seg['segment_number'] - 1
                if idx < len(voiceover_segments):
                    vo_seg = voiceover_segments[idx]
                    segment_analysis['voiceover_comparison'] = {
                        'voiceover_duration': vo_seg['duration'],
                        'gemini_duration': seg.get('duration_seconds'),
                        'duration_diff': abs(vo_seg['duration'] - seg.get('duration_seconds', 0))
                    }
            
            gemini_data['segments'].append(segment_analysis)
        
        self.data['stages']['gemini'] = gemini_data
        self._write_json('02_gemini_response/gemini_data.json', gemini_data)
        self._write_json('02_gemini_response/raw_response.json', gemini_response)
        
        # Create comparison table
        self._write_summary('02_gemini_response/comparison.txt',
                          self._format_gemini_comparison(gemini_data, voiceover_segments))
        
        logger.info(f"Collected Gemini response: {len(gemini_data['segments'])} segments")
    
    def collect_extraction_command(self,
                                  segment_num: int,
                                  ffmpeg_command: List[str],
                                  source_video: Path,
                                  output_path: Path,
                                  expected_duration: float,
                                  actual_duration: Optional[float] = None) -> None:
        """
        Collect FFmpeg extraction command and results.
        
        Args:
            segment_num: Segment number
            ffmpeg_command: Full FFmpeg command used
            source_video: Source video path
            output_path: Output segment path
            expected_duration: Expected duration
            actual_duration: Actual duration after extraction
        """
        extraction_data = {
            'segment_number': segment_num,
            'source_video': str(source_video),
            'output_file': str(output_path),
            'command': ' '.join(ffmpeg_command),
            'expected_duration': expected_duration,
            'actual_duration': actual_duration,
            'duration_error': abs(expected_duration - actual_duration) if actual_duration else None
        }
        
        # Store command
        self.data['ffmpeg_commands'].append(extraction_data)
        
        # Write individual command file
        cmd_file = self.dirs['commands'] / f"segment_{segment_num:03d}_command.txt"
        with open(cmd_file, 'w') as f:
            f.write(f"# Segment {segment_num} Extraction Command\n")
            f.write(f"# Expected duration: {expected_duration:.2f}s\n")
            f.write(f"# Actual duration: {actual_duration:.2f}s\n" if actual_duration else "")
            f.write(f"\n{' '.join(ffmpeg_command)}\n")
        
        # Copy extracted segment for inspection
        if output_path.exists():
            segment_copy = self.dirs['segments'] / f"segment_{segment_num:03d}.mp4"
            shutil.copy2(output_path, segment_copy)
            
            # Verify segment with ffprobe
            self._analyze_segment(segment_copy, segment_num)
        
        logger.debug(f"Collected extraction data for segment {segment_num}")
    
    def collect_final_compilation(self,
                                 final_video: Path,
                                 expected_duration: float,
                                 actual_duration: float,
                                 segment_order: List[int]) -> None:
        """
        Collect final compilation data.
        
        Args:
            final_video: Path to final compiled video
            expected_duration: Expected total duration
            actual_duration: Actual total duration
            segment_order: Order of segments in final video
        """
        compilation_data = {
            'final_video': str(final_video),
            'expected_duration': expected_duration,
            'actual_duration': actual_duration,
            'duration_error': abs(expected_duration - actual_duration),
            'segment_order': segment_order,
            'status': 'SUCCESS' if abs(expected_duration - actual_duration) < 0.5 else 'MISMATCH'
        }
        
        self.data['stages']['compilation'] = compilation_data
        self._write_json('04_compilation/compilation_data.json', compilation_data)
        
        # Create final summary
        self._create_final_report()
        
        logger.info(f"Collected compilation data: {compilation_data['status']}")
    
    def log_error(self, stage: str, error: str, details: Optional[Dict] = None) -> None:
        """Log an error during processing."""
        error_entry = {
            'stage': stage,
            'error': error,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.data['errors'].append(error_entry)
        self._write_json('errors.json', self.data['errors'])
        logger.error(f"Debug collector logged error in {stage}: {error}")
    
    def log_warning(self, stage: str, warning: str, details: Optional[Dict] = None) -> None:
        """Log a warning during processing."""
        warning_entry = {
            'stage': stage,
            'warning': warning,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.data['warnings'].append(warning_entry)
        self._write_json('warnings.json', self.data['warnings'])
        logger.warning(f"Debug collector logged warning in {stage}: {warning}")
    
    def _analyze_segment(self, segment_path: Path, segment_num: int) -> None:
        """Analyze extracted segment with ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=duration,r_frame_rate,width,height,codec_name',
                '-show_entries', 'format=duration',
                '-of', 'json',
                str(segment_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                
                analysis_file = self.dirs['segments'] / f"segment_{segment_num:03d}_analysis.json"
                with open(analysis_file, 'w') as f:
                    json.dump(probe_data, f, indent=2)
                
                # Extract key info
                format_duration = float(probe_data.get('format', {}).get('duration', 0))
                logger.debug(f"Segment {segment_num} verified: {format_duration:.3f}s")
                
        except Exception as e:
            logger.error(f"Failed to analyze segment {segment_num}: {e}")
    
    def _write_json(self, filename: str, data: Any) -> None:
        """Write JSON data to file."""
        filepath = self.debug_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _write_summary(self, filename: str, content: str) -> None:
        """Write text summary to file."""
        filepath = self.debug_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
    
    def _format_whisper_summary(self, data: Dict) -> str:
        """Format Whisper data as readable summary."""
        lines = [
            "WHISPER ANALYSIS SUMMARY",
            "=" * 50,
            f"Voiceover Duration: {data['voiceover_duration']:.2f}s",
            f"Raw Segments: {data['raw_segments_count']}",
            f"Processed Segments: {data['processed_segments_count']}",
            "",
            "SEGMENT BREAKDOWN:",
            "-" * 30
        ]
        
        if 'statistics' in data and 'segments' in data['statistics']:
            for seg in data['statistics']['segments']:
                lines.append(
                    f"Segment {seg['number']:2d}: [{seg['start']:6.2f} - {seg['end']:6.2f}] "
                    f"({seg['duration']:5.2f}s) - {seg['text']}"
                )
        
        return "\n".join(lines)
    
    def _format_gemini_comparison(self, gemini_data: Dict, voiceover_segments: Optional[List]) -> str:
        """Format Gemini comparison with voiceover."""
        lines = [
            "GEMINI vs VOICEOVER COMPARISON",
            "=" * 50,
            f"Total Duration: {gemini_data.get('total_duration', 0):.2f}s",
            f"Target Duration: {gemini_data.get('target_duration', 0):.2f}s",
            "",
            "SEGMENT TIMING COMPARISON:",
            "-" * 50,
            "Seg | Voiceover Dur | Gemini Dur | Diff  | Video Start | Video End",
            "-" * 70
        ]
        
        for seg in gemini_data['segments']:
            vo_dur = "N/A"
            diff = "N/A"
            
            if 'voiceover_comparison' in seg:
                vo_dur = f"{seg['voiceover_comparison']['voiceover_duration']:.2f}s"
                diff = f"{seg['voiceover_comparison']['duration_diff']:.2f}s"
            
            lines.append(
                f"{seg['segment_number']:3} | {vo_dur:13} | {seg['duration']:10.2f}s | "
                f"{diff:5} | {seg['video_start']:11} | {seg['video_end']:9}"
            )
        
        return "\n".join(lines)
    
    def _create_final_report(self) -> None:
        """Create comprehensive final report."""
        report_lines = [
            "FINAL DEBUG REPORT",
            "=" * 70,
            f"Request ID: {self.request_id}",
            f"Timestamp: {self.timestamp}",
            "",
            "PROCESSING PIPELINE SUMMARY",
            "-" * 40
        ]
        
        # Whisper summary
        if 'whisper' in self.data['stages']:
            whisper = self.data['stages']['whisper']
            report_lines.extend([
                "",
                "1. WHISPER ANALYSIS:",
                f"   - Voiceover Duration: {whisper['voiceover_duration']:.2f}s",
                f"   - Segments: {whisper['processed_segments_count']}",
            ])
        
        # Gemini summary
        if 'gemini' in self.data['stages']:
            gemini = self.data['stages']['gemini']
            report_lines.extend([
                "",
                "2. GEMINI RESPONSE:",
                f"   - Total Duration: {gemini['total_duration']:.2f}s",
                f"   - Segments: {gemini['segments_count']}",
            ])
        
        # Compilation summary
        if 'compilation' in self.data['stages']:
            comp = self.data['stages']['compilation']
            report_lines.extend([
                "",
                "3. FINAL COMPILATION:",
                f"   - Expected Duration: {comp['expected_duration']:.2f}s",
                f"   - Actual Duration: {comp['actual_duration']:.2f}s",
                f"   - Error: {comp['duration_error']:.2f}s",
                f"   - Status: {comp['status']}",
            ])
        
        # Errors and warnings
        if self.data['errors']:
            report_lines.extend([
                "",
                "ERRORS:",
                "-" * 20
            ])
            for error in self.data['errors']:
                report_lines.append(f"   [{error['stage']}] {error['error']}")
        
        if self.data['warnings']:
            report_lines.extend([
                "",
                "WARNINGS:",
                "-" * 20
            ])
            for warning in self.data['warnings']:
                report_lines.append(f"   [{warning['stage']}] {warning['warning']}")
        
        # FFmpeg commands summary
        if self.data['ffmpeg_commands']:
            report_lines.extend([
                "",
                "FFMPEG EXTRACTION SUMMARY:",
                "-" * 30
            ])
            for cmd in self.data['ffmpeg_commands']:
                error = cmd.get('duration_error', 0)
                status = "OK" if error and error < 0.1 else "ERROR" if error and error > 0.5 else "WARN"
                report_lines.append(
                    f"   Segment {cmd['segment_number']:2d}: {status:5} "
                    f"(expected: {cmd['expected_duration']:.2f}s, "
                    f"actual: {cmd.get('actual_duration', 0):.2f}s)"
                )
        
        report_lines.extend([
            "",
            "=" * 70,
            f"Debug data saved to: {self.debug_dir}"
        ])
        
        # Write report
        report_content = "\n".join(report_lines)
        self._write_summary('FINAL_REPORT.txt', report_content)
        
        # Also save complete data
        self._write_json('complete_debug_data.json', self.data)
        
        print(f"\n{'='*70}")
        print(f"DEBUG DATA COLLECTED: {self.debug_dir}")
        print(f"{'='*70}\n")
        print(report_content)