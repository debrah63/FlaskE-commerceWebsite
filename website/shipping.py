CAMPUS_DISTANCES_KM = {
    frozenset(['Legon', 'KNUST']): 250,
    frozenset(['Legon', 'UCC']): 165,
    frozenset(['Legon', 'UEW']): 140,
    frozenset(['Legon', 'GIMPA']): 15,
    frozenset(['Legon', 'GCTU']): 20,
    frozenset(['KNUST', 'UCC']): 280,
    frozenset(['KNUST', 'UEW']): 220,
    frozenset(['KNUST', 'GIMPA']): 260,
    frozenset(['KNUST', 'GCTU']): 255,
    frozenset(['UCC', 'UEW']): 60,
    frozenset(['UCC', 'GIMPA']): 155,
    frozenset(['UCC', 'GCTU']): 150,
    frozenset(['UEW', 'GIMPA']): 130,
    frozenset(['UEW', 'GCTU']): 125,
    frozenset(['GIMPA', 'GCTU']): 10,
}

ZONE_BOUNDARIES = [(0, 1), (1, 50), (50, 150), (150, float('inf'))]
ZONE_FEES = {1: 10.0, 2: 15.0, 3: 22.0, 4: 30.0}
UNKNOWN_ROUTE_FEE = 25.0


def get_zone(distance_km):
    if distance_km <= 0:
        return 1
    for zone, (low, high) in enumerate(ZONE_BOUNDARIES, start=1):
        if low < distance_km <= high:
            return zone
    return 4


def shipping_fee(origin, destination):
    if not origin or not destination:
        return {'fee': UNKNOWN_ROUTE_FEE, 'zone': None, 'distance_km': None, 'label': 'Unknown route'}

    if origin == destination:
        return {'fee': ZONE_FEES[1], 'zone': 1, 'distance_km': 0, 'label': 'Same campus'}

    distance = CAMPUS_DISTANCES_KM.get(frozenset([origin, destination]))

    if distance is None:
        return {'fee': UNKNOWN_ROUTE_FEE, 'zone': None, 'distance_km': None, 'label': 'Custom route'}

    zone = get_zone(distance)
    return {'fee': ZONE_FEES[zone], 'zone': zone, 'distance_km': distance, 'label': f'Zone {zone}'}