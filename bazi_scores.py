"""
BaZi fun score calculator — entertainment chart scoring.
6 dimensions: Charisma, Wealth, Career, Marriage, Health, Talent.
Composite score shown in center.
"""
from bazi_calc import TIAN_GAN, DI_ZHI

# ── Element index (0=Wood,1=Fire,2=Earth,3=Metal,4=Water) ──
EL_MAP = {'Wood': 0, 'Fire': 1, 'Earth': 2, 'Metal': 3, 'Water': 4}

# 六合: 子丑, 寅亥, 卯戌, 辰酉, 巳申, 午未
SIX_HE = [{0,1}, {2,11}, {3,10}, {4,9}, {5,8}, {6,7}]
# 三合: 申子辰, 亥卯未, 寅午戌, 巳酉丑
TRIPLE_HE = [{8,0,4}, {11,2,7}, {2,6,10}, {5,9,1}]
# 六冲: 子午, 丑未, 寅申, 卯酉, 辰戌, 巳亥
SIX_CHONG = [{0,6}, {1,7}, {2,8}, {3,9}, {4,10}, {5,11}]

# 桃花星: 年支 → 桃花地支
PEACH_BLOSSOM = {0: 3, 1: 6, 2: 9, 3: 0, 4: 9, 5: 0, 6: 3, 7: 6, 8: 6, 9: 9, 10: 0, 11: 3}

# 财库: 五行 → 地支
WEALTH_VAULT = {0: 7, 1: 10, 2: 4, 3: 1, 4: 4}

# 文昌星: 日干 → 地支
# 甲巳乙午, 丙申丁酉, 戊申己酉, 庚亥辛子, 壬寅癸卯
WEN_CHANG = {0: 5, 1: 6, 2: 8, 3: 9, 4: 8, 5: 9, 6: 11, 7: 0, 8: 2, 9: 3}


def _el(name):
    return EL_MAP.get(name, -1)


def _cap(v, lo=5, hi=100):
    return max(lo, min(hi, v))


def _pick_title(dm_element, top_dim_name, composite, lang):
    """Pick honorific title from day master element & top dimension."""
    el_en = {
        0: ("Jade Scholar", "The Verdant", "of Eternal Spring"),
        1: ("Crimson Phoenix", "The Blazing", "of the Rising Sun"),
        2: ("Golden Sage", "The Mountain", "of Solid Ground"),
        3: ("Iron Commander", "The Platinum", "of Unyielding Will"),
        4: ("Azure Seer", "The Deep", "of Endless Flow"),
    }
    el_cn = {
        0: ("青木帝君", "玉面", "春风化雨"),
        1: ("烈焰帝君", "赤焰", "如日中天"),
        2: ("厚土天尊", "黄金", "稳如泰山"),
        3: ("白金将星", "铁血", "百炼成钢"),
        4: ("玄水真人", "沧海", "上善若水"),
    }
    dim_en = {
        'charisma': ("Irresistible Aura", "of Magnetic Charm"),
        'wealth':   ("Fortune's Favorite", "of Abundant Gold"),
        'career':   ("Destined Commander", "of Rising Glory"),
        'marriage': ("Soulmate Blessed", "of Eternal Bond"),
        'health':   ("Vital Spirit", "of Boundless Energy"),
        'talent':   ("Gifted Genius", "of Brilliant Mind"),
    }
    dim_cn = {
        'charisma': ("倾国倾城", "魅力四射"),
        'wealth':   ("财神眷顾", "富贵天成"),
        'career':   ("天命所归", "步步高升"),
        'marriage': ("天赐良缘", "琴瑟和鸣"),
        'health':   ("寿比南山", "身心健康"),
        'talent':   ("才高八斗", "天赋异禀"),
    }

    if lang == 'zh':
        en, ep, es = el_cn.get(dm_element, el_cn[2])
        dn, ds = dim_cn.get(top_dim_name, dim_cn['talent'])
        if composite >= 88:
            return f"「{en}」· {dn}"
        elif composite >= 70:
            return f"「{ep}」· {dn}"
        else:
            return f"「{ds}」"
    else:
        en, ep, es = el_en.get(dm_element, el_en[2])
        dn, ds = dim_en.get(top_dim_name, dim_en['talent'])
        if composite >= 88:
            return f"「{en}」— {dn}"
        elif composite >= 70:
            return f"「{ep} {dn}」"
        else:
            return f"「{ds}」"


