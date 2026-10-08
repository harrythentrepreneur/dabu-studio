"""
Simple Environment Configuration System
Handles LOCAL, HYBRID, and PRODUCTION modes
"""

import os
from typing import Dict, Any
from pathlib import Path

class EnvironmentConfig:
    """Environment configuration based on ENVIRONMENT_MODE"""
    
    def __init__(self):
        self.mode = os.getenv('ENVIRONMENT_MODE', 'LOCAL').upper()
        self._validate_mode()
        
    def _validate_mode(self):
        """Validate environment mode"""
        valid_modes = ['LOCAL', 'HYBRID', 'PRODUCTION']
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid ENVIRONMENT_MODE: {self.mode}. Must be one of {valid_modes}")
    
    def is_local(self) -> bool:
        """Check if running in LOCAL mode"""
        return self.mode == 'LOCAL'
    
    def is_hybrid(self) -> bool:
        """Check if running in HYBRID mode"""
        return self.mode == 'HYBRID'
    
    def is_production(self) -> bool:
        """Check if running in PRODUCTION mode"""
        return self.mode == 'PRODUCTION'
    
    def use_runpod(self) -> bool:
        """Check if RunPod should be used"""
        return self.mode in ['HYBRID', 'PRODUCTION']
    
    def use_digital_ocean(self) -> bool:
        """Check if Digital Ocean Spaces should be used"""
        # Use DO Spaces in all modes when USE_LOCAL_DOCKER is true
        if self.mode == 'LOCAL' and os.getenv('USE_LOCAL_DOCKER', 'false').lower() == 'true':
            return True
        return self.mode in ['HYBRID', 'PRODUCTION']
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration based on mode"""
        if self.is_local():
            return {
                'type': 'local',
                'upload_path': Path('/tmp/tiktok-automation/uploads'),
                'output_path': Path('/tmp/tiktok-automation/outputs'),
                'temp_path': Path('/tmp/tiktok-automation/temp')
            }
        else:
            return {
                'type': 'cloud',
                'bucket': os.getenv('DO_SPACES_BUCKET', ''),
                'region': os.getenv('DO_SPACES_REGION', 'sfo3'),
                'endpoint': os.getenv('DO_SPACES_ENDPOINT'),
                'upload_prefix': 'uploads',
                'output_prefix': 'outputs',
                'temp_prefix': 'temp'
            }
    
    def get_processing_service(self, service_name: str) -> str:
        """Get the processing service location based on mode and service"""
        service_map = {
            'express_builder': 'runpod' if self.use_runpod() else 'local',
            'quick_create': 'runpod' if self.use_runpod() else 'local',
            'gif_studio': 'local',  # Always local
            'music_library': 'local'  # Always local
        }
        return service_map.get(service_name, 'local')
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate required configuration for current mode"""
        validation = {
            'mode_valid': True,
            'gemini_configured': bool(os.getenv('GEMINI_API_KEY')),
        }
        
        if self.use_runpod():
            validation['runpod_configured'] = bool(
                os.getenv('RUNPOD_API_KEY') and 
                os.getenv('RUNPOD_ENDPOINT_ID')
            )
        
        if self.use_digital_ocean():
            validation['do_configured'] = bool(
                os.getenv('DO_SPACES_KEY') and 
                os.getenv('DO_SPACES_SECRET') and
                os.getenv('DO_SPACES_BUCKET')
            )
        
        validation['all_valid'] = all(validation.values())
        return validation
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'mode': self.mode,
            'use_runpod': self.use_runpod(),
            'use_digital_ocean': self.use_digital_ocean(),
            'storage': self.get_storage_config(),
            'services': {
                'express_builder': self.get_processing_service('express_builder'),
                'quick_create': self.get_processing_service('quick_create'),
                'gif_studio': self.get_processing_service('gif_studio'),
                'music_library': self.get_processing_service('music_library')
            },
            'validation': self.validate_config()
        }

# Global instance
env_config = EnvironmentConfig()