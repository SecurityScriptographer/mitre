from typing import Dict, Any, List, Tuple
import logging
import json
import os
from statistics import mean, quantiles
import colorsys

logger = logging.getLogger(__name__)

def analyze_and_update_techniques(techniques: List[Dict[str, Any]], all_techniques_length: int) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Extracting statistics for techniques and updating them with counts
    
    Args:
        techniques (List[Dict[str, Any]]): all mapped techniques
        all_techniques_length (int): length of all techniques
        
    Returns:
        tuple[Dict[str, Any], List[Dict[str, Any]]]: overall stats and all mapped techniques with statistics
    """
    total_techniques = len(techniques)
    
    # Calculate counts for each technique
    for technique in techniques:
        technique['stats'] = {
            'groups_count': len(technique.get('groups', [])),
            'mitigations_count': len(technique.get('mitigations', []))
        }
    
    # Helper function to get top 5 techniques for a specific count type
    def get_top_5(techniques, count_type):
        return sorted(
            techniques,
            key=lambda t: t['stats'][count_type],
            reverse=True
        )[:5]
    
    # Get top 5 for each category
    top_5_groups = [
        {
            'id': t['technique_id'],
            'name': t['name'],
            'count': t['stats']['groups_count']
        }
        for t in get_top_5(techniques, 'groups_count')
    ]
    
    top_5_mitigations = [
        {
            'id': t['technique_id'],
            'name': t['name'],
            'count': t['stats']['mitigations_count']
        }
        for t in get_top_5(techniques, 'mitigations_count')
    ]
    
    # Find techniques with maximum counts
    max_groups_technique = max(techniques, key=lambda t: t['stats']['groups_count'])
    max_mitigations_technique = max(techniques, key=lambda t: t['stats']['mitigations_count'])

    # Helper function to safely calculate average
    def safe_average(values, total):
        try:
            return sum(values) / total if total > 0 else 0
        except (TypeError, ValueError):
            return 0
    
    # Calculate overall statistics
    overall_stats = {
        "all_techniques": all_techniques_length,
        'total_used_techniques': total_techniques,
        'total_groups': sum(t['stats']['groups_count'] for t in techniques),
        'total_mitigations': sum(t['stats']['mitigations_count'] for t in techniques),
        'avg_groups_per_technique': safe_average([t['stats']['groups_count'] for t in techniques], total_techniques),
        'avg_mitigations_per_technique': safe_average([t['stats']['mitigations_count'] for t in techniques], total_techniques),
        'most_targeted_technique': {
            'id': max_groups_technique['technique_id'],
            'name': max_groups_technique['name'],
            'groups_count': max_groups_technique['stats']['groups_count']
        },
        'most_mitigated_technique': {
            'id': max_mitigations_technique['technique_id'],
            'name': max_mitigations_technique['name'],
            'mitigations_count': max_mitigations_technique['stats']['mitigations_count']
        },
        # Add top 5 rankings
        'top_5_by_groups': top_5_groups,
        'top_5_by_mitigations': top_5_mitigations
    }
    
    return overall_stats, techniques

def find_color_for_count(colors: Dict[str, Dict[str, str]], count: int) -> str:
    """Utility function to find color for a specific count
    
    Args:
        colors (Dict[str, Dict[str, str]]): all colors
        count (int): count to find color for
        
    Returns:
        str: color for that specific count
    """
    keys = sorted(int(key) for key in colors if key.isdigit())
    
    selected_key = None
    for key in keys:
        if key <= count:
            selected_key = key
        else:
            break
            
    if selected_key is None or count > max(keys):
        selected_key = 'more'
    
    return colors[str(selected_key)]['color']

def generate_color_gradient(start_hex: str, end_hex: str, steps: int) -> List[str]:
    """Generate a gradient between two hex colors
    
    Args:
        start_hex (str): Starting hex color (e.g., '#ffffff')
        end_hex (str): Ending hex color (e.g., '#ff0000')
        steps (int): Number of colors to generate
        
    Returns:
        List[str]: List of hex colors forming a gradient
    """
    def hex_to_hsv(hex_color: str) -> Tuple[float, float, float]:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    
    def hsv_to_hex(hsv: Tuple[float, float, float]) -> str:
        rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
        return '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
    
    start_hsv = hex_to_hsv(start_hex)
    end_hsv = hex_to_hsv(end_hex)
    
    gradient = []
    for i in range(steps):
        ratio = i / (steps - 1)
        hsv = tuple(
            start + (end - start) * ratio
            for start, end in zip(start_hsv, end_hsv)
        )
        gradient.append(hsv_to_hex(hsv))
    
    return gradient

def calculate_color_thresholds(techniques: List[Dict[str, Any]], count_type: str) -> Dict[str, Dict[str, str]]:
    """Calculate dynamic color thresholds based on data distribution
    
    Args:
        techniques (List[Dict[str, Any]]): List of techniques with stats
        count_type (str): Type of count to analyze ('groups' or 'mitigations')
        
    Returns:
        Dict[str, Dict[str, str]]: Color mapping dictionary
    """
    valid_count_types = ['groups', 'mitigations']
    if count_type not in valid_count_types:
        logger.warning(f"Invalid count_type: {count_type}. Using default color scheme.")
        return default_color_scheme()
    
    counts = [tech['stats'].get(f'{count_type}_count', 0) for tech in techniques]
    
    if not counts:
        return default_color_scheme()
    
    max_count = max(counts)
    if max_count == 0:
        return default_color_scheme()
    
    try:
        quarts = quantiles(counts, n=4)
        thresholds = sorted(list(set([
            0,
            round(quarts[0]),
            round(mean(counts)),
            round(quarts[2]),
            round(max_count * 0.9),
            max_count
        ])))
    except Exception as e:
        logger.warning(f"Error calculating thresholds: {e}. Using default scheme.")
        return default_color_scheme()
    
    colors = generate_color_gradient('#ffffff', '#000066', len(thresholds) + 1)
    
    color_map = {
        str(threshold): {"color": color}
        for threshold, color in zip(thresholds, colors)
    }
    color_map["more"] = {"color": colors[-1]}
    
    return color_map

def default_color_scheme() -> Dict[str, Dict[str, str]]:
    """Return the default color scheme
    
    Returns:
        Dict[str, Dict[str, str]]: Default color mapping
    """
    return {
        "0": {"color": "#ffffff"},  # White
        "1": {"color": "#ff6666"},  # Light red
        "2": {"color": "#f94444"},  # Moderate red
        "4": {"color": "#e41b1b"},  # Strong red
        "6": {"color": "#f10000"},  # Very strong red
        "11": {"color": "#950000"},  # Deep red
        "more": {"color": "#2b0000"}  # Very deep red
    }

def create_navigator_layer(techniques: List[Dict[str, Any]], layer_name: str, count_type: str, hide_uncovered=True) -> Dict[str, Any]:
    """Creates a MITRE ATT&CK Navigator layer for visualization
    
    Args:
        techniques (List[Dict[str, Any]]): techniques with statistics
        layer_name (str): name for the layer
        count_type (str): type of count to visualize ('groups' or 'mitigations')
        hide_uncovered (bool): whether to hide techniques with count=0
        
    Returns:
        Dict[str, Any]: Navigator layer data structure
    """
    colors = calculate_color_thresholds(techniques, count_type)
    
    result_data = {
        "description": f"Enterprise techniques heat map showing {count_type} count",
        "name": layer_name,
        "domain": "enterprise-attack",
        "versions": {
            "attack": "16",
            "navigator": "5.0.0",
            "layer": "4.5"
        },
        "gradient": {
            "colors": [],
            "minValue": 0,
            "maxValue": 1
        },
        "legendItems": [],
        "techniques": [],
        "showTacticRowBackground": True,
        "tacticRowBackground": "#dddddd",
        "selectTechniquesAcrossTactics": True,
        "selectSubtechniquesWithParent": True,
        "selectVisibleTechniques": False,
        "layout": {
            "layout": "flat",
            "showName": True,
            "showID": False,
            "expandedSubtechniques": True
        },
        "hideDisabled": True
    }
    
    for technique in techniques:
        if not technique.get("technique_id"):
            logger.debug(f"Could not find technique_id for {technique.get('name', 'Unknown')}")
            continue
            
        count = technique['stats'].get(f'{count_type}_count', 0)
        comment = f"{count} {count_type}"
        color = find_color_for_count(colors, count)
        
        technique_entry = {
            "techniqueID": technique["technique_id"],
            "color": color,
            "comment": comment,
            "showSubtechniques": True,
            "enabled": not hide_uncovered or count > 0,
        }
        result_data["techniques"].append(technique_entry)
    
    result_data["gradient"]["colors"] = [v['color'] for v in colors.values()]
    result_data["legendItems"] = [
        {
            "label": "More" if k == "more" else str(k),
            "color": v['color']
        } for k, v in colors.items()
    ]
    
    return result_data

def save_navigator_layers(analysis_results: Dict[str, Any], output_dir: str, hide_uncovered=True) -> None:
    """Saves the navigator layers as separate JSON files
    
    Args:
        analysis_results (Dict[str, Any]): Results from analyze_data containing visualization layers
        output_dir (str): Directory to save the layer files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    layer_types = {
        'groups': 'Groups Heat Map',
        'mitigations': 'Mitigations Heat Map'
    }
    
    for layer_type, layer_name in layer_types.items():
        layer = create_navigator_layer(
            analysis_results['techniques'],
            layer_name,
            layer_type,
            hide_uncovered=hide_uncovered
        )
        
        output_path = os.path.join(output_dir, f'{layer_type}_layer.json')
        with open(output_path, 'w') as f:
            json.dump(layer, f, indent=2)
        logger.info(f"Saved {layer_type} layer to {output_path}")

def analyze_data(techniques: List[Dict[str, Any]], all_techniques_length: int, output_dir: str = "navigator_layers", hide_uncovered=True) -> Dict[str, Any]:
    """Main analysis function that processes techniques and creates visualization layers
    
    Args:
        techniques (List[Dict[str, Any]]): all techniques to analyze
        all_techniques_length (int): total number of techniques
        output_dir (str): directory to save navigator layer files
        
    Returns:
        Dict[str, Any]: analysis results including stats
    """
    overall_stats, updated_techniques = analyze_and_update_techniques(techniques, all_techniques_length)
    
    save_navigator_layers({'techniques': updated_techniques}, output_dir)
    
    return {
        "overall_stats": overall_stats,
        "techniques": updated_techniques
    }