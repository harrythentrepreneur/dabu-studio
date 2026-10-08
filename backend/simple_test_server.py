#!/usr/bin/env python3
"""
Simple test server for backend - testing basic functionality
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Backend test server is running',
        'environment': os.getenv('ENVIRONMENT_MODE', 'LOCAL'),
        'services': {
            'gemini': bool(os.getenv('GEMINI_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'do_spaces': bool(os.getenv('DO_SPACES_KEY')),
        }
    })

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'environment': os.getenv('ENVIRONMENT_MODE', 'LOCAL'),
        'use_runpod': os.getenv('USE_RUNPOD', 'false') == 'true',
        'flask_port': os.getenv('FLASK_PORT', '8000'),
        'apis_configured': {
            'gemini': bool(os.getenv('GEMINI_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'do_spaces': bool(os.getenv('DO_SPACES_KEY')),
        },
        'paths': {
            'backend_root': os.getcwd(),
            'input_videos': 'input_videos/',
            'output': 'output/',
            'temp': 'temp/'
        }
    })

@app.route('/test-gemini', methods=['POST'])
def test_gemini():
    """Test Gemini API connection"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({'error': 'GEMINI_API_KEY not configured'}), 400
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Simple test prompt
        response = model.generate_content("Say 'Hello from Gemini!' in 5 words or less")
        
        return jsonify({
            'success': True,
            'response': response.text,
            'model': 'gemini-2.0-flash-exp'
        })
    except Exception as e:
        logger.error(f"Gemini test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-openai', methods=['POST'])
def test_openai():
    """Test OpenAI API connection"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'OPENAI_API_KEY not configured'}), 400
        
        client = OpenAI(api_key=api_key)
        
        # Simple test
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello from OpenAI!' in 5 words or less"}
            ],
            max_tokens=20
        )
        
        return jsonify({
            'success': True,
            'response': response.choices[0].message.content,
            'model': 'gpt-3.5-turbo'
        })
    except Exception as e:
        logger.error(f"OpenAI test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-ffmpeg', methods=['GET'])
def test_ffmpeg():
    """Test FFmpeg installation"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return jsonify({
                'success': True,
                'ffmpeg_available': True,
                'version': version_line
            })
        else:
            return jsonify({
                'success': False,
                'ffmpeg_available': False,
                'error': 'FFmpeg not found'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'ffmpeg_available': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"""
    ========================================
    Backend Test Server Starting
    ========================================
    Port: {port}
    Environment: {os.getenv('ENVIRONMENT_MODE', 'LOCAL')}
    Debug: {debug}
    
    Available endpoints:
    - GET  /health        - Health check
    - GET  /config        - Show configuration
    - POST /test-gemini   - Test Gemini API
    - POST /test-openai   - Test OpenAI API
    - GET  /test-ffmpeg   - Test FFmpeg
    
    API Keys configured:
    - Gemini: {bool(os.getenv('GEMINI_API_KEY'))}
    - OpenAI: {bool(os.getenv('OPENAI_API_KEY'))}
    - DO Spaces: {bool(os.getenv('DO_SPACES_KEY'))}
    ========================================
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)