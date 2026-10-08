"""
Processing Steps Manager
Centralized processing step definitions and progress calculation
"""

class ProcessingSteps:
    """Manages processing steps and progress for Express Builder pipeline"""
    
    # Step definitions for different scenarios
    STEPS_NO_VOICEOVER = {
        1: {"name": "Preparing files", "progress_range": (0, 15)},
        2: {"name": "Uploading to cloud", "progress_range": (15, 25)},
        3: {"name": "Merging videos", "progress_range": (25, 35)},
        4: {"name": "Analyzing with AI", "progress_range": (35, 60)},
        5: {"name": "Matching script to video", "progress_range": (60, 75)},
        6: {"name": "Extracting segments", "progress_range": (75, 85)},
        7: {"name": "Creating final video", "progress_range": (85, 95)},
        8: {"name": "Finalizing", "progress_range": (95, 100)},
    }
    
    STEPS_WITH_VOICEOVER = {
        1: {"name": "Analyzing voiceover", "progress_range": (0, 10)},
        2: {"name": "Preparing files", "progress_range": (10, 20)},
        3: {"name": "Uploading to cloud", "progress_range": (20, 28)},
        4: {"name": "Merging videos", "progress_range": (28, 35)},
        5: {"name": "Analyzing with AI", "progress_range": (35, 55)},
        6: {"name": "Matching script to video", "progress_range": (55, 68)},
        7: {"name": "Extracting segments", "progress_range": (68, 78)},
        8: {"name": "Creating final video", "progress_range": (78, 88)},
        9: {"name": "Adding voiceover", "progress_range": (88, 95)},
        10: {"name": "Finalizing", "progress_range": (95, 100)},
    }
    
    # Docker-specific sub-steps
    DOCKER_SUB_STEPS = {
        "uploading": {"message": "Uploading files to cloud storage...", "progress_offset": 0},
        "docker_starting": {"message": "Initializing processing container...", "progress_offset": 2},
        "docker_processing": {"message": "Processing with Docker container...", "progress_offset": 5},
        "downloading_results": {"message": "Retrieving processed files...", "progress_offset": 8},
        "finalizing": {"message": "Finalizing output files...", "progress_offset": 10},
    }
    
    @staticmethod
    def get_step_info(step_number: int, has_voiceover: bool = False):
        """Get step information including name and progress range"""
        steps = ProcessingSteps.STEPS_WITH_VOICEOVER if has_voiceover else ProcessingSteps.STEPS_NO_VOICEOVER
        return steps.get(step_number, {"name": "Processing", "progress_range": (0, 100)})
    
    @staticmethod
    def calculate_progress(step_number: int, sub_progress: float = 0.0, has_voiceover: bool = False):
        """
        Calculate overall progress based on step and sub-progress
        
        Args:
            step_number: Current step number
            sub_progress: Progress within current step (0-100)
            has_voiceover: Whether voiceover is being processed
            
        Returns:
            Overall progress percentage (0-100)
        """
        step_info = ProcessingSteps.get_step_info(step_number, has_voiceover)
        min_progress, max_progress = step_info["progress_range"]
        
        # Calculate progress within the step's range
        step_range = max_progress - min_progress
        progress = min_progress + (step_range * sub_progress / 100.0)
        
        return min(100, max(0, int(progress)))
    
    @staticmethod
    def get_docker_message(sub_step: str):
        """Get message for Docker sub-steps"""
        return ProcessingSteps.DOCKER_SUB_STEPS.get(
            sub_step, 
            {"message": "Processing...", "progress_offset": 0}
        )
    
    @staticmethod
    def format_message(step_name: str, details: str = None):
        """Format a status message with optional details"""
        if details:
            return f"{step_name}: {details}"
        return step_name