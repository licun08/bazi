"""
五行平衡判断模块（喜用神 / 忌神）
Based on the 旺衰平衡 (strength-balance) school of BaZi.

This is a DETERMINISTIC calculation — no AI — so it is free, fast, and
reproducible across share links. It is a mainstream simplified algorithm,
not an authoritative judgment (BaZi has multiple schools).

Output: day-master strength (身强/身弱), favorable elements (喜用), and
unfavorable elements (忌神).
"""
from bazi_calc import TIAN_GAN, DI_ZHI, DI_ZHI_HIDDEN

# Element index: 0=木 Wood, 1=火 Fire, 2=土 Earth, 3=金 Metal, 4=水 Water
ELEMENTS_CN = ['木', '火', '土', '金', '水']
ELEMENTS_EN = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']

# Earthly-branch primary element (本气) by DI_ZHI index 0-11
# 子水 丑土 寅木 卯木 辰土 巳火 午火 未土 申金 酉金 戌土 亥水
DI_ZHI_PRIMARY = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]

# Weight for hidden stems beyond the primary (中气/余气)
HIDDEN_WEIGHT = 0.3


def _stem_element(stem_char: str) -> int:
    return TIAN_GAN.index(stem_char) // 2


def compute_wuxing_balance(bazi_data: dict, lang: str = 'zh') -> dict:
    """Compute day-master strength and favorable/unfavorable elements."""
    dm = bazi_data['day_master']
    dm_stem = dm['stem']
    dm_el = TIAN_GAN.index(dm_stem) // 2

    # ── Count five-element power across all four pillars ──
    power = [0.0, 0.0, 0.0, 0.0, 0.0]
    month_branch_char = None

    pillars = bazi_data['pillars']
    for key, p in pillars.items():
        # Heavenly stem: full weight
        power[_stem_element(p['stem'])] += 1.0

        # Earthly branch primary: full weight
        b_idx = DI_ZHI.index(p['branch'])
        power[DI_ZHI_PRIMARY[b_idx]] += 1.0

        # Hidden stems beyond primary (中气/余气): partial weight
        hidden = DI_ZHI_HIDDEN.get(p['branch'], [])
        if len(hidden) > 1:
            for h in hidden[1:]:
                power[_stem_element(h)] += HIDDEN_WEIGHT

        if key == 'month_pillar':
            month_branch_char = p['branch']

    # ── Day-master support vs drain ──
    # support (帮身) = 生我(印) + 同我(比劫)
    # drain   (克泄耗) = 我生(食伤) + 我克(财) + 克我(官杀)
    support = power[(dm_el - 1) % 5] + power[dm_el]
    drain = power[(dm_el + 1) % 5] + power[(dm_el + 2) % 5] + power[(dm_el - 2) % 5]

    # 月令得令 (month command): month branch supports the day master
    month_support = False
    if month_branch_char:
        mb_idx = DI_ZHI.index(month_branch_char)
        mb_el = DI_ZHI_PRIMARY[mb_idx]
        month_support = (mb_el == dm_el) or (mb_el == (dm_el - 1) % 5)

    # Adjust: being in command (得令) strongly favors the day master
    adj_support = support + (1.5 if month_support else 0.0)
    adj_drain = drain + (0.0 if month_support else 1.5)

    strong = adj_support >= adj_drain

    # ── Favorable / unfavorable elements ──
    # 身弱 → 喜 印(生我)+比劫(同我)，忌 财(我克)+官杀(克我)
    # 身强 → 喜 财(我克)+食伤(我生)，忌 印(生我)+比劫(同我)
    if strong:
        favorable = [(dm_el + 2) % 5, (dm_el + 1) % 5]   # 我克(财) + 我生(食伤)
        unfavorable = [(dm_el - 1) % 5, dm_el]           # 生我(印) + 同我(比劫)
    else:
        favorable = [(dm_el - 1) % 5, dm_el]             # 生我(印) + 同我(比劫)
        unfavorable = [(dm_el + 2) % 5, (dm_el - 2) % 5] # 我克(财) + 克我(官杀)

    # De-duplicate while preserving order
    def dedup(lst):
        seen = set()
        out = []
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    favorable = dedup(favorable)
    unfavorable = dedup(unfavorable)

    cn = lang == 'zh'
    return {
        'strength': 'strong' if strong else 'weak',
        'strength_label': ('身强' if strong else '身弱') if cn else ('Strong' if strong else 'Weak'),
        'strength_desc': ('日主得令得势，五行力量充沛' if strong else '日主失令，需借助外界五行补益') if cn else
                         ('Day master is well-supported' if strong else 'Day master needs support from external elements'),
        'day_master_element': ELEMENTS_CN[dm_el] if cn else ELEMENTS_EN[dm_el],
        'favorable': favorable,
        'favorable_label': '、'.join(ELEMENTS_CN[i] for i in favorable) if cn else ', '.join(ELEMENTS_EN[i] for i in favorable),
        'unfavorable': unfavorable,
        'unfavorable_label': '、'.join(ELEMENTS_CN[i] for i in unfavorable) if cn else ', '.join(ELEMENTS_EN[i] for i in unfavorable),
        'support_power': round(support, 2),
        'drain_power': round(drain, 2),
        'month_support': month_support,
    }
