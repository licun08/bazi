"""
Compatibility analysis between two BaZi charts (合婚).
Checks branch clashes, combinations, element balance, and zodiac compatibility.
"""
from datetime import datetime
from bazi_calc import BaZiEngine, TIAN_GAN, DI_ZHI, DI_ZHI_EN, TIAN_GAN_ELEMENT, DI_ZHI_ELEMENT

engine = BaZiEngine()

# ─── Branch Clashes (六冲) ──────────────────────────
LIU_CHONG = {
    (0, 6): '子午冲', (6, 0): '子午冲',    # Rat-Horse
    (1, 7): '丑未冲', (7, 1): '丑未冲',    # Ox-Goat
    (2, 8): '寅申冲', (8, 2): '寅申冲',    # Tiger-Monkey
    (3, 9): '卯酉冲', (9, 3): '卯酉冲',    # Rabbit-Rooster
    (4, 10): '辰戌冲', (10, 4): '辰戌冲',   # Dragon-Dog
    (5, 11): '巳亥冲', (11, 5): '巳亥冲',   # Snake-Pig
}

# ─── Branch Combinations (六合) ─────────────────────
LIU_HE = {
    (0, 1): '子丑合', (1, 0): '子丑合',    # Rat-Ox
    (2, 11): '寅亥合', (11, 2): '寅亥合',  # Tiger-Pig
    (3, 10): '卯戌合', (10, 3): '卯戌合',  # Rabbit-Dog
    (4, 9): '辰酉合', (9, 4): '辰酉合',    # Dragon-Rooster
    (5, 8): '巳申合', (8, 5): '巳申合',    # Snake-Monkey
    (6, 7): '午未合', (7, 6): '午未合',    # Horse-Goat
}

# ─── Three Harmonies (三合) ─────────────────────────
SAN_HE = [
    ({0, 4, 8}, '申子辰三合水局'),      # Monkey-Rat-Dragon → Water
    ({1, 5, 9}, '巳酉丑三合金局'),      # Snake-Rooster-Ox → Metal
    ({2, 6, 10}, '寅午戌三合火局'),     # Tiger-Horse-Dog → Fire
    ({3, 7, 11}, '亥卯未三合木局'),     # Pig-Rabbit-Goat → Wood
]

# ─── Branch Punishments (刑) ────────────────────────
XING = {
    (0, 3): '子卯无礼之刑', (3, 0): '子卯无礼之刑',
    (1, 7): '丑未戌无恩之刑', (7, 1): '丑未戌无恩之刑',
    (4, 4): '辰辰自刑',
    (6, 6): '午午自刑',
    (9, 9): '酉酉自刑',
    (11, 11): '亥亥自刑',
}

# ─── Zodiac Compatibility (生肖配对) ────────────────
# 0=Rat, 1=Ox, 2=Tiger, 3=Rabbit, 4=Dragon, 5=Snake
# 6=Horse, 7=Goat, 8=Monkey, 9=Rooster, 10=Dog, 11=Pig
ZODIAC_COMPAT = {
    0: {'best': [1, 4, 8], 'bad': [6, 3, 7]},
    1: {'best': [0, 5, 9], 'bad': [7, 6, 10]},
    2: {'best': [11, 6, 10], 'bad': [8, 5]},
    3: {'best': [10, 11, 7], 'bad': [9, 4, 0]},
    4: {'best': [9, 0, 8], 'bad': [10, 3]},
    5: {'best': [8, 9, 1], 'bad': [2, 11, 3]},
    6: {'best': [2, 10, 7], 'bad': [0, 1, 3]},
    7: {'best': [3, 6, 11], 'bad': [1, 10, 0]},
    8: {'best': [5, 0, 4], 'bad': [2, 11]},
    9: {'best': [1, 5, 4], 'bad': [3, 10, 11]},
    10: {'best': [2, 6, 3], 'bad': [1, 4, 7]},
    11: {'best': [2, 3, 7], 'bad': [5, 8, 9]},
}

ZODIAC_NAMES = ['Rat', 'Ox', 'Tiger', 'Rabbit', 'Dragon', 'Snake',
                'Horse', 'Goat', 'Monkey', 'Rooster', 'Dog', 'Pig']

# ─── Year Element Relationship (纳音五行年命) ──────
# Heavenly Stem Element for year determines the couple's elemental dynamic
# Wood-Fire: compatible, Fire-Earth: compatible, Earth-Metal: compatible
# Metal-Water: compatible, Water-Wood: compatible
# Same element: neutral
# Controlling relationship: less compatible
STEM_ELEMENT_MAP = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 4}
ELEMENT_NAMES = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']


def check_branch_compatibility(b1: int, b2: int) -> list:
    """Check compatibility between two branches."""
    results = []
    
    # Check clash
    key = (min(b1, b2), max(b1, b2))
    if key in LIU_CHONG:
        results.append({'type': 'clash', 'name': LIU_CHONG[key], 'score': -3,
                       'desc': '地支相冲，关系容易有冲突和波动'})
    
    # Check combination
    key2 = (b1, b2)
    if key2 in LIU_HE:
        results.append({'type': 'harmony', 'name': LIU_HE[key2], 'score': 3,
                       'desc': '地支六合，关系和谐互补'})
    
    # Check punishment
    if key2 in XING:
        results.append({'type': 'punish', 'name': XING[key2], 'score': -2,
                       'desc': '地支相刑，容易有摩擦和压力'})
    
    # Check three-harmony
    for san_set, san_name in SAN_HE:
        if b1 in san_set and b2 in san_set:
            results.append({'type': 'sanhe', 'name': san_name, 'score': 4,
                           'desc': '地支三合，缘分深厚，能量共鸣'})
    
    return results