def compute_scores(bazi_data, lang='zh'):
    """Compute 6 fun dimensions + composite + title from BaZi data."""
    pillars = bazi_data['pillars']
    dm = bazi_data['day_master']
    dm_element = _el(dm['element'])
    dm_idx = TIAN_GAN.index(dm['stem'])

    stems, branches, shi_shens, stem_els, branch_els = [], [], [], [], []
    for key in ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']:
        p = pillars[key]
        stems.append(TIAN_GAN.index(p['stem']))
        branches.append(DI_ZHI.index(p['branch']))
        shi_shens.append(p['shi_shen'])
        stem_els.append(_el(p['stem_element']))
        branch_els.append(_el(p['branch_element']))

    has_eating  = any('食神' in s for s in shi_shens)
    has_hurting = any('伤官' in s for s in shi_shens)
    has_seal    = any('印'   in s for s in shi_shens)
    has_7kill   = any('七杀' in s for s in shi_shens)
    has_wealth  = any('财'   in s for s in shi_shens)
    has_sibling = any('比肩' in s for s in shi_shens)
    has_rob     = any('劫财' in s for s in shi_shens)
    has_zheng_cai = any('正财' in s for s in shi_shens)
    has_pian_cai  = any('偏财' in s for s in shi_shens)
    has_zheng_guan = any('正官' in s for s in shi_shens)
    has_pian_guan  = any('七杀' in s for s in shi_shens)

    wealth_count = sum(1 for s in shi_shens if '财' in s)
    officer_count = sum(1 for s in shi_shens if '官' in s or '七杀' in s)
    seal_count = sum(1 for s in shi_shens if '印' in s)
    all_el = stem_els + branch_els
    unique_els = len(set(all_el))
    el_counts = [all_el.count(i) for i in range(5)]

    year_branch = branches[0]
    peach = PEACH_BLOSSOM.get(year_branch, -1)
    peach_count = branches.count(peach)
    day_branch = branches[2]

    # ── 1. 魅力 / Charisma ──
    cha = 40
    if has_eating: cha += 16
    if has_hurting: cha += 10
    cha += peach_count * 18
    if branches[2] == peach: cha += 10
    if has_rob: cha -= 8
    if has_7kill: cha += 6
    cha = _cap(cha)

    # ── 2. 财运 / Wealth ──
    wea = 40
    if has_zheng_cai: wea += 20
    if has_pian_cai: wea += 15
    if wealth_count >= 2: wea += 10
    if wealth_count >= 3: wea += 8
    if has_eating and has_wealth: wea += 12
    vault = WEALTH_VAULT.get(dm_element, -1)
    if vault in branches: wea += 15
    if has_rob: wea -= 10
    if has_sibling and has_rob and not has_wealth: wea -= 8
    wea = _cap(wea)

    # ── 3. 事业 / Career ──
    car = 40
    if has_zheng_guan: car += 15
    if has_pian_guan: car += 12
    if has_7kill and has_seal: car += 22
    if has_wealth and (has_zheng_guan or has_pian_guan): car += 12
    if has_seal: car += 10
    if has_hurting and (has_zheng_guan or has_pian_guan): car -= 15
    if officer_count >= 3: car -= 10
    elif officer_count >= 2: car -= 5
    if has_eating and has_7kill: car += 8
    car = _cap(car)

    # ── 4. 婚姻 / Marriage ──
    mar = 45
    gender = bazi_data.get('gender', 'male')
    if gender == 'male':
        if has_zheng_cai: mar += 20
        if has_pian_cai: mar += 8
    else:
        if has_zheng_guan: mar += 20
        if has_pian_guan: mar += 8
    for i in range(4):
        if i != 2 and {day_branch, branches[i]} in [set(h) for h in SIX_HE]:
            mar += 12
    for i in range(4):
        if i != 2 and {day_branch, branches[i]} in [set(c) for c in SIX_CHONG]:
            mar -= 15
    if day_branch == peach: mar += 12
    mar += peach_count * 10
    if has_rob: mar -= 10
    if branches.count(day_branch) >= 2: mar -= 5
    mar = _cap(mar, lo=5, hi=98)

    # ── 5. 健康 / Health ──
    hea = 40
    hea += unique_els * 4
    if max(el_counts) >= 4: hea -= 15
    elif max(el_counts) >= 3: hea -= 5
    chong_count = 0
    for i in range(4):
        for j in range(i+1, 4):
            if {branches[i], branches[j]} in [set(c) for c in SIX_CHONG]:
                chong_count += 1
    hea -= chong_count * 8
    if officer_count >= 3: hea -= 10
    elif officer_count >= 2: hea -= 5
    if has_seal: hea += 8
    if unique_els == 5: hea += 10
    bset = set(branches)
    for combo in TRIPLE_HE:
        if len(bset & combo) >= 2: hea += 5
    hea = _cap(hea)

    # ── 6. 才华 / Talent ──
    tal = 40
    # 食神 = 创造力、表达能力
    if has_eating: tal += 20
    # 伤官 = 才华、聪明
    if has_hurting: tal += 16
    # 文昌星: 日干 → 地支
    wc_branch = WEN_CHANG.get(dm_idx, -1)
    if wc_branch in branches: tal += 18
    # 文昌出现多次
    if branches.count(wc_branch) >= 2: tal += 10
    # 印星 = 学习能力、知识储备
    if has_seal: tal += 10
    if seal_count >= 2: tal += 6
    # 杀印相生 = 逆境中的智慧
    if has_7kill and has_seal: tal += 8
    # 食神+印 = 创造力+学识
    if has_eating and has_seal: tal += 8
    # 伤官见官 = 才华被压制
    if has_hurting and (has_zheng_guan or has_pian_guan): tal -= 8
    tal = _cap(tal)

    # ── 综合 Composite (center) ──
    composite = round(cha * 0.15 + wea * 0.18 + car * 0.20 + mar * 0.15 + hea * 0.15 + tal * 0.12 + 5)
    composite = max(1, min(100, composite))

    # ── Chosen tier ──
    tiers = [
        (85, 5, '👑', '天选之命 · 万中无一', 'The Chosen One · One in Ten Thousand'),
        (72, 4, '⭐', '非凡之命 · 人中龙凤', 'Extraordinary · Among the Elite'),
        (58, 3, '✨', '上等之命 · 得天独厚', 'Favored · Blessed by Heaven'),
        (42, 2, '🌿', '中等之命 · 不偏不倚', 'Balanced · Steady and True'),
        (0,  1, '🔥', '磨砺之命 · 苦尽甘来', 'Tempered · Rising Through Fire'),
    ]
    chosen_tier, chosen_emoji = 1, '🔥'
    chosen_label = tiers[-1][3] if lang == 'zh' else tiers[-1][4]
    for threshold, tier, emoji, zh_lbl, en_lbl in tiers:
        if composite >= threshold:
            chosen_tier = tier
            chosen_emoji = emoji
            chosen_label = zh_lbl if lang == 'zh' else en_lbl
            break

    # ── 6 dimensions on hexagon ──
    dim_names = ['魅力', '财运', '事业', '婚姻', '健康', '才华'] if lang == 'zh' \
                else ['Charisma', 'Wealth', 'Career', 'Marriage', 'Health', 'Talent']
    dim_keys = ['charisma', 'wealth', 'career', 'marriage', 'health', 'talent']
    dim_values = [cha, wea, car, mar, hea, tal]

    top_idx = dim_values.index(max(dim_values))
    title = _pick_title(dm_element, dim_keys[top_idx], composite, lang)

    return {
        'dimensions': {k: round(v) for k, v in zip(dim_keys, dim_values)},
        'dimension_names': dim_names,
        'dimension_keys': dim_keys,
        'composite': composite,
        'chosen_tier': chosen_tier,
        'chosen_label': chosen_label,
        'chosen_emoji': chosen_emoji,
        'title': title,
        'stars': '★' * chosen_tier + '☆' * (5 - chosen_tier),
    }


