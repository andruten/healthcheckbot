import json
from typing import List, Dict


def read_services(filename='data/services.json') -> List[Dict]:
    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        with open(filename, '+w') as f:
            f.write('[]')
        return []


def add_service(service_data: Dict, filename: str = 'data/services.json') -> None:
    services_data = read_services(filename)
    services_data.append(service_data)
    with open(filename, '+w') as f:
        f.write(json.dumps(services_data))


def remove_service(name: str, filename: str = 'data/services.json') -> None:
    services_data = [service_data for service_data in read_services(filename) if service_data['name'] != name]
    with open(filename, '+w') as f:
        f.write(json.dumps(services_data))
