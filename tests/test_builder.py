#!/usr/bin/env python3
"""
Unit tests for Economy JSON Builder normalization and validation.
These tests avoid network/SDK imports by not initializing providers.
"""

import unittest

from economy_json_builder import EconomyJSONBuilder


def make_builder():
    # initialize_provider=False avoids importing model SDKs
    return EconomyJSONBuilder(provider_name='gemini', api_key='', repo_path='', initialize_provider=False)


class TestBuilder(unittest.TestCase):
    def test_label_and_resource_styling(self):
        b = make_builder()
        data = {
            "inputs": [
                {"id": "time", "label": "Time", "kind": "initial_sink_node"},
            ],
            "nodes": [
                {
                    "id": "gather",
                    "label": "gathering",
                    "sources": ["raw_materials", "xp"],
                    "sinks": ["time"],
                    "values": []
                },
            ],
            "edges": [["time", "gather"]],
        }
        data = b.stylize_labels(data)
        data = b.stylize_resources(data)
        data = b.reclassify_value_terms(data)

        node = data['nodes'][0]
        self.assertTrue(node['label'].startswith('To '))
        self.assertIn('Raw Materials', node['sources'])
        # XP should be a value, not a source
        self.assertIn('XP', node['values'])
        self.assertNotIn('XP', node['sources'])

    def test_prune_unknown_edges_and_collapse(self):
        b = make_builder()
        data = {
            "inputs": [
                {"id": "time", "label": "Time", "kind": "initial_sink_node"},
            ],
            "nodes": [
                {"id": "gather", "label": "To Gather", "sources": [], "sinks": ["Time"], "values": []},
                {"id": "materials", "label": "Materials", "sources": [], "sinks": [], "values": []},
            ],
            "edges": [["time", "gather"], ["gather", "materials"], ["materials", "missing_node"]],
        }
        data = b.collapse_resource_nodes(data)
        data = b.prune_unknown_edges(data)
        # Resource node removed; edge to missing id removed
        ids = {n['id'] for n in data['nodes']}
        self.assertNotIn('materials', ids)
        for e in data['edges']:
            self.assertTrue(all(x in ids or x == 'time' for x in e))

    def test_validate_schema(self):
        b = make_builder()
        valid = {
            "inputs": [{"id": "time", "label": "Time", "kind": "initial_sink_node"}],
            "nodes": [{"id": "play", "label": "To Play", "sources": ["Gold"], "sinks": ["Time"], "values": []}],
            "edges": [["time", "play"]],
        }
        self.assertTrue(b.validate_json(valid))


if __name__ == '__main__':
    unittest.main()
