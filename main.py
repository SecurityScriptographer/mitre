import logging
from config import FULL_PATH, setup_logging
from loader import load_all_data
from mapper import map_all_data
from analyzer import analyze_data
from optimizer import save_optimized_data

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
    
    # Save the optimized mapped data
    save_optimized_data(mapped_techniques, FULL_PATH)
    
    logger.info("Statistics for techniques:")
    for key, value in analysis_results['overall_stats'].items():
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        logger.info(f"  {key}: {formatted_value}")