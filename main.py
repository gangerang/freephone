import requests
import csv
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# API endpoint
url = 'https://tapi.telstra.com/presentation/v1/tcom/geo/payphones/list'

# Headers to mimic a browser request
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Origin': 'https://www.telstra.com.au',
    'Referer': 'https://www.telstra.com.au/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'source': 'tcom'
}

# Search points
SEARCH_POINTS = {
    "JUNEE": {"lat": -34.8709308, "lon": 147.5847095},
    "MACKAY": {"lat": -21.1690168, "lon": 149.0108144},
    "ALICE": {"lat": -23.6993435, "lon": 133.8749801},
    "PERTH": {"lat": -32.0390554, "lon": 115.6318991}
}

REQUEST_SIZE = 100  # any bigger than 100 just defaults to 5
MAX_FROM = 9000     # 9000 seemed to be about the biggest that would work
LARGE_RADIUS = 1000000000000000  # Defining a named constant for clarity and adjustability

def fetch_data(point, from_record):
    """Function to fetch data using pagination."""
    payload = {
        "point": point,
        "radius": LARGE_RADIUS,
        "pagination": {"size": 100, "from": from_record}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        print(f"Request for records starting from {from_record} for point {point} was successful.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data for records starting from {from_record} at point {point}: {e}")
        return None

def process_data(data, records):
    """Process data and add to the records set."""
    if data and 'results' in data and len(data['results']) > 0:
        results = data['results'][0]['value']
        for result in results:
            for feature in result['featureList']:
                record = (
                    feature['latitude'],
                    feature['longitude'],
                    feature['address'],
                    feature['state'],
                    str(feature['postcode']),
                    feature['phone_attributes'],
                    feature['cabinet_id'],
                    feature['fnn'],
                    feature['cli'],
                    feature['type'],
                    feature['icon']
                )
                records.add(record)

def write_json(records, output_filename):
    """Write all data to a JSON file."""
    json_records = [
        {
            "latitude": record[0],
            "longitude": record[1],
            "address": record[2],
            "state": record[3],
            "postcode": str(record[4]),
            "number": record[8]
        }
        for record in records
    ]

    with open(output_filename, 'w') as json_file:
        json.dump(json_records, json_file, indent=4)

    print(f"All data written to {output_filename}.")

def write_geojson(records, output_filename):
    """Write all data to a GeoJSON file."""
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(record[1]), float(record[0])]
                },
                "properties": {
                    "address": record[2],
                    "state": record[3],
                    "postcode": str(record[4]),
                    "number": record[8]
                }
            }
            for record in records
        ]
    }

    with open(output_filename, 'w') as geojson_file:
        json.dump(geojson, geojson_file, indent=4)

    print(f"All data written to {output_filename}.")

def write_nsw_json(records, output_filename):
    """Write NSW filtered data to a JSON file."""
    nsw_records = [
        {
            "latitude": record[0],
            "longitude": record[1],
            "address": record[2],
            "postcode": record[4],
            "number": record[8]
        }
        for record in records if record[3] == 'NSW'
    ]

    with open(output_filename, 'w') as json_file:
        json.dump(nsw_records, json_file, indent=4)

    print(f"NSW data written to {output_filename}.")

def write_nsw_geojson(records, output_filename):
    """Write NSW filtered data to a GeoJSON file."""
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(record[1]), float(record[0])]
                },
                "properties": {
                    "address": record[2],
                    "postcode": str(record[4]),
                    "number": record[8]
                }
            }
            for record in records if record[3] == 'NSW'
        ]
    }

    with open(output_filename, 'w') as geojson_file:
        json.dump(geojson, geojson_file, indent=4)

    print(f"NSW GeoJSON data written to {output_filename}.")

def process_region(region_name, point, records):
    """Process a single region in parallel."""
    print(f"Processing region: {region_name}")
    for from_record in range(0, MAX_FROM, REQUEST_SIZE):  # up to 9000 with steps of 100
        data = fetch_data(point, from_record)
        if data:
            process_data(data, records)
        print(f"Processed batch starting from record {from_record} for region {region_name}")

def main():
    records = set()

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_region, region_name, point, records)
            for region_name, point in SEARCH_POINTS.items()
        ]

        # Wait for all futures to complete
        for future in futures:
            future.result()

    # Generate timestamped filenames
    csv_output_filename = f'payphones_data.csv'
    json_output_filename = f'payphones_data.json'
    geojson_output_filename = f'payphones_data.geojson'
    nsw_json_output_filename = f'payphones_data_nsw.json'
    nsw_geojson_output_filename = f'payphones_data_nsw.geojson'

    # Write JSON and GeoJSON
    write_json(records, json_output_filename)
    write_geojson(records, geojson_output_filename)

    # Write NSW JSON and GeoJSON
    write_nsw_json(records, nsw_json_output_filename)
    write_nsw_geojson(records, nsw_geojson_output_filename)

if __name__ == '__main__':
    main()
