# optimizer.py
import datetime
import json
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def optimize_group_data(group: Dict) -> Dict:
    """Extract only essential group information"""
    return {
        "id": group.get("id"),
        "name": group.get("name"),
        "aliases": group.get("aliases", []),
        "description": group.get("description")
    }

def optimize_d3fend_references(techniques: List[Dict]) -> Dict:
    """
    Optimize D3FEND data by deduplicating common references and authors across techniques
    """
    # Create reference and author lookup tables
    reference_lookup = {}
    author_lookup = {}
    ref_counter = 0
    author_counter = 0

    # First pass: build lookup tables
    for tech in techniques:
        if 'd3fend' in tech:
            for d3f in tech['d3fend']:
                # Handle references
                if 'references' in d3f:
                    new_refs = []
                    for ref in d3f['references']:
                        # Create a unique key from the reference URL
                        ref_key = ref['url'] if isinstance(ref, dict) else ref
                        if ref_key not in reference_lookup:
                            ref_counter += 1
                            reference_lookup[ref_key] = {
                                'id': str(ref_counter),
                                'data': ref
                            }
                        new_refs.append(reference_lookup[ref_key]['id'])
                    d3f['references'] = new_refs

                # Handle authors
                if 'authors' in d3f:
                    new_authors = []
                    for author in d3f['authors']:
                        if author not in author_lookup:
                            author_counter += 1
                            author_lookup[author] = str(author_counter)
                        new_authors.append(author_lookup[author])
                    d3f['authors'] = new_authors

    # Create reverse lookups for the final data
    reference_reverse_lookup = {
        v['id']: v['data'] for v in reference_lookup.values()
    }
    author_reverse_lookup = {v: k for k, v in author_lookup.items()}

    return {
        'techniques': techniques,
        'metadata': {
            'reference_lookup': reference_reverse_lookup,
            'author_lookup': author_reverse_lookup,
            'generated_at': datetime.datetime.now().isoformat(),
            'version': '1.0',
            'technique_count': len(techniques)
        }
    }

def optimize_technique_data(technique: Dict) -> Dict:
    """Optimizes technique data structure to minimize size while retaining essential information"""
    return {
        "type": "attack-pattern",
        "id": technique.get("id"),
        "technique_id": technique.get("technique_id"),
        "name": technique.get("name"),
        "description": technique.get("description"),
        "groups": [optimize_group_data(group) for group in technique.get("groups", [])],
        "d3fend": technique.get("d3fend", []),  # D3FEND data is already optimized in map_d3fend_to_technique
        "all_references": technique.get("all_references", []),
        "mitigations": technique.get("mitigations", [])
    }

def save_optimized_data(mapped_techniques: List[Dict], output_path: str):
    """Save optimized technique data with improved compression"""
    
    # First optimize each technique
    optimized_techniques = [optimize_technique_data(tech) for tech in mapped_techniques]
    
    # Then optimize D3FEND references across all techniques
    optimized_data = optimize_d3fend_references(optimized_techniques)
    
    # Remove empty values
    def clean_empty(d):
        if isinstance(d, dict):
            return {k: clean_empty(v) for k, v in d.items() 
                   if v not in (None, "", [], {}, 0) and clean_empty(v) not in (None, "", [], {}, 0)}
        elif isinstance(d, list):
            return [clean_empty(item) for item in d if item not in (None, "", [], {}, 0)]
        return d
    
    optimized_data = clean_empty(optimized_data)
    
    # Use optimal JSON encoding
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(optimized_data, f, 
                 ensure_ascii=False,
                 separators=(',', ':'),
                 check_circular=False)