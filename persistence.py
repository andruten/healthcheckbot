import json
from typing import List, Dict


def read_services(filename='data/services.json') -> List[Dict]:
    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        return []
