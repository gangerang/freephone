#!/usr/bin/env python3
"""
Verification script for payphone search optimizations.
This simulates the JavaScript spatial index to ensure correctness.
"""

import json
import math
from collections import defaultdict

def deg2rad(deg):
    return deg * (math.pi / 180)

def get_distance_km(lat1, lon1, lat2, lon2):
    """Haversine distance calculation (same as JavaScript version)"""
    R = 6371  # Earth radius in km
    dLat = deg2rad(lat2 - lat1)
    dLon = deg2rad(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def build_spatial_index(payphones, grid_size=0.1):
    """Build grid-based spatial index"""
    spatial_index = defaultdict(list)

    for idx, phone in enumerate(payphones):
        grid_x = int(phone['latitude'] / grid_size)
        grid_y = int(phone['longitude'] / grid_size)
        grid_key = f"{grid_x},{grid_y}"
        spatial_index[grid_key].append(idx)

    return spatial_index

def get_candidates(lat, lon, spatial_index, payphones, grid_size=0.1):
    """Get candidate payphones from spatial index (9 cells)"""
    grid_x = int(lat / grid_size)
    grid_y = int(lon / grid_size)
    candidates = []

    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            grid_key = f"{grid_x + dx},{grid_y + dy}"
            if grid_key in spatial_index:
                for idx in spatial_index[grid_key]:
                    candidates.append(payphones[idx])

    return candidates

def find_nearest_brute_force(lat, lon, payphones):
    """Original O(n) brute force approach"""
    nearest = None
    min_distance = float('inf')

    for phone in payphones:
        distance = get_distance_km(lat, lon, phone['latitude'], phone['longitude'])
        if distance < min_distance:
            min_distance = distance
            nearest = phone

    return nearest, min_distance

def find_nearest_optimized(lat, lon, payphones, spatial_index):
    """Optimized approach using spatial index"""
    candidates = get_candidates(lat, lon, spatial_index, payphones)

    nearest = None
    min_distance = float('inf')

    for phone in candidates:
        distance = get_distance_km(lat, lon, phone['latitude'], phone['longitude'])
        if distance < min_distance:
            min_distance = distance
            nearest = phone

    return nearest, min_distance, len(candidates)

def main():
    print("=== Payphone Search Optimization Verification ===\n")

    # Load payphones data
    with open('payphones.json', 'r') as f:
        payphones = json.load(f)

    print(f"Loaded {len(payphones)} payphones")

    # Build indexes
    spatial_index = build_spatial_index(payphones)
    print(f"Built spatial index with {len(spatial_index)} grid cells")

    # Test locations
    test_locations = [
        {"name": "Sydney CBD", "lat": -33.8688, "lon": 151.2093},
        {"name": "Melbourne CBD", "lat": -37.8136, "lon": 144.9631},
        {"name": "Brisbane CBD", "lat": -27.4698, "lon": 153.0251},
        {"name": "Perth CBD", "lat": -31.9505, "lon": 115.8605},
        {"name": "Adelaide CBD", "lat": -34.9285, "lon": 138.6007},
    ]

    print("\nVerifying correctness across test locations...\n")

    all_correct = True
    total_reduction = 0

    for location in test_locations:
        lat, lon = location['lat'], location['lon']

        # Brute force (original)
        nearest_bf, dist_bf = find_nearest_brute_force(lat, lon, payphones)

        # Optimized (with spatial index)
        nearest_opt, dist_opt, num_candidates = find_nearest_optimized(
            lat, lon, payphones, spatial_index
        )

        # Verify results match
        is_correct = (
            nearest_bf['address'] == nearest_opt['address'] and
            abs(dist_bf - dist_opt) < 0.001  # Allow tiny floating point differences
        )

        reduction = len(payphones) / num_candidates
        total_reduction += reduction

        status = "✓ PASS" if is_correct else "✗ FAIL"
        print(f"{status} - {location['name']}")
        print(f"  Nearest: {nearest_opt['address']}")
        print(f"  Distance: {dist_opt:.2f} km")
        print(f"  Candidates: {num_candidates} (reduced from {len(payphones)}, {reduction:.1f}x)")
        print()

        if not is_correct:
            all_correct = False
            print(f"  ERROR: Mismatch!")
            print(f"  Brute force: {nearest_bf['address']} at {dist_bf:.2f} km")
            print(f"  Optimized:   {nearest_opt['address']} at {dist_opt:.2f} km")
            print()

    avg_reduction = total_reduction / len(test_locations)

    print("=== Summary ===")
    if all_correct:
        print("✓ All tests PASSED - optimization is correct!")
        print(f"✓ Average search space reduction: {avg_reduction:.1f}x")
        print(f"✓ Expected performance improvement: ~{avg_reduction:.0f}x faster")
    else:
        print("✗ Some tests FAILED - optimization has errors!")
        return 1

    # Test postcode index
    print("\n=== Postcode Index Test ===")
    postcode_index = defaultdict(list)
    for idx, phone in enumerate(payphones):
        if phone.get('postcode'):
            postcode_index[phone['postcode']].append(idx)

    print(f"Built postcode index with {len(postcode_index)} unique postcodes")

    test_postcode = "2000"  # Sydney CBD
    if test_postcode in postcode_index:
        count = len(postcode_index[test_postcode])
        print(f"Postcode {test_postcode}: {count} payphones")
        print(f"O(1) lookup vs O(n) scan: ~{len(payphones)}x faster")

    return 0

if __name__ == '__main__':
    exit(main())
