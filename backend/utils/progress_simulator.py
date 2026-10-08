"""
Progress Simulator for Docker/RunPod Processing
Provides smooth progress updates during long-running operations
"""

import threading
import time
from typing import Optional, Callable
from utils.logger import get_logger

logger = get_logger(__name__)

class ProgressSimulator:
    """Simulates smooth progress updates during Docker/RunPod processing"""
    
    def __init__(self, emitter, start_step: int = 3, end_step: int = 6, has_voiceover: bool = False):
        """
        Initialize progress simulator
        
        Args:
            emitter: Status emitter for sending updates
            start_step: Starting step number
            end_step: Ending step number
            has_voiceover: Whether processing includes voiceover
        """
        self.emitter = emitter
        self.start_step = start_step
        self.end_step = end_step
        self.has_voiceover = has_voiceover
        self.running = False
        self.thread = None
        self.current_progress = 0
        
        # Define sub-steps for Docker processing
        self.docker_substeps = [
            {"step": 3, "name": "Merging videos", "duration": 8, "messages": [
                "Preparing video files...",
                "Analyzing video formats...",
                "Merging video segments...",
                "Optimizing video quality..."
            ]},
            {"step": 4, "name": "Analyzing with AI", "duration": 20, "messages": [
                "Uploading to Gemini AI...",
                "AI analyzing video content...",
                "Identifying key moments...",
                "Matching visuals to script...",
                "Processing scene transitions...",
                "Analyzing motion and composition..."
            ]},
            {"step": 5, "name": "Matching script to video", "duration": 15, "messages": [
                "Aligning script segments...",
                "Finding optimal cut points...",
                "Analyzing scene continuity...",
                "Optimizing timing..."
            ]},
            {"step": 6, "name": "Extracting segments", "duration": 10, "messages": [
                "Extracting video segments...",
                "Processing transitions...",
                "Applying cuts...",
                "Finalizing segments..."
            ]}
        ]
    
    def start(self):
        """Start simulating progress"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._simulate_progress)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Started progress simulation")
    
    def stop(self):
        """Stop simulating progress"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("Stopped progress simulation")
    
    def _simulate_progress(self):
        """Simulate progress updates in background thread"""
        from utils.processing_steps import ProcessingSteps
        
        try:
            for substep in self.docker_substeps:
                if not self.running:
                    break
                
                step_num = substep["step"]
                if step_num < self.start_step or step_num > self.end_step:
                    continue
                
                step_name = substep["name"]
                messages = substep["messages"]
                duration = substep["duration"]
                
                # Calculate time per message
                time_per_message = duration / len(messages)
                
                for i, message in enumerate(messages):
                    if not self.running:
                        break
                    
                    # Calculate progress within this step
                    sub_progress = (i + 1) * 100 / len(messages)
                    overall_progress = ProcessingSteps.calculate_progress(
                        step_num, 
                        sub_progress, 
                        self.has_voiceover
                    )
                    
                    # Emit status update
                    if self.emitter and self.running:
                        self.emitter.emit_status(
                            step=step_num,
                            step_name=step_name,
                            progress=overall_progress,
                            message=message
                        )
                    
                    # Wait before next update
                    time.sleep(time_per_message)
            
        except Exception as e:
            logger.error(f"Error in progress simulation: {e}")
        finally:
            self.running = False
    
    def update_manual(self, step: int, message: str, sub_progress: float = 50):
        """
        Manually update progress (interrupts simulation)
        
        Args:
            step: Step number
            message: Status message
            sub_progress: Progress within step (0-100)
        """
        from utils.processing_steps import ProcessingSteps
        
        # Stop simulation if running
        if self.running:
            self.stop()
        
        # Send manual update
        if self.emitter:
            overall_progress = ProcessingSteps.calculate_progress(
                step, 
                sub_progress, 
                self.has_voiceover
            )
            
            self.emitter.emit_status(
                step=step,
                step_name=ProcessingSteps.get_step_info(step, self.has_voiceover)["name"],
                progress=overall_progress,
                message=message
            )