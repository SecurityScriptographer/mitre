import os
import logging

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
RES_DIR = os.path.join(BASE_DIR, '..', 'resources')

# Ensure directories exist
for directory in [CACHE_DIR]:
    os.makedirs(directory, exist_ok=True)

# Cache File paths
TECH_PATH = os.path.join(CACHE_DIR, 'all_techniques.json')
RELATIONS_PATH = os.path.join(CACHE_DIR, 'all_relationships.json')
GROUPS_PATH = os.path.join(CACHE_DIR, 'all_groups.json')
MIT_PATH = os.path.join(CACHE_DIR, 'all_mitigations.json')
FULL_PATH = os.path.join(CACHE_DIR, 'full.json')

def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    # Suppress TAXII warnings by setting its logger to ERROR level
    logging.getLogger('taxii2client.v20').setLevel(logging.ERROR)