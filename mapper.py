from typing import Dict, Any, List
import logging
import json
from loader import load_d3fend_data, load_d3fend_technique_details

logger = logging.getLogger(__name__)

def clean_group_data(group_data):
    """
    Merges and cleans up MITRE ATT&CK group data structure.
    Added debug logging to trace data transformation.
    """
    
    if not isinstance(group_data, dict):
        logger.warning(f"Group data is not a dict: {type(group_data)}")  # Added debug log
        return None
        
    # Extract main object properties and relationships
    cleaned_data = group_data.get('object', group_data)  # Modified to handle both formats
    
    return cleaned_data

def clean_mitigation_data(mitigation_data):
    """
    Merges and cleans up MITRE ATT&CK mitigation data structure by flattening the nested structure.
    
    Args:
        mitigation_data (dict): Raw mitigation data with 'object' and 'relationships' properties
        
    Returns:
        dict: Cleaned data with merged properties
    """
    if not isinstance(mitigation_data, dict):
        return None
        
    # Extract main object properties and relationships
    cleaned_data = mitigation_data.get('object', {})
    
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
        self.d3fend_cache = {}
    
    def map_groups_to_technique(self, technique_id: str) -> List[Dict[str, Any]]:
        """Maps groups to a specific technique with debug logging"""
        try:
            if not technique_id:
                return []
                
            tech_obj = self.attack.get_object_by_attack_id(technique_id, "attack-pattern")
            if not tech_obj:
                logger.warning(f"Could not find technique object for {technique_id}")
                return []
                
            
            # Get groups using this technique
            groups = self.attack.get_groups_using_technique(tech_obj.id)
            if groups:
                serialized_groups = [make_json_serializable(group) for group in groups]
                cleaned_groups = [clean_group_data(group) for group in serialized_groups]
                return cleaned_groups
            
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
                
            
            # Get mitigations for this technique
            mitigations = self.attack.get_mitigations_mitigating_technique(tech_obj.id)
            if mitigations:
                return [clean_mitigation_data(make_json_serializable(mitigation)) for mitigation in mitigations]
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
            
            groups = self.map_groups_to_technique(technique_id)
            if groups:
                technique['groups'] = groups
            
            mitigations = self.map_mitigations_to_technique(technique_id)
            if mitigations:
                technique['mitigations'] = mitigations
        
        logger.info("Finished mapping all techniques")
        return techniques
    
    def map_d3fend_to_technique(self, technique_id: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Maps D3FEND defensive techniques to an ATT&CK technique with full references"""
        try:
            if not technique_id:
                return []

            d3fend_data = load_d3fend_data(technique_id, use_cache)
            if not d3fend_data or 'off_to_def' not in d3fend_data:
                return []

            d3fend_techniques = []
            bindings = d3fend_data['off_to_def']['results']['bindings']
            
            for binding in bindings:
                if 'def_tech_label' not in binding:
                    continue
                    
                def_tech_id = binding['def_tech']['value'].split('#')[-1]
                
                if def_tech_id not in self.d3fend_cache:
                    self.d3fend_cache[def_tech_id] = load_d3fend_technique_details(def_tech_id, use_cache)
                
                def_tech_details = self.d3fend_cache[def_tech_id]
                if not def_tech_details:
                    continue

                description = None
                
                if 'description' in def_tech_details and '@graph' in def_tech_details['description']:
                    graph = def_tech_details['description']['@graph']
                    if graph:
                        def_text = graph[0].get('d3f:definition', '')
                        if isinstance(def_text, str):
                            description = def_text
                        elif isinstance(def_text, list):
                            description = def_text[0] if def_text else None

                # Create technique info
                technique_info = {
                    "id": def_tech_id,
                    "title": binding['def_tech_label']['value'],
                    "url": f"https://d3fend.mitre.org/technique/d3f:{def_tech_id}"
                }

                if description:
                    technique_info["description"] = description

                # Add full references and authors information
                if 'references' in def_tech_details and def_tech_details['references'].get('@graph'):
                    ref_graph = def_tech_details['references']['@graph'][0]
                    
                    # Get all reference information
                    if '@graph' in def_tech_details['references']:
                        references = []
                        for ref in def_tech_details['references']['@graph']:
                            if 'd3f:has-link' in ref:
                                ref_url = ref.get('d3f:has-link', {}).get('@value')
                                ref_desc = ref.get('d3f:description', '')
                                if ref_url:
                                    references.append({
                                        'url': ref_url,
                                        'description': ref_desc
                                    })
                        if references:
                            technique_info["references"] = references

                    # Get author information
                    if 'd3f:kb-author' in ref_graph:
                        author_value = ref_graph['d3f:kb-author']
                        if isinstance(author_value, str):
                            # Split by comma and clean up each author name
                            authors = [a.strip() for a in author_value.split(',') if a.strip()]
                            if authors:
                                technique_info["authors"] = authors
                        elif isinstance(author_value, list):
                            technique_info["authors"] = author_value

                # Log for debugging
                logger.debug(f"D3FEND technique for {def_tech_id}:")
                if "references" in technique_info:
                    logger.debug(f"References: {technique_info['references']}")
                if "authors" in technique_info:
                    logger.debug(f"Authors: {technique_info['authors']}")

                d3fend_techniques.append(technique_info)

            return d3fend_techniques

        except Exception as e:
            logger.error(f"Error mapping D3FEND data for technique {technique_id}: {str(e)}", exc_info=True)
            return []


    def map_all_techniques(self, techniques: List[Dict[str, Any]], use_cache: bool = True) -> List[Dict[str, Any]]:
        """Maps all relationships (groups, mitigations, and D3FEND) to techniques"""
        logger.info("Mapping techniques to groups, mitigations, and D3FEND...")
        total = len(techniques)
        
        for i, technique in enumerate(techniques, 1):
            if i % 50 == 0:
                logger.info(f"Processed {i}/{total} techniques...")
                
            technique_id = technique.get('technique_id')
            logger.debug(f"Processing technique {technique_id}")
            
            # Map all relationships
            groups = self.map_groups_to_technique(technique_id)
            if groups:
                technique['groups'] = groups
                
            mitigations = self.map_mitigations_to_technique(technique_id)
            if mitigations:
                technique['mitigations'] = mitigations
            
            d3fend = self.map_d3fend_to_technique(technique_id, use_cache)
            if d3fend:
                technique['d3fend'] = d3fend
        
        logger.info("Finished mapping all techniques")
        return techniques

def map_all_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Main function to map all relationships"""
    attack = data['attack']
    
    mapper = TechniqueMapper(attack)
    mapped_data = mapper.map_all_techniques(data['techniques'])
    
    # Ensure everything is JSON serializable
    return make_json_serializable(mapped_data)