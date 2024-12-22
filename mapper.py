from typing import Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)

def clean_group_data(group_data):
    """
    Merges and cleans up MITRE ATT&CK group data structure by flattening the nested structure.
    
    Args:
        group_data (dict): Raw group data with 'object' and 'relationships' properties
        
    Returns:
        dict: Cleaned data with merged properties
    """
    if not isinstance(group_data, dict):
        return None
        
    # Extract main object properties and relationships
    cleaned_data = group_data.get('object', {})
    
    return cleaned_data

def make_json_serializable(obj):
    """Convert STIX objects to dictionaries"""
    if hasattr(obj, 'serialize'):
        return json.loads(obj.serialize())
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(i) for i in obj]
    return obj

class TechniqueMapper:
    def __init__(self, attack):
        self.attack = attack
    
    def map_groups_to_technique(self, technique_id: str) -> List[Dict[str, Any]]:
        """Maps groups to a specific technique"""
        try:
            if not technique_id:
                return []
                
            tech_obj = self.attack.get_object_by_attack_id(technique_id, "attack-pattern")
            if not tech_obj:
                logger.warning(f"Could not find technique object for {technique_id}")
                return []
                
            logger.debug(f"Getting groups for technique {technique_id}")
            
            # Get groups using this technique
            groups = self.attack.get_groups_using_technique(tech_obj.id)
            if groups:
                serialized_groups = [make_json_serializable(group) for group in groups]
                return [clean_group_data(group) for group in serialized_groups]
            return []
            
        except Exception as e:
            logger.error(f"Error mapping groups for technique {technique_id}: {str(e)}", exc_info=True)
            return []
    
    def map_mitigations_to_technique(self, technique_id: str) -> List[Dict[str, Any]]:
        """Maps mitigations to a specific technique"""
        try:
            if not technique_id:
                return []
                
            tech_obj = self.attack.get_object_by_attack_id(technique_id, "attack-pattern")
            if not tech_obj:
                return []
                
            logger.debug(f"Getting mitigations for technique {technique_id}")
            
            # Get mitigations for this technique
            mitigations = self.attack.get_mitigations_mitigating_technique(tech_obj.id)
            if mitigations:
                return [make_json_serializable(mitigation) for mitigation in mitigations]
            return []
            
        except Exception as e:
            logger.error(f"Error mapping mitigations for technique {technique_id}: {str(e)}", exc_info=True)
            return []
    
    def map_all_techniques(self, techniques: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Maps groups and mitigations to all techniques"""
        logger.info("Mapping techniques to groups and mitigations...")
        total = len(techniques)
        
        for i, technique in enumerate(techniques, 1):
            if i % 50 == 0:
                logger.info(f"Processed {i}/{total} techniques...")
                
            technique_id = technique.get('technique_id')
            logger.debug(f"Processing technique {technique_id}")
            
            groups = self.map_groups_to_technique(technique_id)
            if groups:
                technique['groups'] = groups
                logger.debug(f"Found {len(groups)} groups for technique {technique_id}")
            
            mitigations = self.map_mitigations_to_technique(technique_id)
            if mitigations:
                technique['mitigations'] = mitigations
                logger.debug(f"Found {len(mitigations)} mitigations for technique {technique_id}")
        
        logger.info("Finished mapping all techniques")
        return techniques

def map_all_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Main function to map all relationships"""
    attack = data['attack']
    
    mapper = TechniqueMapper(attack)
    mapped_data = mapper.map_all_techniques(data['techniques'])
    
    # Ensure everything is JSON serializable
    return make_json_serializable(mapped_data)