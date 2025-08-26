#!/usr/bin/env python3
"""
REST API Server for Economy JSON Builder
Provides HTTP endpoints for the Figma plugin to generate economy JSONs
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

# Import the economy builder
from economy_json_builder import EconomyJSONBuilder
from providers import get_provider
from providers.secure_config import SecureConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['*'])  # Allow all origins for development

# Store for ongoing research sessions (in production, use Redis/database)
research_sessions = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/research/cache', methods=['POST'])
def generate_cache():
    """Generate a research cache for a game"""
    try:
        data = request.json
        game_name = data.get('gameName', '')
        depth = data.get('depth', 2)
        
        if not game_name:
            return jsonify({'error': 'Game name is required'}), 400
        
        # Generate cache structure
        cache = {
            'game': game_name,
            'depth': depth,
            'timestamp': datetime.now().isoformat(),
            'prompt_version': '1.0',
            'instructions': f'Research the economy of {game_name} at depth level {depth}',
            'session_id': f"{game_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Add depth-specific details
        if depth >= 1:
            cache['categories'] = [
                'Core Gameplay Loop',
                'Resource Management', 
                'Progression Systems'
            ]
        
        if depth >= 2:
            cache['categories'].extend([
                'Monetization',
                'Time-Limited Events',
                'Social Features'
            ])
        
        if depth >= 3:
            cache['categories'].extend([
                'Competitive Elements',
                'Collection/Completion',
                'End-game Content'
            ])
        
        # Store session info
        research_sessions[cache['session_id']] = {
            'game': game_name,
            'depth': depth,
            'created': datetime.now().isoformat(),
            'cache': cache
        }
        
        logger.info(f"Generated cache for {game_name} at depth {depth}")
        
        return jsonify({
            'success': True,
            'cache': cache,
            'session_id': cache['session_id']
        })
        
    except Exception as e:
        logger.error(f"Error generating cache: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/generate', methods=['POST'])
def generate_economy():
    """Generate full economy JSON using LLM provider"""
    try:
        data = request.json
        game_name = data.get('gameName', '')
        depth = data.get('depth', 2)
        provider_name = data.get('provider', 'gemini')
        api_key = data.get('apiKey')
        session_id = data.get('sessionId')
        
        if not game_name:
            return jsonify({'error': 'Game name is required'}), 400
        
        if not api_key:
            # Try to get from environment or secure config
            config = SecureConfig()
            api_key = config.get_api_key(provider_name)
            if not api_key:
                return jsonify({'error': 'API key is required'}), 400
        
        logger.info(f"Generating economy for {game_name} using {provider_name}")
        
        # Create markdown input
        markdown_content = f"""# {game_name} Economy Research

## Overview
Game: {game_name}
Research Depth: Level {depth}
Generated: {datetime.now().isoformat()}

## Research Focus
Please research and model the complete economy for {game_name}.

### Core Elements to Include:
- Primary currencies and resources
- Core gameplay loops and activities
- Progression systems (XP, levels, ranks)
- Resource conversion mechanics
- Time gates and energy systems
- Monetization elements
- Social and competitive features
- End-game content and goals

### Depth Requirements:
"""
        
        if depth >= 1:
            markdown_content += """
Level 1 - Basic Economy:
- Identify main currencies (premium, soft, event)
- Map core gameplay loop
- Basic progression (levels, XP)
- Primary resource flows
"""
        
        if depth >= 2:
            markdown_content += """
Level 2 - Detailed Analysis:
- All currency types and exchange rates
- Secondary activities (crafting, trading)
- Time-gated content
- Battle passes and subscriptions
- Social features impact on economy
"""
        
        if depth >= 3:
            markdown_content += """
