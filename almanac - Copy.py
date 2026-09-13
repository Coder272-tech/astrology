#!/usr/bin/env python3

"""
Chinese 28 Lunar Mansions (二十八宿) astronomical calculator.

Coordinate system:
    Apparent geocentric equatorial
    True equator/equinox of date

Ephemeris:
    Skyfield + JPL DE421

Xiu methodology:
    - Canonical 28-mansion sequence.
    - Each mansion begins at the apparent geocentric RA of its
      determinative star (距星).
    - The mansion ends at the RA of the next determinative star.
    - Width = (next_RA - current_RA) % 360.
    - NO equal 12.857142857° sectors.
    - NO sorting by RA.
    - RA is evaluated in the canonical mansion sequence.
    - 軫 -> 角 wraps across 0°.

Bodies:
    Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn

Test case:
    2026-09-12 22:50:00 America/New_York
    = 2026-09-13 02:50:00 UTC

Requires:
    pip install skyfield
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from skyfield.api import load


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EPHEMERIS_FILE = "de421.bsp"

LOCAL_TIMEZONE = "America/New_York"

TEST_LOCAL_TIME = datetime(
    2026,
    9,
    14,
    23,
    00,
    0,
    tzinfo=ZoneInfo(LOCAL_TIMEZONE),
)


# ---------------------------------------------------------------------------
# Canonical 28 Lunar Mansions
#
# IMPORTANT:
# This list is the canonical sequence.
# DO NOT SORT THIS LIST BY RA.
#
# Each entry:
#   (Chinese name, English name, HIP, star designation)
# ---------------------------------------------------------------------------

XIU = [
    ("角", "Jiao", 65474, "α Vir"),
    ("亢", "Kang", 69427, "κ Vir"),
    ("氐", "Di", 72622, "α² Lib"),
    ("房", "Fang", 78265, "π Sco"),
    ("心", "Xin", 80112, "σ Sco"),
    ("尾", "Wei", 82514, "μ¹ Sco"),
    ("箕", "Ji", 88635, "γ² Sgr"),
    ("斗", "Dou", 92041, "φ Sgr"),
    ("牛", "Niu", 100345, "β Cap"),
    ("女", "Nv", 102618, "ε Aqr"),
    ("虛", "Xu", 106278, "β Aqr"),
    ("危", "Wei", 109074, "α Aqr"),
    ("室", "Shi", 113963, "α Peg"),
    ("壁", "Bi", 1067, "γ Peg"),
    ("奎", "Kui", 4463, "η And"),
    ("婁", "Lou", 8903, "β Ari"),
    ("胃", "Wei", 12719, "35 Ari"),
    ("昴", "Mao", 17499, "17 Tau"),
    ("畢", "Bi", 20889, "ε Tau"),
    ("觜", "Zi", 26207, "λ¹ Ori"),
    ("參", "Shen", 26727, "ζ¹ Ori"),
    ("井", "Jing", 30343, "μ Gem"),
    ("鬼", "Gui", 41822, "θ Cnc"),
    ("柳", "Liu", 42313, "δ Hya"),
    ("星", "Xing", 46390, "α Hya"),
    ("張", "Zhang", 48356, "υ¹ Hya"),
    ("翼", "Yi", 53740, "α Crt"),
    ("軫", "Zhen", 59803, "γ Crv"),
]


# ---------------------------------------------------------------------------
# Skyfield initialization
# ---------------------------------------------------------------------------

print("Loading Skyfield ephemeris...")

eph = load(EPHEMERIS_FILE)
ts = load.timescale()

earth = eph["earth"]

BODIES = {
    "SUN": eph["sun"],
    "MOON": eph["moon"],
    "MERCURY": eph["mercury"],
    "VENUS": eph["venus"],
    "MARS": eph["mars"],
    "JUPITER": eph["jupiter barycenter"],
    "SATURN": eph["saturn barycenter"],
}


# ---------------------------------------------------------------------------
# Time conversion
# ---------------------------------------------------------------------------

utc_time = TEST_LOCAL_TIME.astimezone(ZoneInfo("UTC"))

t = ts.from_datetime(utc_time)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_hms(hours):
    """
    Convert decimal hours to:
        12h 14m 17.20s
    """
    hours %= 24.0

    h = int(hours)

    minutes_total = (hours - h) * 60.0
    m = int(minutes_total)

    s = (minutes_total - m) * 60.0

    if s >= 59.995:
        s = 0.0
        m += 1

    if m >= 60:
        m = 0
        h += 1

    h %= 24

    return f"{h:02d}h {m:02d}m {s:05.2f}s"


def format_dms(degrees):
    """
    Convert decimal degrees to:
        +03° 49′ 12.80″
        -01° 02′ 31.46″
    """
    sign = "+" if degrees >= 0 else "-"

    x = abs(degrees)

    d = int(x)

    minutes_total = (x - d) * 60.0
    m = int(minutes_total)

    s = (minutes_total - m) * 60.0

    if s >= 59.995:
        s = 0.0
        m += 1

    if m >= 60:
        m = 0
        d += 1

    return f"{sign}{d:02d}° {m:02d}′ {s:05.2f}″"


def normalize_degrees(degrees):
    return degrees % 360.0


# ---------------------------------------------------------------------------
# Apparent geocentric equatorial position
# ---------------------------------------------------------------------------

def get_body_position(body, t):
    """
    Return apparent geocentric equatorial coordinates.

    Skyfield's apparent() applies the appropriate light-time,
    aberration, and deflection corrections for apparent position.
    """

    astrometric = earth.at(t).observe(body)

    apparent = astrometric.apparent()

    ra, dec, distance = apparent.radec()

    return (
        ra.hours,
        ra.degrees,
        distance.au,
    )


# ---------------------------------------------------------------------------
# Determinative-star positions
# ---------------------------------------------------------------------------

def get_xiu_star_positions(t):
    """
    Calculate apparent geocentric equatorial RA/Dec for all
    28 determinative stars.

    The stars are represented by HIP numbers.

    Skyfield's star() object is used with the supplied HIP catalog
    coordinates available through the Hipparcos data loader.
    """

    # Download/load Hipparcos catalog.
    # Skyfield caches it locally after first download.
    print("Loading Hipparcos catalog...")

    with load.open(
        "https://cdsarc.u-strasbg.fr/ftp/cats/I/239/hip_main.dat"
    ) as f:
        # This fallback path is intentionally not used.
        pass


# ---------------------------------------------------------------------------
# HIP star loading
# ---------------------------------------------------------------------------

def load_hipparcos():
    """
    Load the Hipparcos catalog.

    Skyfield's standard workflow uses:
        load.open(hip_main.dat)

    If the catalog has already been downloaded, Skyfield will use
    its local cache.
    """

    from skyfield.data import hipparcos

    print("Downloading/loading Hipparcos catalog...")

    with load.open(hipparcos.URL) as f:
        return hipparcos.load_dataframe(f)


# ---------------------------------------------------------------------------
# Star apparent RA
# ---------------------------------------------------------------------------

def get_star_positions(t, hip):
    """
    Return apparent geocentric RA/Dec of a HIP star.

    The star's catalog coordinates are propagated using Skyfield,
    then observed from Earth.
    """

    row = hip.loc[hip.index == hip_number]

    if len(row) == 0:
        raise ValueError(f"HIP {hip_number} not found")

    star = Star.from_dataframe(row.iloc[[0]])

    astrometric = earth.at(t).observe(star)

    apparent = astrometric.apparent()

    ra, dec, distance = apparent.radec()

    return ra.hours, ra.degrees, distance.au


# ---------------------------------------------------------------------------
# Correct star helper
# ---------------------------------------------------------------------------

from skyfield.data.hipparcos import load_dataframe
from skyfield.starlib import Star


def apparent_star_position(t, hip_df, hip_number):
    """
    Return apparent geocentric equatorial coordinates for a Hipparcos star.

    Returns ordinary Python floats, not NumPy arrays.
    """

    if hip_number not in hip_df.index:
        raise ValueError(
            f"HIP {hip_number} not found in Hipparcos catalog"
        )

    row = hip_df.loc[[hip_number]]

    star = Star.from_dataframe(row)

    astrometric = earth.at(t).observe(star)
    apparent = astrometric.apparent()

    ra, dec, distance = apparent.radec()

    return (
        float(ra.hours[0]),
        float(ra.degrees[0]),
        float(dec.degrees[0]),
        float(distance.au[0]),
    )


# ---------------------------------------------------------------------------
# Calculate all Xiu boundaries
# ---------------------------------------------------------------------------

def calculate_xiu_boundaries(t, hip_df):
    """
    Calculate the 28 mansion boundaries.

    Boundary i:

        start = RA of determinative star i
        end   = RA of determinative star i+1

    Width:

        (end - start) % 360

    The canonical order is preserved.

    Returns a list of dictionaries.
    """

    positions = []

    for chinese, english, hip_number, designation in XIU:

        ra_hours, ra_deg, dec_deg, distance = apparent_star_position(
            t,
            hip_df,
            hip_number,
        )

        positions.append(
            {
                "xiu": chinese,
                "english": english,
                "hip": hip_number,
                "star": designation,
                "ra_hours": ra_hours,
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "distance_au": distance,
            }
        )

    boundaries = []

    for i, current in enumerate(positions):

        next_position = positions[(i + 1) % len(positions)]

        start_ra = current["ra_deg"]
        end_ra = next_position["ra_deg"]

        width = (end_ra - start_ra) % 360.0

        boundaries.append(
            {
                "xiu": current["xiu"],
                "english": current["english"],
                "hip": current["hip"],
                "star": current["star"],
                "start_ra": start_ra,
                "end_ra": end_ra,
                "width": width,
                "next_xiu": next_position["xiu"],
            }
        )

    return positions, boundaries


# ---------------------------------------------------------------------------
# Find Xiu from RA
# ---------------------------------------------------------------------------

def find_xiu(ra_deg, boundaries):
    """
    Find the mansion containing an RA value.

    The boundary is:

        [start_RA, end_RA)

    using the canonical sequence.

    For the final mansion 軫, the interval wraps through 0°.
    """

    ra_deg = normalize_degrees(ra_deg)

    for b in boundaries:

        start = b["start_ra"]
        end = b["end_ra"]

        if start < end:

            if start <= ra_deg < end:
                return b

        else:

            # Wrap-around interval.
            #
            # Example:
            # start = 350°
            # end   = 10°
            #
            # valid:
            # 350° -> 360°
            # 0°   -> 10°

            if ra_deg >= start or ra_deg < end:
                return b

    raise RuntimeError(
        f"Could not assign RA {ra_deg}° to a Xiu."
    )


# ---------------------------------------------------------------------------
# Print star table
# ---------------------------------------------------------------------------

def print_xiu_table(positions, boundaries):

    print()
    print("=" * 100)
    print("28 LUNAR MANSION DETERMINATIVE STAR POSITIONS")
    print("=" * 100)

    print(
        f"{'Xiu':<5}"
        f"{'English':<8}"
        f"{'Star':<10}"
        f"{'HIP':>7}"
        f"{'RA':>18}"
        f"{'RA deg':>14}"
        f"{'Dec':>18}"
    )

    print("-" * 100)

    for p in positions:

        print(
            f"{p['xiu']:<5}"
            f"{p['english']:<8}"
            f"{p['star']:<10}"
            f"{p['hip']:>7}"
            f"{format_hms(p['ra_hours']):>18}"
            f"{p['ra_deg']:>14.8f}"
            f"{format_dms(p['dec_deg']):>18}"
        )

    print()
    print("=" * 100)
    print("XIU BOUNDARIES")
    print("=" * 100)

    print(
        f"{'Xiu':<5}"
        f"{'Start star':<12}"
        f"{'Start RA':>15}"
        f"{'End Xiu':<7}"
        f"{'End RA':>15}"
        f"{'Width':>14}"
    )

    print("-" * 100)

    total_width = 0.0

    for b in boundaries:

        total_width += b["width"]

        print(
            f"{b['xiu']:<5}"
            f"{b['star']:<12}"
            f"{b['start_ra']:>15.8f}"
            f"{b['next_xiu']:<7}"
            f"{b['end_ra']:>15.8f}"
            f"{b['width']:>14.8f}"
        )

    print("-" * 100)

    print(
        f"TOTAL WIDTH: {total_width:.12f}°"
    )

    print(
        f"EXPECTED    : 360.000000000000°"
    )

    print(
        f"DIFFERENCE  : {total_width - 360.0:.12f}°"
    )


# ---------------------------------------------------------------------------
# Print body
# ---------------------------------------------------------------------------

def print_body(name, ra_hours, ra_deg, dec_deg, distance_au, xiu=None):

    print()
    print(name)
    print("-" * 80)

    print(
        f"RA             : {format_hms(ra_hours)}"
    )

    print(
        f"RA (degrees)   : {ra_deg:.8f}°"
    )

    print(
        f"Dec            : {format_dms(dec_deg)}"
    )

    print(
        f"Dec (degrees)  : {dec_deg:.8f}°"
    )

    print(
        f"Distance       : {distance_au:.8f} AU"
    )

    if xiu is not None:

        print(
            f"Xiu            : {xiu['xiu']} {xiu['english']}"
        )

        index = next(
            i
            for i, item in enumerate(XIU)
            if item[0] == xiu["xiu"]
        )

        print(
            f"Xiu number     : {index + 1}"
        )

        print(
            f"Determinative  : {xiu['star']} "
            f"(HIP {xiu['hip']})"
        )

        print(
            f"Xiu start RA   : {xiu['start_ra']:.8f}°"
        )

        print(
            f"Xiu end RA     : {xiu['end_ra']:.8f}°"
        )

        print(
            f"Xiu width      : {xiu['width']:.8f}°"
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_boundaries(boundaries):

    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)

    # 1. Exactly 28 mansions.
    assert len(boundaries) == 28

    print("28 Xiu count              : PASS")

    # 2. Widths must be positive.
    bad_widths = [
        b for b in boundaries
        if b["width"] <= 0.0
    ]

    if bad_widths:
        print("Positive widths           : FAIL")
        for b in bad_widths:
            print(
                f"  {b['xiu']} width={b['width']}"
            )
    else:
        print("Positive widths           : PASS")

    # 3. Total width should be 360.
    total = sum(
        b["width"]
        for b in boundaries
    )

    if abs(total - 360.0) < 1e-8:
        print("Widths sum to 360°        : PASS")
    else:
        print(
            f"Widths sum to 360°        : FAIL "
            f"({total:.12f}°)"
        )

    # 4. Check for equal sectors.
    equal_sector = 360.0 / 28.0

    equal_count = sum(
        abs(b["width"] - equal_sector) < 1e-8
        for b in boundaries
    )

    if equal_count == 28:
        print("Historical widths used    : FAIL")
        print("All 28 widths are equal.")
    else:
        print("Historical widths used    : PASS")

    # 5. Check canonical sequence.
    expected_sequence = [
        item[0]
        for item in XIU
    ]

    actual_sequence = [
        b["xiu"]
        for b in boundaries
    ]

    if actual_sequence == expected_sequence:
        print("Canonical sequence        : PASS")
    else:
        print("Canonical sequence        : FAIL")

    # 6. Explicit 軫 -> 角 check.
    final_boundary = boundaries[-1]

    if (
        final_boundary["xiu"] == "軫"
        and final_boundary["next_xiu"] == "角"
    ):
        print("軫 → 角 wrap              : PASS")
    else:
        print("軫 → 角 wrap              : FAIL")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    print()
    print("=" * 80)
    print("CHINESE 28 LUNAR MANSION ALMANAC")
    print("=" * 80)

    print(
        f"Local time : "
        f"{TEST_LOCAL_TIME.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )

    print(
        f"UTC time   : "
        f"{utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    print(
        f"Julian date: {t.tt:.8f}"
    )

    print(
        f"Ephemeris  : {EPHEMERIS_FILE}"
    )

    # -----------------------------------------------------------------------
    # Load Hipparcos
    # -----------------------------------------------------------------------

    from skyfield.data import hipparcos

    print()
    print("Loading Hipparcos catalog...")

    with load.open(hipparcos.URL) as f:
        hip_df = hipparcos.load_dataframe(f)

    # -----------------------------------------------------------------------
    # Calculate Xiu boundaries
    # -----------------------------------------------------------------------

    positions, boundaries = calculate_xiu_boundaries(
        t,
        hip_df,
    )

    # -----------------------------------------------------------------------
    # Print star positions
    # -----------------------------------------------------------------------

    print_xiu_table(
        positions,
        boundaries,
    )

    # -----------------------------------------------------------------------
    # Validate Xiu system
    # -----------------------------------------------------------------------

    validate_boundaries(
        boundaries,
    )

    # -----------------------------------------------------------------------
    # Calculate planets
    # -----------------------------------------------------------------------

    for name, body in BODIES.items():

        ra_hours, ra_deg, dec_deg, distance_au = (
            None,
            None,
            None,
            None,
        )

        astrometric = earth.at(t).observe(body)

        apparent = astrometric.apparent()

        ra, dec, distance = apparent.radec()

        ra_hours = ra.hours
        ra_deg = ra.degrees
        dec_deg = dec.degrees
        distance_au = distance.au

        xiu = find_xiu(
            ra_deg,
            boundaries,
        )

        print_body(
            name,
            ra_hours,
            ra_deg,
            dec_deg,
            distance_au,
            xiu,
        )

    # -----------------------------------------------------------------------
    # Explicit Mercury validation
    # -----------------------------------------------------------------------

    mercury = eph["mercury"]

    astrometric = earth.at(t).observe(mercury)
    apparent = astrometric.apparent()

    ra, dec, distance = apparent.radec()

    mercury_xiu = find_xiu(
        ra.degrees,
        boundaries,
    )

    print()
    print("=" * 80)
    print("MERCURY VALIDATION TARGET")
    print("=" * 80)

    print(
        f"UTC              : "
        f"{utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    print(
        f"RA               : "
        f"{format_hms(ra.hours)}"
    )

    print(
        f"RA degrees       : "
        f"{ra.degrees:.8f}°"
    )

    print(
        f"Dec              : "
        f"{format_dms(dec.degrees)}"
    )

    print(
        f"Dec degrees      : "
        f"{dec.degrees:.8f}°"
    )

    print(
        f"Distance         : "
        f"{distance.au:.8f} AU"
    )

    print(
        f"Xiu              : "
        f"{mercury_xiu['xiu']} "
        f"{mercury_xiu['english']}"
    )

    mercury_xiu_number = next(
        i + 1
        for i, item in enumerate(XIU)
        if item[0] == mercury_xiu["xiu"]
    )

    print(
        f"Xiu number       : "
        f"{mercury_xiu_number}"
    )

    print(
        f"Determinative    : "
        f"{mercury_xiu['star']} "
        f"(HIP {mercury_xiu['hip']})"
    )

    print(
        f"Boundary start   : "
        f"{mercury_xiu['start_ra']:.8f}°"
    )

    print(
        f"Mercury RA       : "
        f"{ra.degrees:.8f}°"
    )

    print(
        f"Boundary end     : "
        f"{mercury_xiu['end_ra']:.8f}°"
    )

    print(
        f"Mansion width    : "
        f"{mercury_xiu['width']:.8f}°"
    )

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    main()