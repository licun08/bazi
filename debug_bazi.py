"""Debug BaZi calculation for solar term accuracy."""
from datetime import datetime
from bazi_calc import BaZiEngine

engine = BaZiEngine()

# Debug: check exact 惊蛰 time
import math
def sun_lon(dt):
    jd = dt.timestamp() / 86400 + 2440587.5
    n = jd - 2451545.0
    L = (280.46646 + 0.98564736 * n) % 360
    g = (357.52816 + 0.98560028 * n) % 360
    lam = L + 1.9146 * math.sin(math.radians(g)) + 0.02 * math.sin(math.radians(2 * g)) + 0.0003 * math.sin(math.radians(3 * g))
    return lam % 360

print("=== Sun longitude around 惊蛰 2024 ===")
for day in [4, 5, 6]:
    for h in [0, 6, 12, 18]:
        dt = datetime(2024, 3, day, h, 0)
        print(f"  2024-03-{day:02d} {h:02d}:00  lon={sun_lon(dt):.4f}°")

print()
print("=== Detailed term dates (debug) ===")
terms = engine._get_solar_term_dates(2024)
for name, d in sorted(terms.items(), key=lambda x: x[1]):
    print(f"  {name}: {d} (type={type(d).__name__})")

print()
print("=== Borderline test: Feb 4 at various times ===")
from bazi_calc import TIAN_GAN, DI_ZHI
for h in [0, 6, 12, 16, 17, 18]:
    dt = datetime(2024, 2, 4, h, 0)
    result = engine.calculate(dt)
    parts = []
    for key in ['year_pillar', 'month_pillar']:
        s, b = result[key]
        parts.append(f"{TIAN_GAN[s]}{DI_ZHI[b]}")
    print(f"  2024-02-04 {h:02d}:00  year={parts[0]} month={parts[1]}")

print()
print("=== Borderline test: Mar 5 at various times ===")
for h in [0, 6, 10, 12, 18]:
    dt = datetime(2024, 3, 5, h, 0)
    result = engine.calculate(dt)
    parts = []
    for key in ['year_pillar', 'month_pillar']:
        s, b = result[key]
        parts.append(f"{TIAN_GAN[s]}{DI_ZHI[b]}")
    print(f"  2024-03-05 {h:02d}:00  year={parts[0]} month={parts[1]}")
