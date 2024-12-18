import logging
import json
from config import FULL_PATH, setup_logging
from loader import load_all_data
from mapper import map_all_data
from analyzer import analyze_data

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    setup_logging()
    
    data = load_all_data(use_cache=True)

    logger.info(f"Loaded {len(data['techniques'])} techniques")
    logger.info(f"Loaded {len(data['relationships'])} relationships")
    logger.info(f"Loaded {len(data['groups'])} groups")
    logger.info(f"Loaded {len(data['mitigations'])} mitigations")
    
    
    logger.info(f"Map data")
    mapped_data = map_all_data(data=data)
    logger.info(f"Mapped all data")
    
    with open(FULL_PATH, 'w+') as json_file:
        json.dump(mapped_data, json_file)
        
    analysis_results = analyze_data(
        mapped_data, 
        len(data['techniques']),
        output_dir="navigator_layers",
        hide_uncovered=True
    )
    
    logger.info("Statistics for techniques:")
    for key, value in analysis_results['overall_stats'].items():
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        logger.info(f"  {key}: {formatted_value}")