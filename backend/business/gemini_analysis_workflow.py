"""
Gemini analysis workflow for handling AI-powered video analysis.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from .base_workflow import BaseWorkflow
from core.gemini_client import GeminiClient
from models.schemas import GeminiResponse
from config.constants import STATUS_MESSAGES, PROCESSING_STEPS, DEFAULT_TARGET_DURATION
from utils.exceptions import GeminiAPIError, GeminiProcessingError


class GeminiAnalysisWorkflow(BaseWorkflow):
    """Workflow for Gemini AI analysis operations."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        super().__init__(temp_dir)
        self.gemini_client = GeminiClient()
        self._total_steps = 2  # Upload + Analysis
    
    def analyze_video_segments(
        self,
        compressed_video_path: Path,
        script: str,
        target_duration: float = DEFAULT_TARGET_DURATION,
        voiceover_segments: Optional[List[Dict]] = None,
        use_mock: bool = False
    ) -> GeminiResponse:
        """
        Analyze video and generate segment timestamps using Gemini AI.
        
        Args:
            compressed_video_path: Path to compressed video for analysis
            script: TikTok ad script text
            target_duration: Target video duration in seconds
            voiceover_segments: Optional voiceover timing data
            use_mock: Whether to use mock response for testing
            
        Returns:
            GeminiResponse with segment analysis
        """
        try:
            # Step 1: Upload video to Gemini
            self._current_step = PROCESSING_STEPS['UPLOADING_TO_AI']
            self.emit_status(
                "Uploading to AI",
                45,
                STATUS_MESSAGES['UPLOADING_TO_AI']
            )
            
            if use_mock:
                self.logger.warning("Using MOCK mode - skipping actual Gemini upload")
                gemini_input = "mock_video"
            else:
                gemini_input = self.gemini_client.upload_to_gemini(compressed_video_path)
                self.logger.info("Upload to Gemini completed successfully")
            
            self.emit_status(
                "Uploading to AI",
                55,
                "Video uploaded successfully to Gemini API"
            )
            
            # Step 2: Get analysis results
            self._current_step = PROCESSING_STEPS['AI_ANALYSIS']
            self.emit_status(
                "AI Analysis",
                60,
                STATUS_MESSAGES['AI_ANALYSIS']
            )
            
            if use_mock:
                # Generate fallback/mock response for testing
                from services import VideoMetadataService
                metadata_service = VideoMetadataService(self.temp_dir)
                video_duration = metadata_service.get_video_duration(compressed_video_path)
                
                gemini_response = self.gemini_client.create_fallback_response(
                    script, target_duration, video_duration
                )
                self.logger.warning("Using MOCK Gemini response")
            else:
                gemini_response = self.gemini_client.get_gemini_response_with_json(
                    gemini_input,
                    script,
                    target_duration,
                    voiceover_segments=voiceover_segments
                )
            
            self.logger.info(f"Gemini analysis completed: {len(gemini_response.script_segments)} segments")
            
            # Log segment details
            for i, seg in enumerate(gemini_response.script_segments, 1):
                self.logger.info(
                    f"  Segment {i}: {seg.start_timestamp} → {seg.end_timestamp} "
                    f"({seg.duration_seconds:.1f}s, confidence: {seg.confidence:.0%})"
                )
            
            self.emit_status(
                "AI Analysis",
                75,
                f"Analysis complete: {len(gemini_response.script_segments)} segments identified"
            )
            
            return gemini_response
            
        except GeminiAPIError as e:
            self.logger.error(f"Gemini API error: {e}")
            raise GeminiAPIError(f"Failed to analyze video with Gemini: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during Gemini analysis: {e}")
            raise GeminiProcessingError(f"Video analysis failed: {e}")
    
    def validate_analysis_results(
        self,
        gemini_response: GeminiResponse,
        target_duration: float,
        voiceover_segments: Optional[List[Dict]] = None
    ) -> bool:
        """
        Validate Gemini analysis results for quality and consistency.
        
        Args:
            gemini_response: Analysis results to validate
            target_duration: Expected target duration
            voiceover_segments: Optional voiceover segments for validation
            
        Returns:
            True if validation passes
        """
        self._current_step = PROCESSING_STEPS['VALIDATING_DURATION']
        self.emit_status(
            "Validating duration",
            78,
            STATUS_MESSAGES['VALIDATING_DURATION']
        )
        
        try:
            total_duration = gemini_response.total_duration
            difference = abs(total_duration - target_duration)
            
            # Validate segment count matches voiceover if provided
            if voiceover_segments:
                expected_segments = len(voiceover_segments)
                actual_segments = len(gemini_response.script_segments)
                
                if expected_segments != actual_segments:
                    self.logger.warning(
                        f"Segment count mismatch: expected {expected_segments}, "
                        f"got {actual_segments} (voiceover mode)"
                    )
            
            # Validate total duration
            if difference > 15.0:
                self.logger.warning(
                    f"Duration outside tolerance: {total_duration:.1f}s "
                    f"(target: {target_duration}s, diff: {difference:.1f}s)"
                )
                # Could implement duration adjustment logic here
            else:
                self.logger.info(f"Duration validated: {total_duration:.1f}s (within ±15s tolerance)")
            
            # Validate confidence scores
            low_confidence_segments = [
                seg for seg in gemini_response.script_segments 
                if seg.confidence < 0.5
            ]
            
            if low_confidence_segments:
                self.logger.warning(
                    f"Found {len(low_confidence_segments)} segments with low confidence (<0.5)"
                )
            
            self.emit_status(
                "Validating duration",
                80,
                f"Duration validated: {total_duration:.1f}s"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False
    
    def execute(self, *args, **kwargs):
        """Execute workflow - implemented by specific workflow methods."""
        raise NotImplementedError("Use specific workflow methods like analyze_video_segments")