"""Test BaZi calculation against known references."""
from datetime import datetime
from bazi_calc import BaZiEngine, TIAN_GAN, DI_ZHI

engine = BaZiEngine()

tests = [
    # (datetime, expected_年柱, expected_月柱, expected_日柱, expected_时柱, note)
    # Known reference: my birth date
    (datetime(2024, 2, 4), None, None, None, None, "立春当天, 年柱应换为甲辰"),
    (datetime(2024, 2, 3), None, None, None, None, "立春前一天, 年柱应为癸卯"),
    (datetime(2024, 3, 5, 10), None, None, None, None, "惊蛰前后"),
]

for dt, *_ in tests:
    result = engine.calculate(dt)
    parts = []
    for key in ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']:
        s, b = result[key]
        parts.append(f"{TIAN_GAN[s]}{DI_ZHI[b]}")
    print(f"{dt}  -> {' '.join(parts)}  八字: {parts[0]}{parts[1]} {parts[2]}{parts[3]}")

print()
print("=== Solar term dates check ===")
terms = engine._get_solar_terms_simple(2024)
for name, d in sorted(terms.items(), key=lambda x: x[1]):
    print(f"  {name}: {d}")

print()
# Check if ephem is available
try:
    import ephem
    print("ephem IS available ✓")
except ImportError:
    print("ephem NOT available, using simple approximation ✗")

# Check the ecliptic longitude calculation precision
print()
print("=== Sun ecliptic longitude on key dates ===")
from bazi_calc import BaZiEngine
eng = BaZiEngine()
key_dates = [
    datetime(2024, 2, 4),  # 立春 ~315°
    datetime(2024, 3, 5),  # 惊蛰 ~345°
    datetime(2024, 4, 4),  # 清明 ~15°
]
for dt in key_dates:
    lon = eng._sun_ecliptic_longitude(dt)
    print(f"  {dt.date()}: ecliptic lon = {lon:.2f}°")
