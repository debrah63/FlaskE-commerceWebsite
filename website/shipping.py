"""
Vouch shipping configuration and fee calculation.

Campus codes must match those defined in website/campuses.py.
"""

from itertools import combinations

from website.campuses import CAMPUS_CODES


# =========================================================
# CAMPUS DISTANCES
# =========================================================

# Estimated distances between campus pairs, in kilometres.
# frozenset allows routes to be looked up in either direction.

CAMPUS_DISTANCES_KM = {
    frozenset(("Legon", "KNUST")): 250,
    frozenset(("Legon", "UCC")): 165,
    frozenset(("Legon", "UEW")): 140,
    frozenset(("Legon", "GIMPA")): 15,
    frozenset(("Legon", "GCTU")): 20,

    frozenset(("KNUST", "UCC")): 280,
    frozenset(("KNUST", "UEW")): 220,
    frozenset(("KNUST", "GIMPA")): 260,
    frozenset(("KNUST", "GCTU")): 255,

    frozenset(("UCC", "UEW")): 60,
    frozenset(("UCC", "GIMPA")): 155,
    frozenset(("UCC", "GCTU")): 150,

    frozenset(("UEW", "GIMPA")): 130,
    frozenset(("UEW", "GCTU")): 125,

    frozenset(("GIMPA", "GCTU")): 10,

    frozenset(("Central", "GCTU")): 25,
    frozenset(("Central", "Legon")): 15,
    frozenset(("Central", "KNUST")): 20,
    frozenset(("Central", "UCC")): 20,
    frozenset(("Central", "UEW")): 20,
    frozenset(("Central", "GIMPA")): 20,


}


# =========================================================
# SHIPPING ZONES AND FEES
# =========================================================

ZONE_BOUNDARIES = [
    (0, 1),
    (1, 50),
    (50, 150),
    (150, float("inf")),
]

ZONE_FEES = {
    1: 10.0,
    2: 15.0,
    3: 22.0,
    4: 30.0,
}

UNKNOWN_ROUTE_FEE = 50.0


# =========================================================
# CAMPUS VALIDATION
# =========================================================

def is_valid_campus(campus_code):
    """Return True if the campus code is supported by Vouch."""

    return (
        isinstance(campus_code, str)
        and campus_code in CAMPUS_CODES
    )


# =========================================================
# ROUTE VALIDATION
# =========================================================

def is_route_configured(origin, destination):
    """Check whether a campus pair has a configured shipping route."""

    if not is_valid_campus(origin):
        return False

    if not is_valid_campus(destination):
        return False

    if origin == destination:
        return True

    return frozenset((origin, destination)) in CAMPUS_DISTANCES_KM


def validate_shipping_routes():
    """
    Check that every distinct campus pair has a configured distance.

    Raises ValueError if a route is missing or invalid.
    """

    expected_routes = {
        frozenset(pair)
        for pair in combinations(CAMPUS_CODES, 2)
    }

    configured_routes = set(CAMPUS_DISTANCES_KM)

    missing_routes = expected_routes - configured_routes
    extra_routes = configured_routes - expected_routes

    if missing_routes:
        raise ValueError(
            f"Missing shipping distances for routes: {missing_routes}"
        )

    if extra_routes:
        raise ValueError(
            f"Invalid shipping routes found: {extra_routes}"
        )

    for route, distance in CAMPUS_DISTANCES_KM.items():

        if len(route) != 2:
            raise ValueError(
                f"Invalid campus pair: {route}"
            )

        if (
            isinstance(distance, bool)
            or not isinstance(distance, (int, float))
            or distance <= 0
        ):
            raise ValueError(
                f"Invalid distance for {route}: {distance}"
            )


# =========================================================
# SHIPPING ZONE CALCULATION
# =========================================================

def get_zone(distance_km):
    """Return the shipping zone corresponding to a distance."""

    if (
        isinstance(distance_km, bool)
        or not isinstance(distance_km, (int, float))
    ):
        raise ValueError("Distance must be a number.")

    if distance_km < 0:
        raise ValueError("Distance cannot be negative.")

    if distance_km <= 1:
        return 1

    for zone, (low, high) in enumerate(
        ZONE_BOUNDARIES,
        start=1,
    ):
        if low < distance_km <= high:
            return zone

    return 4
# =========================================================
# SHIPPING FEE CALCULATION
# =========================================================

def shipping_fee(origin, destination):
    """
    Calculate the shipping fee between two campuses.

    Returns:
        fee: Shipping fee, or None for an invalid campus.
        zone: Shipping zone, if applicable.
        distance_km: Configured distance, if available.
        label: Description of the route.
        configured: Whether the route has a configured distance.
    """

    if not is_valid_campus(origin):
        return {
            "fee": None,
            "zone": None,
            "distance_km": None,
            "label": "Invalid origin campus",
            "configured": False,
        }

    if not is_valid_campus(destination):
        return {
            "fee": None,
            "zone": None,
            "distance_km": None,
            "label": "Invalid destination campus",
            "configured": False,
        }

    # Same-campus deliveries retain the existing Zone 1 fee.
    if origin == destination:
        return {
            "fee": ZONE_FEES[1],
            "zone": 1,
            "distance_km": 0,
            "label": "Same campus",
            "configured": True,
        }

    route = frozenset((origin, destination))
    distance = CAMPUS_DISTANCES_KM.get(route)

    # Preserve the existing fallback fee for valid but
    # unconfigured campus pairs.
    if distance is None:
        return {
            "fee": UNKNOWN_ROUTE_FEE,
            "zone": None,
            "distance_km": None,
            "label": "Custom route",
            "configured": False,
        }

    zone = get_zone(distance)

    return {
        "fee": ZONE_FEES[zone],
        "zone": zone,
        "distance_km": distance,
        "label": f"Zone {zone}",
        "configured": True,
    }


# =========================================================
# INITIAL CONFIGURATION VALIDATION
# =========================================================

validate_shipping_routes()