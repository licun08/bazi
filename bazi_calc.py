"""
Chinese BaZi (八字) calculation engine.
Calculates Four Pillars of Destiny from birth date/time.
"""

from datetime import datetime, date, time, timedelta
try:
    import ephem
    HAS_EPHEM = True
except ImportError:
    HAS_EPHEM = False

# ─── 天干地支 Tables ────────────────────────────────────────────

TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
TIAN_GAN_EN = ['Jia', 'Yi', 'Bing', 'Ding', 'Wu', 'Ji', 'Geng', 'Xin', 'Ren', 'Gui']
TIAN_GAN_ELEMENT = ['Wood', 'Wood', 'Fire', 'Fire', 'Earth', 'Earth', 'Metal', 'Metal', 'Water', 'Water']
TIAN_GAN_YINYANG = ['Yang', 'Yin', 'Yang', 'Yin', 'Yang', 'Yin', 'Yang', 'Yin', 'Yang', 'Yin']

DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
DI_ZHI_EN = ['Zi', 'Chou', 'Yin', 'Mao', 'Chen', 'Si', 'Wu', 'Wei', 'Shen', 'You', 'Xu', 'Hai']
DI_ZHI_ELEMENT = ['Water', 'Earth', 'Wood', 'Wood', 'Earth', 'Fire', 'Fire', 'Earth', 'Metal', 'Metal', 'Earth', 'Water']
DI_ZHI_ANIMAL = ['Rat', 'Ox', 'Tiger', 'Rabbit', 'Dragon', 'Snake', 'Horse', 'Goat', 'Monkey', 'Rooster', 'Dog', 'Pig']

# 地支藏干 (Hidden Stems in each Branch)
DI_ZHI_HIDDEN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

# 五鼠遁: Day Stem -> Hour Stem for 子时
WU_SHU_DUN = {
    0: 0,   # 甲日 -> 甲子
    1: 2,   # 乙日 -> 丙子
    2: 4,   # 丙日 -> 戊子
    3: 6,   # 丁日 -> 庚子
    4: 8,   # 戊日 -> 壬子
    5: 0,   # 己日 -> 甲子
    6: 2,   # 庚日 -> 丙子
    7: 4,   # 辛日 -> 戊子
    8: 6,   # 壬日 -> 庚子
    9: 8,   # 癸日 -> 壬子
}

# 五虎遁: Year Stem -> First Month Stem (寅月)
WU_HU_DUN = {
    0: 2,   # 甲年 -> 丙寅
    1: 4,   # 乙年 -> 戊寅
    2: 6,   # 丙年 -> 庚寅
    3: 8,   # 丁年 -> 壬寅
    4: 0,   # 戊年 -> 甲寅
    5: 2,   # 己年 -> 丙寅
    6: 4,   # 庚年 -> 戊寅
    7: 6,   # 辛年 -> 庚寅
    8: 8,   # 壬年 -> 壬寅
    9: 0,   # 癸年 -> 甲寅
}

# Month branches (fixed - 寅=2 for 立春 month, through 丑=1 for 小寒 month)
MONTH_BRANCH_FOR_SOLAR_TERM = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]

# Solar term names (the 12 节, not 中气)
SOLAR_TERMS = [
    '立春', '惊蛰', '清明', '立夏', '芒种', '小暑',
    '立秋', '白露', '寒露', '立冬', '大雪', '小寒'
]

SOLAR_TERMS_EN = [
    'Start of Spring', 'Awakening of Insects', 'Clear and Bright', 'Start of Summer',
    'Grain in Ear', 'Minor Heat', 'Start of Autumn', 'White Dew',
    'Cold Dew', 'Start of Winter', 'Major Snow', 'Minor Cold'
]


class BaZiEngine:
    """Main engine for calculating BaZi / Four Pillars."""

    def _get_solar_term_dates(self, year: int) -> dict:
        """Calculate exact solar term dates using sun ecliptic longitude (pure Python)."""
        terms = {}
        for i, term_name in enumerate(SOLAR_TERMS):
            target_longitude = (315 + i * 30) % 360
            approx_month = {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7,
                            6: 8, 7: 9, 8: 10, 9: 11, 10: 12, 11: 1}
            approx_day = {0: 4, 1: 6, 2: 5, 3: 5, 4: 6, 5: 7,
                          6: 7, 7: 8, 8: 8, 9: 7, 10: 7, 11: 6}
            search_year = year if i < 11 else year + 1
            try:
                start = datetime(search_year, approx_month[i], approx_day[i]) - timedelta(days=5)
                end = start + timedelta(days=15)
                target_date = self._find_sun_longitude_date(target_longitude, start, end)
                terms[term_name] = target_date
            except Exception:
                fallback = datetime(search_year, approx_month[i], approx_day[i])
                terms[term_name] = fallback
        return terms

    def _find_sun_longitude_date(self, target_lon: float, start: datetime, end: datetime) -> datetime:
        """Find exact date when sun crosses target longitude using binary search."""
        from math import sin, cos, atan2, radians, degrees

        def sun_lon(dt):
            jd = dt.timestamp() / 86400 + 2440587.5
            n = jd - 2451545.0
            L = (280.46646 + 0.98564736 * n) % 360
            g = (357.52816 + 0.98560028 * n) % 360
            lam = L + 1.9146 * sin(radians(g)) + 0.02 * sin(radians(2 * g)) + 0.0003 * sin(radians(3 * g))
            return lam % 360

        mid = start
        for _ in range(30):
            mid = start + (end - start) / 2
            lon = sun_lon(mid)
            if abs(lon - target_lon) < 0.01 or abs(lon - target_lon) > 359.99:
                return mid
            diff = (lon - target_lon + 540) % 360 - 180  # normalize to [-180, 180]
            if diff < 0:
                start = mid
            else:
                end = mid
        return mid

    def _sun_ecliptic_longitude(self, dt: datetime) -> float:
        """Calculate the Sun's ecliptic longitude for a given date.
        This is a simplified calculation accurate enough for solar term determination."""
        # Use ephem properly
        obs = ephem.Observer()
        sun = ephem.Sun()
        obs.date = dt.strftime('%Y/%m/%d %H:%M:%S')
        sun.compute(obs)
        
        # Get ecliptic longitude
        # In ephem, we can use sun.hlon (heliocentric longitude) or compute differently
        # Actually let's use a simpler approach
        
        # Use the fact that around 2000, the sun's ecliptic longitude can be approximated
        # from the day of year
        from math import sin, cos, atan2, radians, degrees
        
        # Julian date approximation
        jd = dt.timestamp() / 86400 + 2440587.5
        
        # Mean anomaly
        n = jd - 2451545.0
        L = (280.46646 + 0.98564736 * n) % 360
        g = (357.52816 + 0.98560028 * n) % 360  # mean anomaly
        
        # Ecliptic longitude
        lam = L + 1.9146 * sin(radians(g)) + 0.02 * sin(radians(2 * g)) + 0.0003 * sin(radians(3 * g))
        lam = lam % 360
        
        return lam

    def _get_solar_term_simple(self, term_name: str, year: int) -> date:
        """Simple approximate solar term dates. ±1 day accuracy."""
        # Average dates for each solar term
        avg_dates = {
            '立春': date(year, 2, 4),
            '惊蛰': date(year, 3, 6),
            '清明': date(year, 4, 5),
            '立夏': date(year, 5, 5),
            '芒种': date(year, 6, 6),
            '小暑': date(year, 7, 7),
            '立秋': date(year, 8, 7),
            '白露': date(year, 9, 8),
            '寒露': date(year, 10, 8),
            '立冬': date(year, 11, 7),
            '大雪': date(year, 12, 7),
            '小寒': date(year + 1, 1, 6),  # 小寒 of NEXT year
        }
        return avg_dates.get(term_name, date(year, 1, 1))

    def _get_solar_terms_simple(self, year: int) -> dict:
        """Get all solar term dates for a year using simple approximation."""
        terms = {}
        for term_name in SOLAR_TERMS:
            terms[term_name] = self._get_solar_term_simple(term_name, year)
        return terms

    def _get_year_pillar(self, dt: datetime) -> tuple:
        """Calculate year pillar (年柱).
        The year starts at 立春 (Start of Spring)."""
        year = dt.year
        
        # Get 立春 date for this year
        try:
            terms = self._get_solar_term_dates(year)
            lichun = terms['立春']
        except:
            lichun = datetime(year, 2, 4, 12, 0)
        if dt < lichun:
            year = year - 1
        
        stem = (year - 4) % 10
        branch = (year - 4) % 12
        
        return (stem, branch)

    def _get_month_pillar(self, dt: datetime, year_stem: int) -> tuple:
        """Calculate month pillar (月柱).
        Based on solar terms (节气)."""
        year = dt.year
        # Get solar terms for current, next, and previous year
        terms = self._get_solar_term_dates(year)
        terms_next = self._get_solar_term_dates(year + 1)
        terms_prev = self._get_solar_term_dates(year - 1)
        
        term_branches = {
            '立春': 2,  # 寅
            '惊蛰': 3,  # 卯
            '清明': 4,  # 辰
            '立夏': 5,  # 巳
            '芒种': 6,  # 午
            '小暑': 7,  # 未
            '立秋': 8,  # 申
            '白露': 9,  # 酉
            '寒露': 10, # 戌
            '立冬': 11, # 亥
            '大雪': 0,  # 子
            '小寒': 1,  # 丑
        }
        
        # Build chronological term list including cross-year terms
        term_dates = []
        # Previous year's 大雪 (Dec ~ Jan, belongs to current solar month 子)
        if '大雪' in terms_prev:
            term_dates.append(('大雪', terms_prev['大雪']))
        # Previous year's 小寒 (Jan ~ Feb, belongs to current solar month 丑)
        if '小寒' in terms_prev:
            term_dates.append(('小寒', terms_prev['小寒']))
        # Current year's 小寒 (next year's Jan ~ Feb, for checking Dec dates)
        if '小寒' in terms:
            term_dates.append(('小寒', terms['小寒']))
        # Current year's terms (立春 to 大雪)
        for t in ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑',
                   '立秋', '白露', '寒露', '立冬', '大雪']:
            d = terms.get(t)
            if d:
                term_dates.append((t, d))
        # Next year's 小寒 (Dec of current year ~ Jan of next year)
        if '小寒' in terms_next:
            term_dates.append(('小寒', terms_next['小寒']))
        
        term_dates.sort(key=lambda x: x[1])
        
        # Find which solar term month we're in
        current_term_idx = None
        current_branch = 2  # Default: 寅 (Spring)
        
        for i, (t, d) in enumerate(term_dates):
            if dt < d:
                # We're in the previous term's month
                if i == 0:
                    # Before 立春 - should be in 丑 month (小寒 to 立春)
                    current_branch = 1  # 丑
                else:
                    current_branch = term_branches[term_dates[i-1][0]]
                break
        else:
            # After 小寒 - in 丑 month
            current_branch = 1  # 丑
        
        # Calculate month stem using 五虎遁
        month_stem = (WU_HU_DUN[year_stem] + (current_branch - 2)) % 10
        
        return (month_stem, current_branch)

    def _get_day_pillar(self, dt: datetime) -> tuple:
        """Calculate day pillar (日柱).
        Uses reference: Jan 1, 1900 = 甲戌日 (Sexagenary index 10)."""
        # Reference date
        ref = date(1900, 1, 1)
        ref_sexagenary_idx = 10  # 甲戌 = stem 0, branch 10
        
        target = dt.date()
        day_diff = (target - ref).days
        
        sexagenary_idx = (ref_sexagenary_idx + day_diff) % 60
        
        stem = sexagenary_idx % 10
        branch = sexagenary_idx % 12
        
        return (stem, branch)

    def _get_hour_pillar(self, hour: int, minute: int, day_stem: int) -> tuple:
        """Calculate hour pillar (时柱).
        Hour branches: 子(23-1), 丑(1-3), 寅(3-5), 卯(5-7), etc."""
        # Determine branch based on hour and minute
        total_minutes = hour * 60 + minute
        
        if total_minutes >= 1380 or total_minutes < 60:  # 23:00-00:59
            branch = 0  # 子
        elif total_minutes < 180:  # 01:00-02:59
            branch = 1  # 丑
        elif total_minutes < 300:  # 03:00-04:59
            branch = 2  # 寅
        elif total_minutes < 420:  # 05:00-06:59
            branch = 3  # 卯
        elif total_minutes < 540:  # 07:00-08:59
            branch = 4  # 辰
        elif total_minutes < 660:  # 09:00-10:59
            branch = 5  # 巳
        elif total_minutes < 780:  # 11:00-12:59
            branch = 6  # 午
        elif total_minutes < 900:  # 13:00-14:59
            branch = 7  # 未
        elif total_minutes < 1020:  # 15:00-16:59
            branch = 8  # 申
        elif total_minutes < 1140:  # 17:00-18:59
            branch = 9  # 酉
        elif total_minutes < 1260:  # 19:00-20:59
            branch = 10  # 戌
        else:  # 21:00-22:59
            branch = 11  # 亥
        
        # Calculate hour stem using 五鼠遁
        hour_stem = (WU_SHU_DUN[day_stem] + branch) % 10
        
        return (hour_stem, branch)

    def calculate(self, dt: datetime) -> dict:
        """Calculate complete BaZi for a given datetime."""
        year_pillar = self._get_year_pillar(dt)
        month_pillar = self._get_month_pillar(dt, year_pillar[0])
        day_pillar = self._get_day_pillar(dt)
        hour_pillar = self._get_hour_pillar(dt.hour, dt.minute, day_pillar[0])
        
        return {
            'year_pillar': year_pillar,
            'month_pillar': month_pillar,
            'day_pillar': day_pillar,
            'hour_pillar': hour_pillar,
            'day_master': day_pillar[0],  # 日主 = day stem
            'day_master_element': TIAN_GAN_ELEMENT[day_pillar[0]],
            'day_master_yinyang': TIAN_GAN_YINYANG[day_pillar[0]],
        }

    def get_formatted_pillars(self, result: dict) -> dict:
        """Format pillar results into readable strings."""
        pillars = ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']
        formatted = {}
        
        for key in pillars:
            stem, branch = result[key]
            formatted[key] = {
                'stem': TIAN_GAN[stem],
                'branch': DI_ZHI[branch],
                'stem_en': TIAN_GAN_EN[stem],
                'branch_en': DI_ZHI_EN[branch],
                'stem_element': TIAN_GAN_ELEMENT[stem],
                'branch_element': DI_ZHI_ELEMENT[branch],
                'branch_animal': DI_ZHI_ANIMAL[branch],
                'stem_yinyang': TIAN_GAN_YINYANG[stem],
            }
        
        # Calculate 十神 (10 Gods / Relationships) for each pillar
        dm = result['day_master']  # 日主
        relationships = []
        
        for key in pillars:
            stem, branch = result[key]
            rel = self._get_shi_shen(dm, stem)
            relationships.append(rel)
        
        formatted['shi_shen'] = relationships
        
        return formatted

    def _get_shi_shen(self, day_master: int, other_stem: int) -> str:
        """Calculate 十神 (Ten Gods / Relationships) between day master and another stem.
        
        Wu Xing (Five Elements) relationship:
        Same element    → 比肩/劫财 (sibling/rob wealth)
        Generates me    → 正印/偏印 (positive/negative seal)
        I generate      → 食神/伤官 (eating god/hurting officer)
        Restrains me    → 正官/偏官 (positive/negative officer)
        I restrain      → 正财/偏财 (positive/negative wealth)
        
        Yang/Yang or Yin/Yin → negative aspect
        Yang/Yin or Yin/Yang → positive aspect
        """
        # Element mapping: 0=Wood, 1=Wood, 2=Fire, 3=Fire, 4=Earth, 5=Earth, 6=Metal, 7=Metal, 8=Water, 9=Water
        dm_element = day_master // 2  # 0=Wood, 1=Fire, 2=Earth, 3=Metal, 4=Water
        ot_element = other_stem // 2
        
        dm_yang = day_master % 2  # 0=Yang, 1=Yin
        ot_yang = other_stem % 2
        
        same_gender = (dm_yang == ot_yang)
        
        # Five element relationships (generating order: Wood → Fire → Earth → Metal → Water → Wood)
        # Same element
        if dm_element == ot_element:
            return '比肩 (Bi Jian - Sibling)' if same_gender else '劫财 (Jie Cai - Rob Wealth)'
        
        # Element that generates me: e.g. Water generates Wood
        prev_element = (dm_element - 1) % 5
        if ot_element == prev_element:
            return '偏印 (Pian Yin - Negative Seal)' if same_gender else '正印 (Zheng Yin - Positive Seal)'
        
        # Element I generate: e.g. Wood generates Fire
        next_element = (dm_element + 1) % 5
        if ot_element == next_element:
            return '食神 (Shi Shen - Eating God)' if same_gender else '伤官 (Shang Guan - Hurting Officer)'
        
        # Element that restrains me: e.g. Metal restrains Wood
        restraining_element = (dm_element + 2) % 5
        if ot_element == restraining_element:
            return '七杀 (Qi Sha - Seven Killings)' if same_gender else '正官 (Zheng Guan - Positive Officer)'
        
        # Element I restrain: e.g. Wood restrains Earth
        restrained_element = (dm_element - 2) % 5
        if ot_element == restrained_element:
            return '偏财 (Pian Cai - Negative Wealth)' if same_gender else '正财 (Zheng Cai - Positive Wealth)'
        
        return 'Unknown'