Level 3 - Comprehensive Model:
- Player segmentation strategies (F2P, dolphins, whales)
- Optimization paths for different playstyles
- Detailed monetization mechanics
- End-game economy loops
- Competitive economy elements
- Collection and completion mechanics
"""
        
        # Initialize builder with proper kwargs
        provider_kwargs = {}
        if provider_name == 'gemini':
            if data.get('model'):
                provider_kwargs['model_name'] = data.get('model', 'gemini-1.5-flash-002')
            provider_kwargs['depth'] = depth
        
        builder = EconomyJSONBuilder(
            provider_name=provider_name,
            api_key=api_key,
            repo_path=None,
            **provider_kwargs
        )
        
        # Generate economy JSON using the provider
        logger.info(f"Generating economy JSON with {provider_name} provider")
        economy_json = builder.provider.generate_economy_json(
            markdown_content, 
            game_name
        )
        
        # Normalize and validate
        economy_json = builder.normalize_json(economy_json)
        economy_json = builder.stylize_labels(economy_json)
        economy_json = builder.stylize_resources(economy_json)
        economy_json = builder.enforce_final_goods_policy(economy_json)
        
        # Validate the result
        if not builder.validate_json(economy_json):
            logger.warning("Generated JSON failed validation but returning anyway")
        
        # Store result in session
        if session_id and session_id in research_sessions:
            research_sessions[session_id]['economy_json'] = economy_json
            research_sessions[session_id]['completed'] = datetime.now().isoformat()
        
        logger.info(f"Successfully generated economy JSON for {game_name}")
        
        return jsonify({
            'success': True,
            'json': economy_json,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error generating economy: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get research session details"""
    if session_id not in research_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify(research_sessions[session_id])

@app.route('/api/research/validate-key', methods=['POST'])
def validate_api_key():
    """Validate a Gemini API key"""
    try:
        data = request.json
        api_key = data.get('apiKey', '')
        
        if not api_key:
            return jsonify({'valid': False, 'error': 'No API key provided'}), 400
        
        # Basic format check
        if not api_key.startswith('AIza') or len(api_key) < 39:
            return jsonify({
                'valid': False,
                'error': 'Invalid API key format'
            })
        
        # Try to initialize the provider to test the key
        try:
            from providers import get_provider
            provider = get_provider('gemini', api_key)
            # If initialization succeeds, key is likely valid
            return jsonify({
                'valid': True,
                'message': 'API key is valid'
            })
        except Exception as e:
            return jsonify({
                'valid': False,
                'error': str(e)
            })
            
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/validate', methods=['POST'])
def validate_json():
    """Validate an economy JSON structure"""
    try:
        data = request.json
        economy_json = data.get('json', {})
        
        if isinstance(economy_json, str):
            economy_json = json.loads(economy_json)
        
        # Use the builder's validation
        builder = EconomyJSONBuilder(
            provider_name='gemini',
            api_key='dummy',
            repo_path=None,
            initialize_provider=False
        )
        
        is_valid = builder.validate_json(economy_json)
        
        return jsonify({
            'valid': is_valid,
            'message': 'JSON is valid' if is_valid else 'JSON validation failed'
        })
        
    except json.JSONDecodeError as e:
        return jsonify({
            'valid': False,
            'message': f'Invalid JSON format: {str(e)}'
        })
    except Exception as e:
        logger.error(f"Error validating JSON: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List available example templates"""
    try:
        examples_dir = Path(__file__).parent.parent / 'economy_flow_plugin' / 'examples'
        templates = []
        
        if examples_dir.exists():
            for file in examples_dir.glob('*.json'):
                templates.append({
                    'name': file.stem,
                    'filename': file.name
                })
        
        return jsonify({
            'templates': templates
        })
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/<template_name>', methods=['GET'])
def get_template(template_name):
    """Get a specific template"""
    try:
        examples_dir = Path(__file__).parent.parent / 'economy_flow_plugin' / 'examples'
        template_file = examples_dir / f"{template_name}.json"
        
        if not template_file.exists():
            return jsonify({'error': 'Template not found'}), 404
        
        with open(template_file, 'r') as f:
            template_data = json.load(f)
        
        return jsonify({
            'name': template_name,
            'json': template_data
        })
        
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Development server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Economy Research API on port {port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )