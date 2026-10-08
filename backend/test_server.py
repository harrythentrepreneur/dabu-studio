#!/usr/bin/env python3
"""
Local test server for the backend processing pipeline
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Import the main pipeline
from main import MainPipeline

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the pipeline
pipeline = MainPipeline()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'environment': os.getenv('ENVIRONMENT_MODE', 'LOCAL'),
        'services': {
            'gemini': bool(os.getenv('GEMINI_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'do_spaces': bool(os.getenv('DO_SPACES_KEY')),
        }
    })

@app.route('/process', methods=['POST'])
def process_video():
    """Process video with script matching"""
    try:
        data = request.json
        script = data.get('script', '')
        target_duration = data.get('duration', 35.0)
        
        # For testing, we'll use the example videos in input_videos
        input_dir = Path(__file__).parent.parent / 'input_videos'
        
        # Check if we have test videos
        video_files = list(input_dir.glob('*.mp4'))
        if not video_files:
            return jsonify({
                'error': 'No test videos found in input_videos directory',
                'hint': 'Please add some .mp4 files to the input_videos directory'
            }), 400
        
        logger.info(f"Processing with {len(video_files)} video files")
        
        # Run the pipeline
        result = pipeline.process(
            script=script,
            video_files=video_files[:3],  # Use first 3 videos for testing
            target_duration=target_duration,
            use_mock=False  # Set to True to skip Gemini API calls
        )
        
        if result.success:
            return jsonify({
                'success': True,
                'output_video': str(result.output_video_path),
                'script_file': str(result.script_file_path),
                'timestamps_file': str(result.timestamps_file_path),
                'processing_time': result.processing_time,
                'segments': len(result.gemini_response.script_segments) if result.gemini_response else 0
            })
        else:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 500
            
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/mock-process', methods=['POST'])
def mock_process():
    """Test endpoint with mock Gemini response"""
    try:
        data = request.json
        script = data.get('script', 'Test script for mock processing')
        
        # Run with mock mode
        result = pipeline.process(
            script=script,
            target_duration=35.0,
            use_mock=True  # Use mock Gemini response
        )
        
        if result.success:
            return jsonify({
                'success': True,
                'message': 'Mock processing completed',
                'output_video': str(result.output_video_path) if result.output_video_path else None,
                'processing_time': result.processing_time
            })
        else:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 500
            
    except Exception as e:
        logger.error(f"Mock processing error: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'environment': os.getenv('ENVIRONMENT_MODE', 'LOCAL'),
        'use_runpod': os.getenv('USE_RUNPOD', 'false') == 'true',
        'gemini_configured': bool(os.getenv('GEMINI_API_KEY')),
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'do_spaces_configured': bool(os.getenv('DO_SPACES_KEY')),
        'input_videos_path': str(Path(__file__).parent.parent / 'input_videos'),
        'output_path': str(Path(__file__).parent / 'output'),
        'temp_path': str(Path(__file__).parent / 'temp')
    })

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting test server on port {port}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT_MODE', 'LOCAL')}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )