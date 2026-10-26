"""
Central configuration for Vouch campuses.

To add a new campus:
1. Add a (code, display_name) tuple to CAMPUSES.
2. Add the required distance entries to CAMPUS_DISTANCES_KM in shipping.py.
3. Update any campus-specific business rules or tests if necessary.

Campus codes are stored in Customer.campus and used by shipping.py.
They must remain consistent across the application.

Display names are shown in dropdowns and other full-name UI elements.
Pill labels are used for compact UI elements.
"""


# =========================================================
# CAMPUS DEFINITIONS
# =========================================================

CAMPUSES = [
    ("GCTU", "Ghana Communication Technology University (GCTU)"),
    ("Legon", "University of Ghana (Legon)"),
    ("KNUST", "KNUST"),
    ("UCC", "University of Cape Coast (UCC)"),
    ("UEW", "University of Education, Winneba (UEW)"),
    ("GIMPA", "Ghana Institute of Management and Public Administration (GIMPA)"),
    ('Central', 'Central University (Central)'),
]


# =========================================================
# DERIVED CAMPUS DATA
# =========================================================

# List of supported campus codes.
CAMPUS_CODES = [
    code for code, display_name in CAMPUSES
]

# Maps each campus code to its full display name.
CAMPUS_DISPLAY_NAMES = {
    code: display_name
    for code, display_name in CAMPUSES
}


# =========================================================
# COMPACT UI LABELS
# =========================================================

# Short labels for homepage pills and compact UI elements.
CAMPUS_PILL_LABELS = {
    "GCTU": "GCTU",
    "Legon": "Legon",
    "KNUST": "KNUST",
    "UCC": "UCC",
    "UEW": "UEW",
    "GIMPA": "GIMPA",
    "CENTRAL": "CENTRAL",
}


# =========================================================
# CONFIGURATION VALIDATION
# =========================================================

def validate_campuses():
    """
    Check campus definitions for duplicate codes and invalid values.

    Raises ValueError if the configuration is invalid.
    """

    codes = [code for code, display_name in CAMPUSES]

    if len(codes) != len(set(codes)):
        raise ValueError(
            "Duplicate campus codes found in CAMPUSES."
        )

    for code, display_name in CAMPUSES:

        if not isinstance(code, str) or not code.strip():
            raise ValueError(
                "Every campus must have a non-empty string code."
            )

        if not isinstance(display_name, str) or not display_name.strip():
            raise ValueError(
                f"Campus {code!r} must have a non-empty display name."
            )

    if len(CAMPUS_CODES) != len(CAMPUS_DISPLAY_NAMES):
        raise ValueError(
            "Campus codes and display names are inconsistent."
        )


# Validate the configuration when this module is imported.
validate_campuses()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_campus_display_name(campus_code):
    """
    Return the full display name for a campus code.

    Unknown codes are returned unchanged.
    None returns an empty string.
    """

    if campus_code is None:
        return ""

    return CAMPUS_DISPLAY_NAMES.get(
        campus_code,
        campus_code
    )


def get_campus_pill_label(campus_code):
    """
    Return the compact label for a campus code.

    Unknown codes are returned unchanged.
    None returns an empty string.
    """

    if campus_code is None:
        return ""

    return CAMPUS_PILL_LABELS.get(
        campus_code,
        campus_code
    )


def is_valid_campus(campus_code):
    """
    Return True if the campus code is supported.
    """

    return (
        isinstance(campus_code, str)
        and campus_code in CAMPUS_CODES
    )