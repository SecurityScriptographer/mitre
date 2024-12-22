import logging
import json
from config import FULL_PATH, setup_logging
from loader import load_all_data
from mapper import map_all_data
from analyzer import analyze_data

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Set up logging
    setup_logging()
    logging.getLogger().setLevel(logging.INFO)
    
    # Load all data including the attack object
    data = load_all_data()
    
    logger.info(f"Loaded {len(data['techniques'])} techniques")
    logger.info(f"Loaded {len(data['groups'])} groups")
    logger.info(f"Loaded {len(data['mitigations'])} mitigations")
    
    # Map relationships between objects
    logger.info("Mapping relationships")
    mapped_techniques = map_all_data(data)
    logger.info("Finished mapping all data")
    
    # Run analysis
    analysis_results = analyze_data(
        mapped_techniques,
        len(data['techniques']),
        output_dir="navigator_layers",
        hide_uncovered=True
    )
    
    # Save the mapped data
    with open(FULL_PATH, 'w+') as json_file:
        json_data = {
            'techniques': mapped_techniques
        }
        json.dump(json_data, json_file)
    
    logger.info("Statistics for techniques:")
    for key, value in analysis_results['overall_stats'].items():
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        logger.info(f"  {key}: {formatted_value}")