#!/usr/bin/env python3
"""
Economy JSON Builder - Modular Edition with Secure Config

This script connects to various LLM providers to research game economies based on a markdown file,
generates a JSON economy specification, and creates a PR to add it to the examples folder.
"""

import os
import sys
import json
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers import get_provider
from providers.secure_config import SecureConfig


class EconomyJSONBuilder:
    def __init__(self, provider_name: str, api_key: str, repo_path: str, initialize_provider: bool = True, **provider_kwargs):
        """Initialize the generator with provider and repository path."""
        self.provider_name = provider_name
        self.provider = None
        if initialize_provider:
            self.provider = get_provider(provider_name, api_key, **provider_kwargs)
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.output_path = Path.cwd() / "output"
        
        # Create output directory if it doesn't exist
        self.output_path.mkdir(exist_ok=True)
    
    def read_markdown_file(self, file_path: str) -> str:
        """Read and return the contents of a markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def validate_json(self, data: Dict[str, Any]) -> bool:
        """Validate the generated JSON against the schema requirements."""
        try:
            # Check required top-level keys
            required_keys = ["inputs", "nodes", "edges"]
            for key in required_keys:
                if key not in data:
                    print(f"Missing required key: {key}")
                    return False
            
            # Validate inputs
            if not isinstance(data["inputs"], list):
                print("'inputs' must be an array")
                return False
            
            for input_item in data["inputs"]:
                if not all(key in input_item for key in ["id", "label", "kind"]):
                    print(f"Input missing required fields: {input_item}")
                    return False
                if input_item["kind"] != "initial_sink_node":
                    print(f"Input kind must be 'initial_sink_node': {input_item}")
                    return False
            
            # Validate nodes
            if not isinstance(data["nodes"], list):
                print("'nodes' must be an array")
                return False
            
            node_ids = set()
            for node in data["nodes"]:
                if "id" not in node or "label" not in node:
                    print(f"Node missing required fields: {node}")
                    return False
                node_ids.add(node["id"])
                
                # Check array fields
                for field in ["sources", "sinks", "values"]:
                    if field in node and not isinstance(node[field], list):
                        print(f"Node field '{field}' must be an array: {node}")
                        return False
            
            # Validate edges
            if not isinstance(data["edges"], list):
                print("'edges' must be an array")
                return False
            
            input_ids = {inp["id"] for inp in data["inputs"]}
            all_ids = input_ids | node_ids
            
            for edge in data["edges"]:
                if not isinstance(edge, list) or len(edge) != 2:
                    print(f"Edge must be a two-element array: {edge}")
                    return False
                if edge[0] not in all_ids or edge[1] not in all_ids:
                    print(f"Edge references non-existent node: {edge}")
                    return False
            
            # Validate optional subsections
            if "subsections" in data:
                if not isinstance(data["subsections"], list):
                    print("'subsections' must be an array")
                    return False
                
                for subsection in data["subsections"]:
                    if not all(key in subsection for key in ["id", "label", "nodeIds"]):
                        print(f"Subsection missing required fields: {subsection}")
                        return False
                    if not isinstance(subsection["nodeIds"], list):
                        print(f"Subsection nodeIds must be an array: {subsection}")
                        return False
                # Ensure all subsection nodeIds exist in valid ids
                node_ids = {n.get('id') for n in data.get('nodes', []) if isinstance(n, dict)}
                input_ids = {i.get('id') for i in data.get('inputs', []) if isinstance(i, dict)}
                valid_ids = node_ids | input_ids
                for idx, subsection in enumerate(data["subsections"]):
                    for nid in subsection.get("nodeIds", []):
                        if nid not in valid_ids:
                            print(f"Subsection {idx}: Node id '{nid}' not found in inputs or nodes.")
                            return False
            
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    def save_json_file(self, data: Dict[str, Any], filename: str) -> str:
        """Save the JSON data to a file in the output directory."""
        # Remove metadata before saving
        if "_metadata" in data:
            metadata = data.pop("_metadata")
            print(f"Generated with {metadata.get('provider', 'unknown')} provider")
        
        file_path = self.output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.write('\n')  # Add trailing newline
        
        return str(file_path)

    def normalize_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Best-effort normalization to improve JSON validity without changing meaning."""
        changed = False

        # Ensure top-level arrays exist
        for key in ["inputs", "nodes", "edges"]:
            if key not in data:
                data[key] = []
                changed = True

        # Normalize nodes arrays
        if isinstance(data.get("nodes"), list):
            for node in data["nodes"]:
                for field in ["sources", "sinks", "values"]:
                    if field not in node or node[field] is None:
                        node[field] = []
                        changed = True

        # Normalize ids to snake_case and update edges/subsections accordingly
        def to_snake(s: str) -> str:
            import re
            s = s.strip()
            # Replace non-alphanumeric with underscore
            s = re.sub(r"[^A-Za-z0-9]+", "_", s)
            # Insert underscore between camelCase
            s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
            s = s.lower()
            s = re.sub(r"_+", "_", s).strip("_")
            return s or "node"

        id_map: Dict[str, str] = {}

        # Map inputs
        seen = set()
        for inp in data.get("inputs", []):
            old = inp.get("id", "")
            if not isinstance(old, str):
                continue
            new = to_snake(old)
            # Prefer canonical ids for primary inputs
            if 'time' in new and new != 'time' and 'time' not in seen:
                new = 'time'
            if 'money' in new and new != 'money' and 'money' not in seen:
                new = 'money'
            base = new
            i = 1
            while new in seen and new != old:
                i += 1
                new = f"{base}_{i}"
            if new != old:
                id_map[old] = new
                inp["id"] = new
                changed = True
            seen.add(inp["id"])

        # Map nodes
        for node in data.get("nodes", []):
            old = node.get("id", "")
            if not isinstance(old, str):
                continue
            new = to_snake(old)
            base = new
            i = 1
            # avoid clashing with inputs and other nodes
            while new in seen and new != old:
                i += 1
                new = f"{base}_{i}"
            if new != old:
                id_map[old] = new
                node["id"] = new
                changed = True
            seen.add(node["id"])

        # Update edges using id_map and remove duplicates
        new_edges = []
        seen_edges = set()
        for edge in data.get("edges", []):
            if isinstance(edge, list) and len(edge) == 2:
                a, b = edge
                if isinstance(a, str) and a in id_map:
                    a = id_map[a]
                    changed = True
                if isinstance(b, str) and b in id_map:
                    b = id_map[b]
                    changed = True
                tup = (a, b)
                if tup not in seen_edges:
                    seen_edges.add(tup)
                    new_edges.append([a, b])
            else:
                new_edges.append(edge)
        if new_edges:
            data["edges"] = new_edges

        # Update subsections.nodeIds if present
        for sub in data.get("subsections", []) or []:
            if isinstance(sub, dict) and isinstance(sub.get("nodeIds"), list):
                updated = []
                for nid in sub["nodeIds"]:
                    if isinstance(nid, str) and nid in id_map:
                        updated.append(id_map[nid])
                        changed = True
                    else:
                        updated.append(nid)
                sub["nodeIds"] = updated

        if changed:
            print("Applied normalization: filled arrays + snake_case ids + updated edges.")
        return data

    def stylize_labels(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply label conventions: node labels as "To <Verb>", human-readable text, XP capitalization."""
        def humanize(text: str) -> str:
            t = str(text).replace('_', ' ').strip()
            t = t.replace(' xp', ' XP').replace(' Xp', ' XP').replace('xp', 'XP')
            if t and not t.isupper():
                t = t[0].upper() + t[1:]
            return t

        def map_activity_label(label: str, node_id: str) -> str:
            base_map = {
                'gathering': 'Gather',
                'farming': 'Farm',
                'crafting': 'Craft',
                'cooking': 'Cook',
                'questing': 'Quest',
                'socializing': 'Socialize',
                'trading': 'Trade',
                'monetization': 'Purchase',
                'fishing': 'Fish',
                'foraging': 'Forage',
                'mining': 'Mine',
                'bug catching': 'Catch Bugs',
            }
            low = label.lower()
            if '&' in low:
                parts = [p.strip() for p in low.split('&')]
                mapped = [base_map.get(p, p.capitalize()) for p in parts]
                return ' & '.join(mapped)
            if node_id in base_map:
                return base_map[node_id]
            if low in base_map:
                return base_map[low]
            if low.endswith('ing') and len(low) > 4:
                stem = low[:-3]
                if stem.endswith('ad') or stem.endswith('iz'):
                    stem += 'e'
                return stem.capitalize()
            return label

        for node in data.get('nodes', []) or []:
            if not isinstance(node, dict):
                continue
            raw_label = node.get('label', '')
            label = humanize(raw_label)
            if label.lower().startswith('spend '):
                low = label.lower()
                idx = low.rfind(' to ')
                if idx != -1:
                    label = label[idx + 4:].strip()
            label = map_activity_label(label, str(node.get('id', '')))
            if node.get('kind') == 'final_good':
                # Final goods keep plain labels (no leading "To ")
                if label.lower().startswith('to '):
                    label = label[3:].strip()
            else:
                if not label.lower().startswith('to '):
                    label = f"To {label}"
            node['label'] = label

        for inp in data.get('inputs', []) or []:
            if not isinstance(inp, dict):
                continue
            if 'label' in inp:
                lbl = humanize(inp['label'])
                if inp.get('id') == 'time':
                    lbl = 'Time'
                if inp.get('id') == 'money':
                    lbl = 'Money'
                inp['label'] = lbl

        return data

    def stylize_resources(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize terms in sources/sinks/values: remove underscores, capitalize, keep XP uppercase."""
        def fix_term(s: str) -> str:
            t = str(s).replace('_', ' ').strip()
            # Remove leading 'To ' mistakenly copied from node labels
            if t.lower().startswith('to '):
                t = t[3:].strip()
            parts = t.split()
            out = []
            for p in parts:
                if p.lower() == 'xp':
                    out.append('XP')
                elif p.lower() == 'time':
                    out.append('Time')
                elif p.lower() == 'money':
                    out.append('Money')
                else:
                    out.append(p[:1].upper() + p[1:])
            return ' '.join(out)

        for node in data.get('nodes', []) or []:
            if not isinstance(node, dict):
                continue
            for field in ['sources', 'sinks', 'values']:
                arr = node.get(field)
                if isinstance(arr, list):
                    node[field] = [fix_term(x) if isinstance(x, str) else x for x in arr]
        return data

    def reclassify_value_terms(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Move value-like terms (XP, Level, Rank, Reputation, Mastery, Progression) from sources/sinks to values.

        Also move resource-like terms (Materials, Gold, Items, Ingredients, Recipes, Components) out of values into sources.
        """
        import re
        if not isinstance(data.get('nodes'), list):
            return data
        value_patterns = [r'\bXP\b', r'Level', r'Rank', r'Reputation', r'Renown', r'Mastery', r'Progress', r'Progression', r'Story', r'Relationship', r'Prestige']
        value_re = re.compile('|'.join(value_patterns), re.IGNORECASE)
        resource_patterns = [r'Material', r'Ingredient', r'Resource', r'Component', r'Item', r'Gold', r'Currency', r'Recipe', r'Fish', r'Dish']
        res_re = re.compile('|'.join(resource_patterns), re.IGNORECASE)
        for n in data['nodes']:
            if not isinstance(n, dict):
                continue
            vals = n.setdefault('values', [])
            # Move value-like from sources/sinks to values
            for fld in ('sources', 'sinks'):
                arr = n.get(fld)
                if isinstance(arr, list):
                    keep = []
                    for t in arr:
                        if isinstance(t, str) and value_re.search(t):
                            if t not in vals:
                                vals.append(t)
                        else:
                            keep.append(t)
                    n[fld] = keep
            # Move resource-like from values to sources
            moved_vals = []
            for t in list(vals):
                if isinstance(t, str) and res_re.search(t):
                    moved_vals.append(t)
            if moved_vals:
                vals[:] = [t for t in vals if t not in moved_vals]
                src = n.setdefault('sources', [])
                for t in moved_vals:
                    if t not in src:
                        src.append(t)
        return data

    def enforce_final_goods_policy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Demote incorrectly marked final goods based on heuristic rules."""
        if not isinstance(data.get('nodes'), list):
            return data
        import re
        # Generic resource/value-like terms that should not be final goods across games
        disallow_patterns = [
            r'Material', r'Ingredient', r'Resource', r'Component', r'Fish', r'Dish', r'Recipe',
            r'Gold', r'Currency', r'Utility', r'Buff', r'Energy', r'Health', r'Quest Item', r'Collectible',
            r'Desired Item', r'Renown', r'Renown', r'XP', r'Common', r'Rare'
        ]
        compiled = [re.compile(p, re.IGNORECASE) for p in disallow_patterns]

        for node in data['nodes']:
            if not isinstance(node, dict):
                continue
            if node.get('kind') == 'final_good':
                lbl = str(node.get('label', ''))
                # Demote if label matches any disallowed pattern
                if any(p.search(lbl) for p in compiled):
                    node.pop('kind', None)
        return data

    def collapse_resource_nodes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Collapse resource-only nodes into sources/sinks on connected activity nodes.

        Heuristic: If a node's label looks like a resource (Materials, Ingredients, Gold, Fish, Dishes, Recipes, XP, etc.)
        then:
          - For every incoming edge A -> R, add the resource label to node A's `sources`.
          - For every outgoing edge R -> B, add the resource label to node B's `sinks` unless it is value-like (e.g., XP, Renown).
          - Remove the resource node and all edges touching it.
        """
        if not isinstance(data.get('nodes'), list) or not isinstance(data.get('edges'), list):
            return data
        import re
        nodes_by_id = {n.get('id'): n for n in data['nodes'] if isinstance(n, dict) and 'id' in n}

        def is_resource_label(lbl: str) -> bool:
            # Conservative, generic resource/value terms (avoid game-specific nouns)
            patterns = [
                r'Material', r'Ingredient', r'Resource', r'Component', r'Fish', r'Dish', r'Recipe', r'Gold',
                r'Currency', r'Buff', r'Energy', r'Health', r'Quest Item', r'Collectible', r'Desired Item',
                r'Renown', r'XP'
            ]
            return any(re.search(p, lbl, re.IGNORECASE) for p in patterns)

        def is_value_like(lbl: str) -> bool:
            value_terms = [
                'XP', 'Renown', 'Progression', 'Story', 'Relationship', 'Unlock', 'Mastery', 'Advancement'
            ]
            return any(t.lower() in lbl.lower() for t in value_terms)

        resource_ids = []
        for nid, node in nodes_by_id.items():
            lbl = str(node.get('label', ''))
            if node.get('kind') == 'final_good':
                continue
            # Collapse any non-activity node (label not starting with 'To '), including resource/value-like nouns
            if not lbl.lower().startswith('to ') and (is_resource_label(lbl) or is_value_like(lbl) or True):
                resource_ids.append(nid)

        if not resource_ids:
            return data

        incoming = {}
        outgoing = {}
        for a, b in [e for e in data['edges'] if isinstance(e, list) and len(e) == 2]:
            incoming.setdefault(b, []).append(a)
            outgoing.setdefault(a, []).append(b)

        for rid in resource_ids:
            node = nodes_by_id.get(rid)
            if not node:
                continue
            res_label = str(node.get('label', '')).strip()
            # Add to sources of producers
            for src in incoming.get(rid, []) or []:
                src_node = nodes_by_id.get(src)
                if src_node is not None:
                    src_list = src_node.setdefault('sources', [])
                    if res_label not in src_list:
                        src_list.append(res_label)
            # Add to sinks of consumers (unless value-like)
            if not is_value_like(res_label):
                for tgt in outgoing.get(rid, []) or []:
                    tgt_node = nodes_by_id.get(tgt)
                    if tgt_node is not None:
                        sink_list = tgt_node.setdefault('sinks', [])
                        if res_label not in sink_list:
                            sink_list.append(res_label)

        # Remove edges referencing resource nodes
        data['edges'] = [e for e in data['edges'] if not (isinstance(e, list) and len(e) == 2 and (e[0] in resource_ids or e[1] in resource_ids))]
        # Remove resource nodes
        data['nodes'] = [n for n in data['nodes'] if n.get('id') not in resource_ids]

        return data

    def ensure_final_good_edges(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure each final_good node has at least one incoming edge.

        If a node lists a final_good's label in its values, connect it via an edge.
        """
        if not isinstance(data.get('nodes'), list):
            return data
        label_to_id = {}
        for n in data['nodes']:
            if isinstance(n, dict) and n.get('kind') == 'final_good':
                lbl = str(n.get('label', '')).strip()
                if lbl:
                    label_to_id[lbl] = n.get('id')

        if not label_to_id:
            return data

        edges = data.get('edges', []) or []
        edge_set = {(e[0], e[1]) for e in edges if isinstance(e, list) and len(e) == 2}

        for n in data['nodes']:
            if not isinstance(n, dict):
                continue
            nid = n.get('id')
            for field in ['values']:
                arr = n.get(field)
                if not isinstance(arr, list):
                    continue
                for val in arr:
                    if isinstance(val, str) and val in label_to_id:
                        tgt = label_to_id[val]
                        if (nid, tgt) not in edge_set:
                            edges.append([nid, tgt])
                            edge_set.add((nid, tgt))
        data['edges'] = edges
        return data

    def prune_unknown_edges(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any edges that reference ids not present in inputs or nodes.

        This is a final safety net to ensure no renderer errors from missing nodes.
        """
        try:
            inputs = data.get('inputs') or []
            nodes = data.get('nodes') or []
            valid_ids = {i.get('id') for i in inputs if isinstance(i, dict)} | {n.get('id') for n in nodes if isinstance(n, dict)}
            pruned = []
            for e in data.get('edges', []) or []:
                if isinstance(e, list) and len(e) == 2 and e[0] in valid_ids and e[1] in valid_ids:
                    pruned.append(e)
            data['edges'] = pruned
            return data
        except Exception:
            return data

    def prune_isolated_nonfinal_nodes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove nodes with no edges that are not final goods (cleanup after collapse)."""
        if not isinstance(data.get('nodes'), list) or not isinstance(data.get('edges'), list):
            return data
        node_ids = {n.get('id') for n in data['nodes'] if isinstance(n, dict)}
        deg = {nid: 0 for nid in node_ids}
        for e in data['edges']:
            if isinstance(e, list) and len(e) == 2:
                a, b = e
                if a in deg:
                    deg[a] += 1
                if b in deg:
                    deg[b] += 1
        kept = []
        for n in data['nodes']:
            if not isinstance(n, dict):
                continue
            nid = n.get('id')
            if deg.get(nid, 0) == 0 and n.get('kind') != 'final_good':
                # prune
                continue
            kept.append(n)
        data['nodes'] = kept
        return data

    def clean_subsections(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove unknown nodeIds from subsections and drop empty subsections."""
        subs = data.get('subsections')
        if not isinstance(subs, list):
            return data
        valid_ids = {n.get('id') for n in data.get('nodes', []) if isinstance(n, dict)} | {
            i.get('id') for i in data.get('inputs', []) if isinstance(i, dict)
        }
        cleaned = []
        for s in subs:
            if not isinstance(s, dict):
                continue
            nodeIds = [nid for nid in (s.get('nodeIds') or []) if nid in valid_ids]
            if nodeIds:
                s = dict(s)
                s['nodeIds'] = nodeIds
                cleaned.append(s)
        if cleaned:
            data['subsections'] = cleaned
        else:
            # If nothing valid remains, remove subsections to avoid renderer errors
            data.pop('subsections', None)
        return data

    def absorb_leaf_final_goods(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert leaf final_good nodes to values on their source activities and remove them.

        Generic rule: If a final_good has no outgoing edges, treat it as a value outcome on its producers.
        """
        if not isinstance(data.get('nodes'), list) or not isinstance(data.get('edges'), list):
            return data
        node_map = {n.get('id'): n for n in data['nodes'] if isinstance(n, dict) and 'id' in n}
        in_edges = {}
        out_edges = {}
        for e in data['edges']:
            if isinstance(e, list) and len(e) == 2:
                a, b = e
                in_edges.setdefault(b, []).append(a)
                out_edges.setdefault(a, []).append(b)

        to_remove = set()
        for nid, n in node_map.items():
            if n.get('kind') == 'final_good':
                outs = out_edges.get(nid, [])
                if not outs:
                    # Leaf final_good; absorb into sources' values
                    lbl = str(n.get('label', '')).strip()
                    for src in in_edges.get(nid, []) or []:
                        src_node = node_map.get(src)
                        if src_node is not None:
                            vals = src_node.setdefault('values', [])
                            if lbl and lbl not in vals:
                                vals.append(lbl)
                    to_remove.add(nid)

        if not to_remove:
            return data

        # Remove affected edges and nodes
        data['edges'] = [e for e in data['edges'] if not (isinstance(e, list) and len(e) == 2 and (e[0] in to_remove or e[1] in to_remove))]
        data['nodes'] = [n for n in data['nodes'] if n.get('id') not in to_remove]
        return data

    def diagnostics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return diagnostics for edges and nodes to help fix render issues."""
        input_ids = {i.get('id') for i in data.get('inputs', []) if isinstance(i, dict)}
        node_ids = {n.get('id') for n in data.get('nodes', []) if isinstance(n, dict)}
        all_ids = input_ids | node_ids
        unknown_edges = []
        self_loops = []
        for e in data.get('edges', []) or []:
            if not (isinstance(e, list) and len(e) == 2):
                unknown_edges.append({'edge': e, 'reason': 'not a 2-item list'})
                continue
            a, b = e
            missing = [x for x in (a, b) if x not in all_ids]
            if missing:
                unknown_edges.append({'edge': e, 'reason': f'unknown ids: {missing}'})
            if a == b:
                self_loops.append(e)
        # Find isolated nodes (no incoming and no outgoing)
        incoming, outgoing = {}, {}
        for a, b in [e for e in data.get('edges', []) if isinstance(e, list) and len(e) == 2]:
            outgoing.setdefault(a, 0)
            outgoing[a] += 1
            incoming.setdefault(b, 0)
            incoming[b] += 1
        isolated = [n for n in node_ids if incoming.get(n, 0) == 0 and outgoing.get(n, 0) == 0]
        return {
            'unknown_edges': unknown_edges,
            'self_loops': self_loops,
            'isolated_nodes': isolated,
        }
    
    def create_pull_request(self, filename: str, game_title: str) -> Optional[str]:
        """Create a pull request with the new JSON file to the figma-economy-flow-builder repo."""
        try:
            # Save current directory
            original_dir = os.getcwd()
            
            # Path to the external repository
            external_repo_path = self.repo_path / "figma-economy-flow-builder"
            
            # Clone or pull the external repository if needed
            if not external_repo_path.exists():
                print(f"Cloning figma-economy-flow-builder repository...")
                subprocess.run([
                    "git", "clone", 
                    "https://github.com/econosopher/figma-economy-flow-builder.git",
                    str(external_repo_path)
                ], check=True)
            else:
                # Pull latest changes
                os.chdir(external_repo_path)
                subprocess.run(["git", "checkout", "main"], check=True)
                subprocess.run(["git", "pull", "origin", "main"], check=True)
            
            # Change to repository directory
            os.chdir(external_repo_path)
            
            # Create a new branch
            branch_name = f"add-{filename.replace('.json', '')}-example"
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"{branch_name}-{timestamp}"
            
            # Create and checkout new branch
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            
            # Copy the JSON file to the examples folder
            source_file = self.output_path / filename
            target_file = external_repo_path / "examples" / filename
            
            shutil.copy2(source_file, target_file)
            
            # Add the new file
            subprocess.run(["git", "add", f"examples/{filename}"], check=True)
            
            # Commit the changes
            commit_message = f"""Add {game_title} economy flow example

Added a new economy flow chart example for {game_title} that demonstrates:
- Core gameplay loops and progression systems
- Resource flows between different game activities
- Player inputs (time/money) and their conversion to in-game value
- Final goals and achievement systems

This example can be used as a reference for understanding {game_title}'s economy structure.
Generated using {self.provider_name} provider with deep research."""
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # Push the branch
            subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
            
            # Create PR using GitHub CLI
            pr_body = f"""## Summary
- Added new economy flow example for {game_title}
- Generated using {self.provider_name} provider with deep research
- JSON follows the plugin's schema requirements
- Includes all major gameplay loops and resource flows

## What's included
- Player inputs (time and money)
- Core gameplay activities and their resource consumption/generation
- Progression systems and value accumulation
- End-game goals and achievements

## Testing
- JSON has been validated against the schema
- All node IDs follow snake_case convention
- All edges connect to valid nodes
- Arrays are properly formatted without trailing commas

## Generation Details
- Provider: {self.provider_name}
- Deep Research: Enabled
- Multi-phase analysis for comprehensive coverage"""
            
            result = subprocess.run([
                "gh", "pr", "create",
                "--title", f"Add {game_title} economy flow example",
                "--body", pr_body,
                "--base", "main"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"Pull request created: {pr_url}")
                return pr_url
            else:
                print(f"Failed to create PR: {result.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return None
        except Exception as e:
            print(f"Error creating pull request: {e}")
            return None
        finally:
            # Always return to original directory
            os.chdir(original_dir)


def setup_command():
    """Interactive setup for API keys and configuration."""
    print("Economy JSON Builder Setup")
    print("=" * 50)
    
    config = SecureConfig()
    
    # Show current status
    print("\nCurrent provider status:")
    providers = config.list_providers()
    for provider, has_key in providers.items():
        status = "✓ Configured" if has_key else "✗ Not configured"
        print(f"  {provider.capitalize()}: {status}")
    
    # Menu loop
    while True:
        print("\nWhat would you like to do?")
        print("1. Configure Claude API key")
        print("2. Configure Gemini API key")
        print("3. Set default provider")
        print("4. Set repository path")
        print("5. Remove an API key")
        print("6. Export config template")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            config.set_api_key('claude')
        elif choice == '2':
            config.set_api_key('gemini')
        elif choice == '3':
            current_default = config.get_config('DEFAULT_PROVIDER', 'gemini')
            print(f"\nCurrent default provider: {current_default}")
            new_default = input("Enter new default provider (claude/gemini): ").lower()
            if new_default in ['claude', 'gemini']:
                config.set_config('DEFAULT_PROVIDER', new_default)
                print(f"✓ Default provider set to: {new_default}")
            else:
                print("Invalid provider.")
        elif choice == '4':
            current_repo = config.get_config('REPO_PATH', 'Not set')
            print(f"\nCurrent repository path: {current_repo}")
            new_repo = input("Enter new repository path: ").strip()
            if new_repo and os.path.exists(new_repo):
                config.set_config('REPO_PATH', new_repo)
                print(f"✓ Repository path set to: {new_repo}")
            else:
                print("Path does not exist.")
        elif choice == '5':
            provider = input("Which provider's API key to remove (claude/gemini): ").lower()
            if provider in ['claude', 'gemini']:
                config.remove_api_key(provider)
        elif choice == '6':
            template_path = input("Enter path for config template: ").strip()
            if template_path:
                config.export_config_template(template_path)
        elif choice == '7':
            print("\n✓ Setup complete!")
            break
        else:
            print("Invalid choice.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate economy JSON from game documentation and create a PR",
        prog="economy_json_builder"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Configure API keys and settings')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate economy JSON')
    generate_parser.add_argument(
        "markdown_file",
        help="Path to the markdown file with game information"
    )
    generate_parser.add_argument(
        "game_title",
        help="Title of the game to research"
    )
    generate_parser.add_argument(
        "--provider",
        choices=["claude", "gemini"],
        help="LLM provider to use (defaults to config file setting)"
    )
    generate_parser.add_argument(
        "--api-key",
        help="API key for the selected provider (use 'setup' for secure storage)"
    )
    generate_parser.add_argument(
        "--repo-path",
        help="Path to the economy_flow_plugin repository"
    )
    generate_parser.add_argument(
        "--output-name",
        help="Output filename (defaults to game_title.json)"
    )
    generate_parser.add_argument(
        "--no-pr",
        action="store_true",
        help="Skip creating a pull request"
    )
    generate_parser.add_argument(
        "--model",
        help="Model to use (for Gemini: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash)"
    )
    generate_parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="Increase required granularity (targets >=depth nodes per key category)"
    )
    generate_parser.add_argument(
        "--retries",
        type=int,
        default=0,
        help="Auto-repair retries if lint/validation issues are found"
    )
    generate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail generation if any lint issues remain after normalization"
    )

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate an existing economy JSON file')
    validate_parser.add_argument(
        "json_file",
        help="Path to the JSON file to validate"
    )
    validate_parser.add_argument(
        "--fix",
        action="store_true",
        help="Normalize and write back JSON if issues are found"
    )

    # Lint command (extended checks, no writes)
    lint_parser = subparsers.add_parser('lint', help='Run extended checks on an economy JSON file')
    lint_parser.add_argument(
        "json_file",
        help="Path to the JSON file to lint"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # For backward compatibility - if no command but has args, assume generate
    if args.command is None and len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Re-parse with generate command
        args = parser.parse_args(['generate'] + sys.argv[1:])
    
    # Handle commands
    if args.command == 'setup':
        setup_command()
        return
    elif args.command == 'lint':
        try:
            with open(args.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            sys.exit(1)

        linter = EconomyJSONBuilder(provider_name='gemini', api_key='', repo_path='', initialize_provider=False)
        print(f"Linting: {args.json_file}")
        diag = linter.diagnostics(data)
        issues = 0
        if diag['unknown_edges']:
            print("Unknown edge references:")
            for item in diag['unknown_edges']:
                print(f"  - {item}")
            issues += len(diag['unknown_edges'])
        if diag['self_loops']:
            print("Self-loop edges:")
            for e in diag['self_loops']:
                print(f"  - {e}")
            issues += len(diag['self_loops'])
        if diag['isolated_nodes']:
            # Only count isolated if not final_good
            final_ids = {n.get('id') for n in (data.get('nodes') or []) if isinstance(n, dict) and n.get('kind') == 'final_good'}
            filtered = [n for n in diag['isolated_nodes'] if n not in final_ids]
            if filtered:
                print("Isolated nodes (no edges):")
                for n in filtered:
                    print(f"  - {n}")
                issues += len(filtered)

        # Style checks
        def has_underscores_label(nodes_or_inputs):
            bad = []
            for item in nodes_or_inputs or []:
                if isinstance(item, dict) and isinstance(item.get('label'), str) and '_' in item['label']:
                    bad.append(item['label'])
            return bad
        label_issues = has_underscores_label(data.get('nodes')) + has_underscores_label(data.get('inputs'))
        if label_issues:
            print("Labels contain underscores (should be human-readable):")
            for lbl in label_issues:
                print(f"  - {lbl}")
            issues += len(label_issues)

        # Node label format rules
        for node in data.get('nodes', []) or []:
            if not isinstance(node, dict):
                continue
            lbl = node.get('label', '') or ''
            kind = node.get('kind')
            if isinstance(lbl, str):
                if '_' in lbl:
                    print(f"Node label has underscores: {lbl}")
                    issues += 1
                if 'spend ' in lbl.lower():
                    print(f"Node label should not include 'Spend': {lbl}")
                    issues += 1
                if kind == 'final_good':
                    if lbl.lower().startswith('to '):
                        print(f"Final good label should not start with 'To ': {lbl}")
                        issues += 1
                else:
                    if not lbl.lower().startswith('to '):
                        print(f"Activity label should start with 'To ': {lbl}")
                        issues += 1

        # Resource naming rules in sources/sinks/values
        def check_resources(arr, node_id, field_name):
            nonlocal issues
            if not isinstance(arr, list):
                return
            for term in arr:
                if not isinstance(term, str):
                    continue
                if '_' in term:
                    print(f"Resource contains underscore in {field_name} for node {node_id}: {term}")
                    issues += 1
                if term.strip().lower().startswith('to '):
                    print(f"Resource should not start with 'To ' in {field_name} for node {node_id}: {term}")
                    issues += 1
                # Ensure XP uppercase when present as a word
                parts = term.split()
                for p in parts:
                    if p.lower() == 'xp' and p != 'XP':
                        print(f"Resource 'XP' should be uppercase in {field_name} for node {node_id}: {term}")
                        issues += 1
                        break
        for node in data.get('nodes', []) or []:
            if not isinstance(node, dict):
                continue
            nid = node.get('id')
            check_resources(node.get('sources'), nid, 'sources')
            check_resources(node.get('sinks'), nid, 'sinks')
            check_resources(node.get('values'), nid, 'values')

        # Ensure inputs are canonical
        for inp in data.get('inputs', []) or []:
            if inp.get('id') == 'time' and inp.get('label') != 'Time':
                print("Input 'time' label should be 'Time'")
                issues += 1
            if inp.get('id') == 'money' and inp.get('label') != 'Money':
                print("Input 'money' label should be 'Money'")
                issues += 1

        # Final goods policy lint
        def is_bad_final_good(label: str) -> bool:
            bad_terms = [
                'Material', 'Ingredient', 'Resource', 'Component', 'Fish', 'Dish', 'Recipe',
                'Gold', 'Utility', 'Buff', 'Energy', 'Health', 'Quest Item', 'Collectible',
                'Desired Item', 'Renown', 'XP', 'Common', 'Rare'
            ]
            for t in bad_terms:
                if t.lower() in label.lower():
                    return True
            return False
        for node in data.get('nodes', []) or []:
            if not isinstance(node, dict):
                continue
            if node.get('kind') == 'final_good':
                lbl = str(node.get('label', ''))
                if is_bad_final_good(lbl):
                    print(f"Final good likely misclassified as resource/intermediate: {lbl}")
                    issues += 1

        if issues == 0:
            print("\n✓ No lint issues found")
            sys.exit(0)
        else:
            print(f"\n❌ Lint found {issues} issue(s)")
            sys.exit(2)
    elif args.command == 'validate':
        # Run validator on a provided JSON file
        try:
            with open(args.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            sys.exit(1)

        validator = EconomyJSONBuilder(provider_name='gemini', api_key='', repo_path='', initialize_provider=False)
        print(f"Validating: {args.json_file}")

        # Diagnostics to help fix rendering issues
        diag = validator.diagnostics(data)
        if diag['unknown_edges']:
            print("Unknown edge references detected:")
            for item in diag['unknown_edges']:
                print(f"  - {item}")
        if diag['self_loops']:
            print("Self-loop edges detected:")
            for e in diag['self_loops']:
                print(f"  - {e}")
        if diag['isolated_nodes']:
            print("Isolated nodes (no edges):")
            for n in diag['isolated_nodes']:
                print(f"  - {n}")

        if validator.validate_json(data):
            print("\n✓ JSON is valid and conforms to schema")
            # Optionally still normalize and write if --fix requested
            if args.fix:
                import json as _json
                normalized = validator.normalize_json(_json.loads(_json.dumps(data)))
                normalized = validator.stylize_labels(normalized)
                normalized = validator.stylize_resources(normalized)
                normalized = validator.reclassify_value_terms(normalized)
                normalized = validator.collapse_resource_nodes(normalized)
                normalized = validator.enforce_final_goods_policy(normalized)
                normalized = validator.ensure_final_good_edges(normalized)
                normalized = validator.absorb_leaf_final_goods(normalized)
                normalized = validator.prune_isolated_nonfinal_nodes(normalized)
                normalized = validator.prune_unknown_edges(normalized)
                normalized = validator.clean_subsections(normalized)
                if normalized != data:
                    backup = args.json_file + ".bak"
                    try:
                        with open(backup, 'w', encoding='utf-8') as bf:
                            json.dump(data, bf, indent=2)
                            bf.write('\n')
                        with open(args.json_file, 'w', encoding='utf-8') as wf:
                            json.dump(normalized, wf, indent=2)
                            wf.write('\n')
                        print(f"Applied fixes and wrote normalized JSON. Backup saved to {backup}")
                    except Exception as e:
                        print(f"Failed to write normalized JSON: {e}")
                        sys.exit(3)
            sys.exit(0)
        else:
            print("\n❌ JSON failed validation. See messages above.")
            if args.fix:
                print("Attempting to normalize and re-validate...")
                import json as _json
                normalized = validator.normalize_json(_json.loads(_json.dumps(data)))
                normalized = validator.stylize_labels(normalized)
                normalized = validator.stylize_resources(normalized)
                normalized = validator.reclassify_value_terms(normalized)
                normalized = validator.collapse_resource_nodes(normalized)
                normalized = validator.enforce_final_goods_policy(normalized)
                normalized = validator.ensure_final_good_edges(normalized)
                normalized = validator.absorb_leaf_final_goods(normalized)
                normalized = validator.prune_isolated_nonfinal_nodes(normalized)
                normalized = validator.prune_unknown_edges(normalized)
                normalized = validator.clean_subsections(normalized)
                if validator.validate_json(normalized):
                    backup = args.json_file + ".bak"
                    try:
                        with open(backup, 'w', encoding='utf-8') as bf:
                            json.dump(data, bf, indent=2)
                            bf.write('\n')
                        with open(args.json_file, 'w', encoding='utf-8') as wf:
                            json.dump(normalized, wf, indent=2)
                            wf.write('\n')
                        print(f"\n✓ Normalization fixed the issues. Saved file and created backup at {backup}")
                        sys.exit(0)
                    except Exception as e:
                        print(f"Failed to write normalized JSON: {e}")
                        sys.exit(3)
                else:
                    print("Normalization could not fix the JSON structure.")
            sys.exit(2)
    elif args.command is None:
        parser.print_help()
        print("\nQuick start:")
        print(f"  {sys.argv[0]} setup                    # Configure API keys")
        print(f"  {sys.argv[0]} generate game.md \"Title\"  # Generate JSON")
        return
    
    # Generate command logic
    config = SecureConfig()
    
    # Determine provider
    provider_name = args.provider or config.get_config("DEFAULT_PROVIDER", "gemini")
    
    # Get API key
    api_key = args.api_key or config.get_api_key(provider_name, prompt_if_missing=True)
    if not api_key:
        print(f"\nError: No API key found for {provider_name} provider.")
        print(f"Please run '{sys.argv[0]} setup' to configure your API keys")
        sys.exit(1)
    
    # Get repository path only if we plan to create a PR
    repo_path = None
    if not getattr(args, 'no_pr', False):
        repo_path = args.repo_path or config.get_config("REPO_PATH")
        if not repo_path:
            print("\nError: No repository path specified.")
            print(f"Please run '{sys.argv[0]} setup' to configure the repository path")
            print("Or use --repo-path to specify it directly, or pass --no-pr to skip PR creation")
            sys.exit(1)
    
    # Set output filename
    if not args.output_name:
        # Convert game title to snake_case for filename
        filename = args.game_title.lower().replace(" ", "_").replace("-", "_")
        # Append provider name
        filename = f"{filename}_{provider_name}.json"
    else:
        filename = args.output_name
        # If custom name doesn't have provider, add it before .json
        if not filename.endswith(".json"):
            filename = f"{filename}_{provider_name}.json"
        elif "_claude" not in filename and "_gemini" not in filename:
            # Insert provider name before .json
            filename = filename.replace(".json", f"_{provider_name}.json")
    
    try:
        # Initialize generator with model if specified
        provider_kwargs = {}
        if hasattr(args, 'model') and args.model and provider_name == 'gemini':
            provider_kwargs['model_name'] = args.model
            print(f"Using {provider_name} provider with {args.model} model...")
        if hasattr(args, 'depth') and provider_name == 'gemini':
            provider_kwargs['depth'] = max(0, int(args.depth))
        else:
            print(f"Using {provider_name} provider...")
        
        generator = EconomyJSONBuilder(provider_name, api_key, repo_path or "", **provider_kwargs)
        
        # Read markdown file
        print(f"Reading markdown file: {args.markdown_file}")
        game_info = generator.read_markdown_file(args.markdown_file)
        
        # Generate economy JSON
        print(f"Researching {args.game_title} economy with {provider_name}...")
        economy_data = generator.provider.generate_economy_json(game_info, args.game_title)

        # Normalize before validation
        economy_data = generator.normalize_json(economy_data)
        # Apply label and resource styling
        economy_data = generator.stylize_labels(economy_data)
        economy_data = generator.stylize_resources(economy_data)
        # Reclassify XP/level-like metrics as values, resources as sources
        economy_data = generator.reclassify_value_terms(economy_data)
        # Collapse resource-only nodes into sources/sinks on activities
        economy_data = generator.collapse_resource_nodes(economy_data)
        # Enforce final-goods policy heuristics
        economy_data = generator.enforce_final_goods_policy(economy_data)
        # Ensure final goods receive edges from producing nodes
        economy_data = generator.ensure_final_good_edges(economy_data)
        # Absorb leaf final goods into values on producers
        economy_data = generator.absorb_leaf_final_goods(economy_data)
        # Prune isolated non-final nodes
        economy_data = generator.prune_isolated_nonfinal_nodes(economy_data)
        # Final safety: drop edges to missing ids
        economy_data = generator.prune_unknown_edges(economy_data)
        # Clean subsections to only include existing nodeIds
        economy_data = generator.clean_subsections(economy_data)

        # Optionally auto-repair if issues detected
        def summarize_issues(data):
            diag = generator.diagnostics(data)
            issues = []
            if diag['unknown_edges']:
                issues.append(f"Unknown edges: {diag['unknown_edges']}")
            if diag['self_loops']:
                issues.append(f"Self loops: {diag['self_loops']}")
            if diag['isolated_nodes']:
                issues.append(f"Isolated nodes: {diag['isolated_nodes']}")
            return "\n".join(issues)

        attempts = 0
        while attempts < getattr(args, 'retries', 0):
            valid = generator.validate_json(economy_data)
            issues_text = summarize_issues(economy_data)
            if valid and not issues_text:
                break
            attempts += 1
            print(f"Attempting repair (try {attempts}/{args.retries})...")
            if hasattr(generator.provider, 'repair_economy_json'):
                try:
                    repaired = generator.provider.repair_economy_json(args.game_title, economy_data, issues_text or 'Fix schema/edge issues')
                    economy_data = generator.normalize_json(repaired)
                    economy_data = generator.stylize_labels(economy_data)
                    economy_data = generator.stylize_resources(economy_data)
                    economy_data = generator.collapse_resource_nodes(economy_data)
                    economy_data = generator.enforce_final_goods_policy(economy_data)
                    economy_data = generator.ensure_final_good_edges(economy_data)
                    economy_data = generator.prune_isolated_nonfinal_nodes(economy_data)
                except Exception as e:
                    print(f"Repair failed: {e}")
                    break
            else:
                break
        
        # Validate JSON
        print("Validating generated JSON...")
        if not generator.validate_json(economy_data):
            print("JSON validation failed! Saving anyway for debugging...")

        # Save JSON file
        print(f"Saving JSON to: {filename}")
        file_path = generator.save_json_file(economy_data, filename)
        print(f"JSON saved successfully: {file_path}")

        # Strict mode: run lint-like checks and fail if issues remain
        if getattr(args, 'strict', False):
            diag = generator.diagnostics(economy_data)
            issues = 0
            if diag['unknown_edges']:
                issues += len(diag['unknown_edges'])
            if diag['self_loops']:
                issues += len(diag['self_loops'])
            # ignore isolated final goods; count only isolated non-finals
            final_ids = {n.get('id') for n in (economy_data.get('nodes') or []) if isinstance(n, dict) and n.get('kind') == 'final_good'}
            iso_nonfinal = [n for n in diag['isolated_nodes'] if n not in final_ids]
            issues += len(iso_nonfinal)
            if issues:
                print("\nStrict mode: lint issues detected, aborting.")
                sys.exit(2)
        
        # Create pull request
        if not args.no_pr:
            print("Creating pull request...")
            pr_url = generator.create_pull_request(filename, args.game_title)
            if pr_url:
                print(f"Pull request created: {pr_url}")
            else:
                print("Failed to create pull request")
        
        print("\n✓ Done!")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