def generate_hex_svg(scores, lang='zh', size=300):
    """SVG hexagon radar chart for 6 dimensions. Composite in center."""
    dim_keys = scores['dimension_keys']
    dim_values = [scores['dimensions'][k] for k in dim_keys]
    dim_names = scores['dimension_names']

    # 6 axes (top = -90°, clockwise)
    axes = [
        (0, -1),       # top
        (0.866, -0.5), # upper-right
        (0.866, 0.5),  # lower-right
        (0, 1),        # bottom
        (-0.866, 0.5), # lower-left
        (-0.866, -0.5),# upper-left
    ]
    cx = cy = size // 2
    r_max = size * 0.40

    def vertex(ratio, i):
        return f"{cx + r_max * ratio * axes[i][0]:.1f},{cy + r_max * ratio * axes[i][1]:.1f}"

    bg = '\n'.join(
        f'<polygon points="{" ".join(vertex(p/100, i) for i in range(6))}" fill="none" stroke="rgba(139,69,19,0.08)" stroke-width="1"/>'
        for p in [20, 40, 60, 80, 100]
    )
    gl = '\n'.join(
        f'<line x1="{cx}" y1="{cy}" x2="{cx + r_max * axes[i][0]:.1f}" y2="{cy + r_max * axes[i][1]:.1f}" stroke="rgba(139,69,19,0.06)" stroke-width="1"/>'
        for i in range(6)
    )

    score_pts = ' '.join(vertex(dim_values[i] / 100, i) for i in range(6))
    score_poly = f'<polygon points="{score_pts}" fill="rgba(139,69,19,0.25)" stroke="#5c2e0e" stroke-width="2" stroke-linejoin="round"/>'

    # Data points at vertices
    pts_html = ''
    for i in range(6):
        ratio = dim_values[i] / 100
        x = cx + r_max * ratio * axes[i][0]
        y = cy + r_max * ratio * axes[i][1]
        pts_html += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#5c2e0e"/>'

    # Axis names: far outside, with the label itself
    lo = size * 0.60
    axis_labels = ''
    for i in range(6):
        lx = cx + lo * axes[i][0]
        ly = cy + lo * axes[i][1]
        axis_labels += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="13" fill="#8b7355" font-family="Georgia,serif" font-weight="bold">{dim_names[i]}</text>'

    cc = scores['composite']
    center = f'<text x="{cx}" y="{cy - 8}" text-anchor="middle" font-size="26" fill="#5c2e0e" font-weight="bold" font-family="Georgia,serif">{cc}</text>' \
             f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" font-size="10" fill="#b8a88a" font-family="Georgia,serif">/100</text>'

    return f'''<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg" style="display:block;margin:0 auto;">
  {bg}
  {gl}
  <circle cx="{cx}" cy="{cy}" r="2" fill="#5c2e0e" opacity="0.3"/>
  {score_poly}
  {pts_html}
  {axis_labels}
  {center}
</svg>'''
