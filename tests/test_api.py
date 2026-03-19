#!/usr/bin/env python3
"""
Unit tests for Economy Research API
"""

import unittest
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api_server import app

class TestEconomyAPI(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
    
    def test_generate_cache_valid(self):
        """Test cache generation with valid input"""
        payload = {
            'gameName': 'Test Game',
            'depth': 2
        }
        response = self.client.post('/api/research/cache',
                                   json=payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('cache', data)
        self.assertIn('session_id', data)
        
        # Check cache structure
        cache = data['cache']
        self.assertEqual(cache['game'], 'Test Game')
        self.assertEqual(cache['depth'], 2)
        self.assertEqual(cache['prompt_version'], '2.0')
        self.assertIn('categories', cache)
        self.assertEqual(len(cache['categories']), 6)  # depth 2 should have 6 categories
        self.assertIn('research_brief', cache)
        self.assertIn('conversion_prompt', cache)
        self.assertIn('json_schema', cache)
    
    def test_generate_cache_depth_levels(self):
        """Test cache generation at different depth levels"""
        for depth in [1, 2, 3]:
            payload = {
                'gameName': f'Depth {depth} Game',
                'depth': depth
            }
            response = self.client.post('/api/research/cache',
                                      json=payload,
                                      content_type='application/json')
            data = json.loads(response.data)
            cache = data['cache']
            
            # Verify category count increases with depth
            if depth == 1:
                self.assertEqual(len(cache['categories']), 3)
            elif depth == 2:
                self.assertEqual(len(cache['categories']), 6)
            elif depth == 3:
                self.assertEqual(len(cache['categories']), 9)
    
    def test_generate_cache_missing_game_name(self):
        """Test cache generation with missing game name"""
        payload = {'depth': 2}
        response = self.client.post('/api/research/cache',
                                   json=payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_validate_json_valid(self):
        """Test JSON validation with valid structure"""
        valid_json = {
            'inputs': [
                {'id': 'time', 'label': 'Time', 'kind': 'initial_sink_node'}
            ],
            'nodes': [
                {
                    'id': 'test_node',
                    'label': 'Test Node',
                    'sources': [],
                    'sinks': [],
                    'values': []
                }
            ],
            'edges': [
                ['time', 'test_node']
            ]
        }
        
        payload = {'json': valid_json}
        response = self.client.post('/api/research/validate',
                                   json=payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['valid'])
    
    def test_validate_json_invalid(self):
        """Test JSON validation with invalid structure"""
        invalid_json = {
            'inputs': [],
            'nodes': [],
            'edges': [['nonexistent', 'also_nonexistent']]
        }
        
        payload = {'json': invalid_json}
        response = self.client.post('/api/research/validate',
                                   json=payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['valid'])
    
    def test_validate_json_string_format(self):
        """Test JSON validation with string input"""
        json_string = '{"inputs":[],"nodes":[],"edges":[]}'
        payload = {'json': json_string}
        response = self.client.post('/api/research/validate',
                                   json=payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('valid', data)
    
    def test_session_retrieval(self):
        """Test session storage and retrieval"""
        # First create a session
        payload = {
            'gameName': 'Session Test',
            'depth': 1
        }
        create_response = self.client.post('/api/research/cache',
                                         json=payload,
                                         content_type='application/json')
        create_data = json.loads(create_response.data)
        session_id = create_data['session_id']
        
        # Now retrieve the session
        get_response = self.client.get(f'/api/research/session/{session_id}')
        self.assertEqual(get_response.status_code, 200)
        session_data = json.loads(get_response.data)
        self.assertEqual(session_data['game'], 'Session Test')
        self.assertEqual(session_data['depth'], 1)
        self.assertIn('cache', session_data)
    
    def test_session_not_found(self):
        """Test retrieval of non-existent session"""
        response = self.client.get('/api/research/session/nonexistent_session')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_list_templates(self):
        """Test template listing"""
        response = self.client.get('/api/templates')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('templates', data)
        self.assertIsInstance(data['templates'], list)
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.client.get('/health')
        self.assertIn('Access-Control-Allow-Origin', response.headers)
    
    def test_generate_economy_missing_params(self):
        """Test economy generation with missing parameters"""
        payload = {'depth': 2}  # Missing gameName
        response = self.client.post('/api/research/generate',
                                   json=payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('api_server.EconomyJSONBuilder')
    def test_generate_economy_forwards_structured_request_fields(self, mock_builder_cls):
        """Structured prompt/schema fields from the plugin should reach the provider."""
        mock_provider = Mock()
        mock_provider.generate_economy_json.return_value = {
            'inputs': [{'id': 'time', 'label': 'Time', 'kind': 'initial_sink_node'}],
            'nodes': [{'id': 'to_play', 'label': 'To Play', 'sources': [], 'sinks': ['Time'], 'values': []}],
            'edges': [['time', 'to_play']]
        }

        mock_builder = Mock()
        mock_builder.provider = mock_provider
        mock_builder.normalize_json.side_effect = lambda data: data
        mock_builder.stylize_labels.side_effect = lambda data: data
        mock_builder.stylize_resources.side_effect = lambda data: data
        mock_builder.enforce_final_goods_policy.side_effect = lambda data: data
        mock_builder.validate_json.return_value = True
        mock_builder_cls.return_value = mock_builder

        payload = {
            'gameName': 'Test Game',
            'depth': 2,
            'provider': 'gemini',
            'apiKey': 'AIza_valid_enough_for_test_payload_only',
            'promptVersion': '2.0',
            'researchBrief': 'Research brief text',
            'conversionPrompt': 'Return a single JSON object only.',
            'responseMimeType': 'application/json',
            'responseJsonSchema': {
                'type': 'object',
                'required': ['inputs', 'nodes', 'edges']
            }
        }

        response = self.client.post('/api/research/generate',
                                    json=payload,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        _, kwargs = mock_provider.generate_economy_json.call_args
        self.assertEqual(kwargs['research_brief'], 'Research brief text')
        self.assertEqual(kwargs['conversion_prompt'], 'Return a single JSON object only.')
        self.assertEqual(kwargs['response_mime_type'], 'application/json')
        self.assertEqual(kwargs['prompt_version'], '2.0')
        self.assertEqual(kwargs['response_json_schema'], payload['responseJsonSchema'])

    def test_validate_key_rejects_placeholder_values(self):
        """Placeholder values should fail fast with a clear error."""
        response = self.client.post('/api/research/validate-key',
                                    json={'apiKey': 'your_google_api_key_here'},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['valid'])
        self.assertIn('placeholder', data['error'])


class TestEconomyAPIIntegration(unittest.TestCase):
    """Integration tests that require external dependencies"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_generate_economy_without_api_key(self):
        """Test economy generation without API key (should fail gracefully)"""
        payload = {
            'gameName': 'Test Game',
            'depth': 1,
            'provider': 'gemini'
        }
        response = self.client.post('/api/research/generate',
                                   json=payload,
                                   content_type='application/json')
        # Should return 400 if no API key in environment
        if response.status_code == 400:
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertIn('API key', data['error'])
        else:
            # If API key is in environment, should work
            self.assertEqual(response.status_code, 200)
    
    def test_template_retrieval(self):
        """Test getting a specific template if it exists"""
        # First check if templates exist
        list_response = self.client.get('/api/templates')
        list_data = json.loads(list_response.data)
        
        if list_data['templates']:
            # Get first template
            template_name = list_data['templates'][0]['name']
            response = self.client.get(f'/api/templates/{template_name}')
            
            if response.status_code == 200:
                data = json.loads(response.data)
                self.assertIn('json', data)
                self.assertIn('name', data)
                self.assertEqual(data['name'], template_name)
            else:
                # Template file might not exist
                self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