def format_result_for_api(result: dict, formatted: dict, birth_dt: datetime) -> dict:
    """Format the result into a readable dict for the API/template."""
    out = {
        'birth_datetime': birth_dt.strftime('%Y-%m-%d %H:%M'),
        'day_master': {
            'stem': TIAN_GAN[result['day_master']],
            'element': result['day_master_element'],
            'yinyang': result['day_master_yinyang'],
        },
        'pillars': {},
        'baZi': '',
        'year_animal': None,
    }
    
    pillar_names_cn = ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']
    pillar_names_label = ['年柱 (Year)', '月柱 (Month)', '日柱 (Day)', '时柱 (Hour)']
    
    ba_zi_parts = []
    
    for i, key in enumerate(pillar_names_cn):
        f = formatted[key]
        p = f['stem'] + f['branch']
        ba_zi_parts.append(p)
        
        out['pillars'][key] = {
            'label': pillar_names_label[i],
            'stem': f['stem'],
            'branch': f['branch'],
            'stem_en': f['stem_en'],
            'branch_en': f['branch_en'],
            'stem_element': f['stem_element'],
            'branch_element': f['branch_element'],
            'branch_animal': f['branch_animal'],
            'stem_yinyang': f['stem_yinyang'],
            'shi_shen': formatted['shi_shen'][i] if 'shi_shen' in formatted else '—',
        }
        
        if key == 'year_pillar':
            out['year_animal'] = f['branch_animal']
    
    out['baZi'] = ' '.join(ba_zi_parts)
    out['baZi_full'] = ' '.join([f'{p}({formatted["shi_shen"][i]})' 
                                 for i, (key, p) in enumerate(zip(pillar_names_cn, ba_zi_parts))])
    
    return out
