"""
True Solar Time (真太阳时) correction for BaZi calculation.
Adjusts clock time to local apparent solar time based on birthplace longitude.
"""
import json
import os
from datetime import datetime, timedelta
from math import sin, radians

CITIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cities.json')

# Load cities database
CITIES = {}
if os.path.exists(CITIES_PATH):
    with open(CITIES_PATH, 'r', encoding='utf-8') as f:
        for city in json.load(f):
            # Index by name (case-insensitive)
            key = city['name'].lower()
            CITIES[key] = city
            # Also index Chinese names
            CITIES[city['name']] = city


def search_city(query: str) -> list:
    """Search for cities matching the query."""
    query = query.lower().strip()
    results = []
    for key, city in CITIES.items():
        if query in key.lower():
            if city not in results:
                results.append(city)
    return results[:10]


def is_dst(dt: datetime, dst_start: int, dst_end: int) -> bool:
    """Check if a date falls in DST period for a given hemisphere."""
    if dst_start is None or dst_end is None:
        return False
    # Northern hemisphere: DST spring-fall
    if dst_start < dst_end:
        return dt.month >= dst_start or dt.month < dst_end
    # Southern hemisphere: DST fall-spring (e.g., Australia Oct-Apr)
    else:
        return dt.month >= dst_start or dt.month < dst_end


def get_timezone_offset(city: dict, dt: datetime) -> float:
    """Get the UTC offset for a city at a given date (accounting for DST)."""
    offset = city['utc']
    if is_dst(dt, city['dst_start'], city['dst_end']):
        offset += 1
    return offset


def solar_time_correction(longitude: float) -> float:
    """
    Calculate the true solar time correction in minutes.
    Reference: Local Solar Time = Standard Time + (longitude - ref_longitude) * 4
    
    For UTC+8 (China): ref_longitude = 120°E
    For other timezones: ref_longitude = utc_offset * 15
    """
    # Equation of Time correction (simplified)
    # This accounts for the Earth's elliptical orbit
    pass  # We add this as an optional refinement


def get_true_solar_time(dt: datetime, city: dict) -> dict:
    """
    Calculate true solar time adjustment for a birth time and location.
    Returns the adjusted time and the difference in minutes.
    """
    utc_offset = get_timezone_offset(city, dt)
    
    # Reference meridian for the timezone: UTC_offset * 15
    ref_meridian = utc_offset * 15
    
    # Difference in longitude (degrees) * 4 minutes per degree
    lon_diff = city['lon'] - ref_meridian
    time_diff_minutes = lon_diff * 4
    
    # Apply correction
    adjusted = dt + timedelta(minutes=time_diff_minutes)
    
    # Round to nearest minute
    total_seconds = (adjusted - adjusted.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    adjusted_hour = int(total_seconds // 3600)
    adjusted_minute = int((total_seconds % 3600) // 60)
    
    return {
        'city': city['name'],
        'city_en': city['name'],
        'country': city['country'],
        'longitude': city['lon'],
        'timezone': f'UTC{utc_offset:+.0f}',
        'is_dst': is_dst(dt, city['dst_start'], city['dst_end']),
        'original_time': dt.strftime('%H:%M'),
        'adjusted_hour': adjusted_hour,
        'adjusted_minute': adjusted_minute,
        'adjusted_time': f'{adjusted_hour:02d}:{adjusted_minute:02d}',
        'correction_minutes': round(time_diff_minutes),
        'correction_text': _correction_text(round(time_diff_minutes)),
    }


def _correction_text(minutes: int) -> str:
    """Generate human-readable correction text."""
    if minutes == 0:
        return "No correction needed"
    elif minutes > 0:
        return f"Add {minutes} min (west of reference)"
    else:
        return f"Subtract {abs(minutes)} min (east of reference)"


def compute_adjusted_birth_time(year: int, month: int, day: int, hour: int, minute: int, city_name: str) -> dict:
    """
    Compute true solar time adjusted birth time.
    Returns original and adjusted datetime + correction info.
    """
    original = datetime(year, month, day, hour, minute)
    
    city = CITIES.get(city_name.lower())
    if not city:
        return {
            'original': original,
            'adjusted_hour': hour,
            'adjusted_minute': minute,
            'correction': None,
            'city_found': False,
        }
    
    info = get_true_solar_time(original, city)
    return {
        'original': original,
        'adjusted_hour': info['adjusted_hour'],
        'adjusted_minute': info['adjusted_minute'],
        'correction': info,
        'city_found': True,
    }