def get_zodiac_compat(animal1: int, animal2: int) -> dict:
    """Get zodiac compatibility."""
    compat = ZODIAC_COMPAT.get(animal1, {})
    if animal2 in compat.get('best', []):
        return {'score': 3, 'level': 'best', 'desc': '上等婚配，天生一对'}
    elif animal2 in compat.get('bad', []):
        return {'score': -2, 'level': 'bad', 'desc': '需要更多磨合，性格差异大'}
    else:
        return {'score': 0, 'level': 'neutral', 'desc': '中等婚配，可互相包容'}


def check_element_balance(dm1: int, dm2: int) -> dict:
    """Check elemental relationship between two day masters."""
    e1 = dm1 // 2  # 0=Wood, 1=Fire, 2=Earth, 3=Metal, 4=Water
    e2 = dm2 // 2
    
    if e1 == e2:
        return {'score': 1, 'desc': f'五行同属{ELEMENT_NAMES[e1]}，性格相似，容易理解对方'}
    
    # Generating cycle: Wood→Fire→Earth→Metal→Water→Wood
    gen_forward = {(0, 1): '木生火', (1, 2): '火生土', (2, 3): '土生金', (3, 4): '金生水', (4, 0): '水生木'}
    gen_backward = {(1, 0): '木生火', (2, 1): '火生土', (3, 2): '土生金', (4, 3): '金生水', (0, 4): '水生木'}
    
    key = (e1, e2)
    if key in gen_forward:
        return {'score': 3, 'desc': f'日主相生：{gen_forward[key]}，关系滋养'}
    if key in gen_backward:
        return {'score': 2, 'desc': f'日主相生：对方{gen_backward[key]}你，对你有利'}
    
    # Controlling cycle: Wood→Earth→Water→Fire→Metal→Wood
    control = {(0, 2): '木克土', (2, 4): '土克水', (4, 1): '水克火', (1, 3): '火克金', (3, 0): '金克木'}
    if key in control:
        return {'score': -1, 'desc': f'日主相克：{control[key]}，需要注意互相理解'}
    
    return {'score': 0, 'desc': '五行关系中性'}


def analyze(bazi1: dict, bazi2: dict, gender1: str = 'male', gender2: str = 'female') -> dict:
    """Full compatibility analysis between two BaZi charts."""
    results = {
        'zodiac': None,
        'branches': [],
        'day_master': None,
        'score': 0,
        'details': [],
    }
    
    p1 = bazi1['pillars']
    p2 = bazi2['pillars']
    
    # Helper: get branch index (0-11) from pillar dict key
    def get_branch_index(pd, key):
        branch_en = pd[key]['branch_en']
        for i, en in enumerate(DI_ZHI_EN):
            if branch_en == en:
                return i
        return 0
    
    # 1. Zodiac compatibility
    a1 = get_branch_index(p1, 'year_pillar')
    a2 = get_branch_index(p2, 'year_pillar')
    
    zodiac = get_zodiac_compat(a1, a2)
    results['zodiac'] = {
        'animal1': p1['year_pillar']['branch_animal'],
        'animal2': p2['year_pillar']['branch_animal'],
        'level': zodiac['level'],
        'score': zodiac['score'],
        'desc': zodiac['desc'],
    }
    results['score'] += zodiac['score']
    
    # 2. Branch compatibility (check all four pillars)
    pillar_names = ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']
    pillar_labels_cn = ['年柱', '月柱', '日柱', '时柱']
    
    for i, pn in enumerate(pillar_names):
        bi1 = get_branch_index(p1, pn)
        bi2 = get_branch_index(p2, pn)
        
        checks = check_branch_compatibility(bi1, bi2)
        for c in checks:
            c['pillar'] = pillar_labels_cn[i]
            results['score'] += c['score']
            results['branches'].append(c)
    
    # 3. Day Master element relationship
    dm1_stem = p1['day_pillar']['stem']
    dm2_stem = p2['day_pillar']['stem']
    dm1_idx = TIAN_GAN.index(dm1_stem)
    dm2_idx = TIAN_GAN.index(dm2_stem)
    
    dm_check = check_element_balance(dm1_idx, dm2_idx)
    results['day_master'] = {
        'dm1': f"{p1['day_pillar']['stem']} ({p1['day_pillar']['stem_element']})",
        'dm2': f"{p2['day_pillar']['stem']} ({p2['day_pillar']['stem_element']})",
        'score': dm_check['score'],
        'desc': dm_check['desc'],
    }
    results['score'] += dm_check['score']
    
    # Total score interpretation
    total = results['score']
    if total >= 8:
        results['verdict'] = '上等合婚'
        results['verdict_en'] = 'Excellent Match'
        results['verdict_desc'] = '两人的八字能量高度契合，互相补益，是难得的良缘。'
    elif total >= 4:
        results['verdict'] = '良好合婚'
        results['verdict_en'] = 'Good Match'
        results['verdict_desc'] = '整体比较和谐，虽有小的冲突点但可以互相包容磨合。'
    elif total >= 0:
        results['verdict'] = '中等合婚'
        results['verdict_en'] = 'Fair Match'
        results['verdict_desc'] = '有合适之处也有需要注意的地方，需要双方用心经营。'
    elif total >= -4:
        results['verdict'] = '需要注意'
        results['verdict_en'] = 'Needs Work'
        results['verdict_desc'] = '两人性格差异较大，需要更多理解和包容。'
    else:
        results['verdict'] = '挑战较大'
        results['verdict_en'] = 'Challenging Match'
        results['verdict_desc'] = '八字冲突较多，需要极大的包容和努力来维系。'
    
    return results
