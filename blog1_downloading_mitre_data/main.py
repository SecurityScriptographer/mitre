import logging
import json
from config import FULL_PATH, setup_logging
from loader import load_all_data

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    setup_logging()
    
    data = load_all_data(use_cache=False)
    with open(FULL_PATH, 'w+') as json_file:
        json.dump(data, json_file)
    logger.info(f"Loaded {len(data['techniques'])} techniques")
    logger.info(f"Loaded {len(data['relationships'])} relationships")
    logger.info(f"Loaded {len(data['groups'])} groups")
    logger.info(f"Loaded {len(data['mitigations'])} mitigations")