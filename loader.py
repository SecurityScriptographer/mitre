import json
import logging
import os
from typing import Dict, Any
from mitreattack.stix20 import MitreAttackData

logger = logging.getLogger(__name__)

def load_attack_data(use_cache: bool = True) -> MitreAttackData:
    """Initialize MitreAttackData with STIX data"""
    stix_path = os.path.join(os.path.dirname(__file__), 'cache', 'enterprise-attack.json')
    
    if not os.path.exists(os.path.dirname(stix_path)):
        os.makedirs(os.path.dirname(stix_path))
    
    if os.path.exists(stix_path) and use_cache:
        logger.info("Loading STIX data from cache")
    else:
        logger.info("Downloading latest STIX data")
        import requests
        
        url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
        response = requests.get(url)
        response.raise_for_status()
        
        with open(stix_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
    
    try:
        return MitreAttackData(stix_filepath=stix_path)
    except Exception as e:
        logger.error(f"Failed to initialize MitreAttackData: {str(e)}")
        raise

def make_json_serializable(obj):
    """Convert STIX objects to dictionaries"""
    if hasattr(obj, 'serialize'):
        return json.loads(obj.serialize())
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(i) for i in obj]
    return obj

def get_techniques(attack: MitreAttackData) -> list:
    """Get all techniques from MITRE ATT&CK"""
    techniques = []
    for technique in attack.get_techniques():
        # Extract technique ID from external references
        technique_id = None
        external_references = []
        
        if hasattr(technique, 'external_references'):
            external_references = make_json_serializable(technique.external_references)
            # Find technique ID
            for ref in external_references:
                if ref.get('source_name') == 'mitre-attack':
                    technique_id = ref.get('external_id')
                    break
                
        if technique_id:
            techniques.append({
                "technique_id": technique_id,
                "id": technique.id,
                "name": technique.name,
                "description": technique.description,
                "external_references": external_references,
                "groups": [],
                "mitigations": []
            })
    return techniques

def load_all_data(use_cache: bool = True) -> Dict[str, Any]:
    """Load all MITRE ATT&CK data"""
    attack = load_attack_data(use_cache)
    
    # Get and serialize groups and mitigations
    groups = [make_json_serializable(group) for group in attack.get_groups()]
    mitigations = [make_json_serializable(mitigation) for mitigation in attack.get_mitigations()]
    
    return {
        'techniques': get_techniques(attack),
        'groups': groups,
        'mitigations': mitigations,
        'attack': attack
    }