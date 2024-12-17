import json
import logging
import os
from attackcti import attack_client
from typing import Dict, Any, List
from config import TECH_PATH, RELATIONS_PATH, GROUPS_PATH, MIT_PATH

logger = logging.getLogger(__name__)

def load_json(file_path: str) -> Dict[str, Any]:
    """Help function to load json data

    Args:
        file_path (str): path to file

    Returns:
        Dict[str, Any]: json data as dictionary
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}

def load_techniques(use_cache: bool) -> List[Dict[str, Any]]:
    """loading mitre techniques

    Args:
        use_cache (bool): if cache should not be used

    Returns:
        List[Dict[str, Any]]: mitre techniques as dictionary
    """
    if os.path.exists(TECH_PATH) and use_cache:
        logger.info("Loading techniques from local JSON file.")
        return load_json(TECH_PATH)
    else:
        logger.info("Retrieving all techniques from ATT&CK server")
        try:
            lift = attack_client()
            all_techniques = lift.get_techniques(enrich_data_sources=True)
            all_techniques = serialize_techniques(all_techniques)
            with open(TECH_PATH, 'w+') as json_file:
                json.dump(all_techniques, json_file)
            logger.info(f"Techniques saved to {TECH_PATH}")
            return all_techniques
        except Exception as e:
            logger.error(f"Could not download techniques from ATT&CK server: {str(e)}")
            exit(2)

def load_relationships(use_cache: bool) -> List[Dict[str, Any]]:
    """loading mitre relationships

    Args:
        use_cache (bool): if cache should not be used

    Returns:
        List[Dict[str, Any]]: mitre relationships as dictionary
    """
    if os.path.exists(RELATIONS_PATH) and use_cache:
        logger.info("Loading relationships from local JSON file.")
        return load_json(RELATIONS_PATH)
    else:
        logger.info("Retrieving all relationships from ATT&CK server")
        try:
            lift = attack_client()
            all_relationships = lift.get_relationships()
            all_relationships = serialize_relationships(all_relationships)
            with open(RELATIONS_PATH, 'w+') as json_file:
                json.dump(all_relationships, json_file)
            logger.info(f"Relationships saved to {RELATIONS_PATH}")
            return all_relationships
        except Exception as e:
            logger.error(f"Could not download relationships from ATT&CK server: {str(e)}")
            exit(2)

def load_groups(use_cache: bool) -> List[Dict[str, Any]]:
    """loading mitre groups

    Args:
        use_cache (bool): if cache should not be used

    Returns:
        List[Dict[str, Any]]: mitre groups as dictionary
    """
    if os.path.exists(GROUPS_PATH) and use_cache:
        logger.info("Loading groups from local JSON file.")
        return load_json(GROUPS_PATH)
    else:
        logger.info("Retrieving all groups from ATT&CK server")
        try:
            lift = attack_client()
            all_groups = lift.get_groups()
            all_groups = serialize_groups(all_groups)
            with open(GROUPS_PATH, 'w+') as json_file:
                json.dump(all_groups, json_file)
            logger.info(f"Groups saved to {GROUPS_PATH}")
            return all_groups
        except Exception as e:
            logger.error(f"Could not download groups from ATT&CK server: {str(e)}")
            exit(2)

def load_mitigations(use_cache: bool) -> List[Dict[str, Any]]:
    """loading mitre mitgations

    Args:
        use_cache (bool): if cache should not be used

    Returns:
        List[Dict[str, Any]]: mitre mitigations as dictionary
    """
    if os.path.exists(MIT_PATH) and use_cache:
        logger.info("Loading mitigations from local JSON file.")
        return load_json(MIT_PATH)
    else:
        logger.info("Retrieving all mitigations from ATT&CK server")
        try:
            lift = attack_client()
            all_mitigations = lift.get_mitigations()
            all_mitigations = serialize_mitigations(all_mitigations)
            with open(MIT_PATH, 'w+') as json_file:
                json.dump(all_mitigations, json_file)
            logger.info(f"Mitigations saved to {MIT_PATH}")
            return all_mitigations
        except Exception as e:
            logger.error(f"Could not download mitigations from ATT&CK server: {str(e)}")
            exit(2)


def load_all_data(use_cache: bool) -> Dict[str, Any]:
    """starting all load functions

    Args:
        use_cache (bool): if cache should not be used

    Returns:
        List[Dict[str, Any]]: object with all data
    """
    return {
        'techniques': load_techniques(use_cache),
        'relationships': load_relationships(use_cache),
        'groups': load_groups(use_cache),
        'mitigations': load_mitigations(use_cache)
    }

def serialize_techniques(techniques):
    """util function to serialize techniques

    Args:
        techniques (_type_): techniques to be serialized

    Returns:
        _type_: techniques as dictionary
    """
    serialized = []
    for t in techniques:
        serialized_t = json.loads(t.serialize())
        description = serialized_t.get('description')

        serialized.append({
            "type": serialized_t['type'],
            "id": serialized_t['id'],
            "technique_id": serialized_t['external_references'][0]['external_id'],
            "parent_id": serialized_t['external_references'][0]['external_id'].split('.')[0] if '.' in serialized_t['external_references'][0]['external_id'] else None,
            "external_references": serialized_t['external_references'],
            "kill_chain_phases": serialized_t['kill_chain_phases'],
            "name": serialized_t['name'],
            "description": description,
            "mitigations": [],
            "groups": [],
            "related_relationships": []
        })
    return serialized

def serialize_relationships(relationships):
    """util function to serialize relationships

    Args:
        relationships (_type_): relationships to be serialized

    Returns:
        _type_: relationships as dictionary
    """
    serialized = []
    for rel in relationships:
        serialized_rel = json.loads(rel.serialize())        
        description = serialized_rel.get('description')
            
        serialized.append({
            "type": serialized_rel['type'],
            "id": serialized_rel['id'],
            "relationship_type": serialized_rel['relationship_type'],
            "target_ref": serialized_rel['target_ref'],
            "description": description,
            "source_ref": serialized_rel['source_ref']
        })
    return serialized

def serialize_groups(groups):
    """util function to serialize groups

    Args:
        groups (_type_): groups to be serialized

    Returns:
        _type_: groups as dictionary
    """
    serialized = []
    for group in groups:
        serialized_grp = json.loads(group.serialize())        
        description = serialized_grp.get('description')
            
        serialized.append({
            "type": serialized_grp['type'],
            "id": serialized_grp['id'],
            "name": serialized_grp['name'],
            "aliases": serialized_grp['aliases'],
            "external_references": serialized_grp['external_references'],
            "description": description,
            "created_by_ref": serialized_grp['created_by_ref']
        })
    return serialized

def serialize_mitigations(mitigations):
    """util function to serialize mitgations

    Args:
        mitgations (_type_): mitgations to be serialized

    Returns:
        _type_: mitgations as dictionary
    """
    serialized = []
    for m in mitigations:
        serialized_m = json.loads(m.serialize())
        description = serialized_m.get('description')
        serialized.append({
            "type": serialized_m['type'],
            "id": serialized_m['id'],
            "mitigation_id": serialized_m['external_references'][0]["external_id"],
            "name": serialized_m['name'],
            "description": description,
            "created_by_ref": serialized_m['created_by_ref'],
            "object_marking_refs": serialized_m['object_marking_refs']
        })
    return serialized