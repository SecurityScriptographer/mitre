from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def_tech_descriptions = {}

def map_relationships_to_techniques(techniques: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Maps relationships to techniques

    Args:
        techniques (List[Dict[str, Any]]): base technique dictionary
        relationships (List[Dict[str, Any]]): relationships to be mapped

    Returns:
        List[Dict[str, Any]]: technique dictionary with mapped relationships
    """
    logger.info("mapping relationships to att&ck")
    relationship_map = prepare_relationship_mapping(relationships)
    
    for technique in techniques:
        technique_id = technique.get("id")
        if technique_id in relationship_map:
            maps_for_technique = relationship_map[technique_id]
            for map_for_technique in maps_for_technique:
                if map_for_technique['relationship_type'] == 'mitigates':
                    technique['mitigations'].append(map_for_technique)
                else:
                    technique['related_relationships'].append(map_for_technique)
    return techniques

def map_groups_to_techniques(techniques: List[Dict[str, Any]], groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Maps groups to techniques

    Args:
        techniques (List[Dict[str, Any]]): base technique dictionary
        groups (List[Dict[str, Any]]): groups to be mapped

    Returns:
        List[Dict[str, Any]]: technique dictionary with mapped groups
    """
    logger.info("mapping groups to att&ck")
    group_map = {group['id']: group for group in groups}
   
    for technique in techniques:
        groups = []
        for relationship in technique['related_relationships']:
            if 'relationship_type' in relationship:
                if relationship['relationship_type'] == 'uses' and relationship['source_ref'].startswith('intrusion-set'):
                    group_id = relationship['source_ref']
                    if group_id in group_map:
                        group_ref = {
                            "id": group_map[group_id]["id"],
                            "name": group_map[group_id]["name"],
                            "group_id": group_id,
                            "aliases": group_map[group_id].get("aliases", []),
                            "description": group_map[group_id].get("description", "")
                        }
                        groups.append(group_ref)
        technique["groups"] = groups
    return techniques

def map_mitigations_to_techniques(techniques: List[Dict[str, Any]], mitigations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Maps mitigations to techniques

    Args:
        techniques (List[Dict[str, Any]]): base technique dictionary
        mitigations (List[Dict[str, Any]]): mitigations to be mapped

    Returns:
        List[Dict[str, Any]]: technique dictionary with mapped mitigations
    """
    logger.info("mapping mitigations to att&ck")
    mitigation_dict = {mitigation['id']: mitigation for mitigation in mitigations}

    for technique in techniques:
        for tech_mitigation in technique['mitigations']:
            if tech_mitigation['source_ref'] in mitigation_dict:
                tech_mitigation['mitigation_id'] = mitigation_dict[tech_mitigation['source_ref']]['mitigation_id']
            else:
                logger.warning(f"{tech_mitigation['source_ref']} not in mitigation_dict")
    
    return techniques

def map_all_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """starting all map functions

    Args:
        data (Dict[str, Any]): loaded data

    Returns:
        Dict[str, Any]: mapped data
    """
    techniques = data['techniques']
    techniques = map_relationships_to_techniques(techniques, data['relationships'])
    techniques = map_groups_to_techniques(techniques, data['groups'])
    techniques = map_mitigations_to_techniques(techniques, data['mitigations'])
    
    return techniques

def prepare_relationship_mapping(relationships: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """util function for mapping relationships to techniques

    Args:
        relationships (List[Dict[str, Any]]): all relationships

    Returns:
        Dict[str, List[Dict[str, Any]]]: all relationships with relationship ids as keys
    """
    relationship_map = {}
    for relationship in relationships:
        target_ref = relationship.get("target_ref")
        if target_ref not in relationship_map:
            relationship_map[target_ref] = []
        relationship_map[target_ref].append(relationship)
    return relationship_map