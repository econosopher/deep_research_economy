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
from providers.prompts import economy_json_response_schema, final_json_instructions_prompt

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
PROMPT_VERSION = '2.0'


def build_research_brief(game_name: str, depth: int) -> str:
    """Build a research brief aligned with the plugin's structured generation contract."""
    lines = [
        f'Research the game economy for "{game_name}".',
        'Focus on concrete, player-facing systems and only include mechanics with strong evidence.',
        'Capture spendable resources, consumed resources, non-spendable progression values, core activities, and final player outcomes.',
    ]

    if depth >= 1:
        lines.append('Depth 1: map the core loop, main currencies/resources, and the primary progression path.')
    if depth >= 2:
        lines.append('Depth 2: add monetization, time gates, event systems, social/competitive loops, and important side systems.')
    if depth >= 3:
        lines.append('Depth 3: add end-game loops, optimization paths, collection/completion systems, and distinct playstyle differences.')

    return '\n'.join(lines)


def build_conversion_prompt(game_name: str) -> str:
    """Build the JSON conversion prompt used when the client does not supply one."""
    return final_json_instructions_prompt(game_name)


def build_markdown_content(
    game_name: str,
    depth: int,
    research_brief: Optional[str] = None,
    conversion_prompt: Optional[str] = None,
    response_json_schema: Optional[Dict[str, Any]] = None,
) -> str:
    """Create the markdown payload used by legacy provider flows."""
    schema = response_json_schema or economy_json_response_schema()
    return (
        f"# {game_name} Economy Research\n\n"
        f"## Research Brief\n{research_brief or build_research_brief(game_name, depth)}\n\n"
        f"## Structured Conversion Prompt\n{conversion_prompt or build_conversion_prompt(game_name)}\n\n"
        f"## Output JSON Schema\n```json\n{json.dumps(schema, indent=2)}\n```"
    )


def build_cache_payload(
    game_name: str,
    depth: int,
    prompt_version: str = PROMPT_VERSION,
    research_brief: Optional[str] = None,
    conversion_prompt: Optional[str] = None,
    response_json_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the cache metadata returned to the plugin."""
    cache = {
        'game': game_name,
        'depth': depth,
        'timestamp': datetime.now().isoformat(),
        'prompt_version': prompt_version,
        'instructions': research_brief or build_research_brief(game_name, depth),
        'research_brief': research_brief or build_research_brief(game_name, depth),
        'conversion_prompt': conversion_prompt or build_conversion_prompt(game_name),
        'json_schema': response_json_schema or economy_json_response_schema(),
        'session_id': f"{game_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

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

    return cache


def is_placeholder_api_key(api_key: Optional[str]) -> bool:
    if not api_key:
        return True
    normalized = api_key.strip().lower()
    return (
        not normalized or
        normalized.startswith('your_') or
        'placeholder' in normalized
    )


def is_api_key_error(message: str) -> bool:
    """Best-effort detection for credential failures returned by providers."""
    normalized = message.lower()
    return (
        'api key' in normalized or
        'permissiondenied' in normalized or
        'reported as leaked' in normalized
    )

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
        cache = build_cache_payload(
            game_name,
            depth,
            prompt_version=data.get('promptVersion', PROMPT_VERSION),
            research_brief=data.get('researchBrief'),
            conversion_prompt=data.get('conversionPrompt'),
            response_json_schema=data.get('responseJsonSchema')
        )
        
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
        prompt_version = data.get('promptVersion', PROMPT_VERSION)
        research_brief = data.get('researchBrief') or build_research_brief(game_name, depth)
        conversion_prompt = data.get('conversionPrompt') or build_conversion_prompt(game_name)
        response_json_schema = data.get('responseJsonSchema') or economy_json_response_schema()
        response_mime_type = data.get('responseMimeType', 'application/json')
        
        if not game_name:
            return jsonify({'error': 'Game name is required'}), 400
        
        if not api_key:
            # Try to get from environment or secure config
            config = SecureConfig()
            api_key = config.get_api_key(provider_name)
            if not api_key:
                return jsonify({'error': 'API key is required'}), 400
        elif is_placeholder_api_key(api_key):
            return jsonify({'error': 'API key is required'}), 400
        
        logger.info(f"Generating economy for {game_name} using {provider_name}")
        markdown_content = build_markdown_content(
            game_name,
            depth,
            research_brief=research_brief,
            conversion_prompt=conversion_prompt,
            response_json_schema=response_json_schema
        )
        
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
            game_name,
            research_brief=research_brief,
            conversion_prompt=conversion_prompt,
            response_json_schema=response_json_schema,
            response_mime_type=response_mime_type,
            prompt_version=prompt_version,
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
        error_message = str(e)
        logger.error(f"Error generating economy: {error_message}\n{traceback.format_exc()}")
        status_code = 400 if is_api_key_error(error_message) else 500
        return jsonify({'error': error_message}), status_code

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
        if is_placeholder_api_key(api_key):
            return jsonify({
                'valid': False,
                'error': 'API key is a placeholder value'
            })
        
        # Try to initialize the provider to test the key
        try:
            from providers import get_provider
            provider = get_provider('gemini', api_key)
            is_valid = provider.validate_api_key() if hasattr(provider, 'validate_api_key') else True
            return jsonify({
                'valid': is_valid,
                'http_ok': True,
                'message': 'API key is valid' if is_valid else None,
                'error': None if is_valid else 'Gemini rejected the supplied API key'
            })
        except Exception as e:
            return jsonify({
                'valid': False,
                'http_ok': True,
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
