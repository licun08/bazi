"""BaZi fun score calculator — entertainment-oriented chart scoring with hexagon radar, composite rating, and honorific titles."""
from bazi_calc import TIAN_GAN, DI_ZHI

# ── Element index mapping (same as bazi_calc: 0=Wood,1=Fire,2=Earth,3=Metal,4=Water) ──
EL_MAP = {'Wood': 0, 'Fire': 1, 'Earth': 2, 'Metal': 3, 'Water': 4}

# 地支六合: 子丑, 寅亥, 卯戌, 辰酉, 巳申, 午未
SIX_HE = [{0,1}, {2,11}, {3,10}, {4,9}, {5,8}, {6,7}]

# 地支三合: 申子辰, 亥卯未, 寅午戌, 巳酉丑
TRIPLE_HE = [{8,0,4}, {11,2,7}, {2,6,10}, {5,9,1}]

# 六冲: 子午, 丑未, 寅申, 卯酉, 辰戌, 巳亥
SIX_CHONG = [{0,6}, {1,7}, {2,8}, {3,9}, {4,10}, {5,11}]


def _el(name):
    return EL_MAP.get(name, -1)

def _to_tier(score):
    if score >= 90: return 5
    if score >= 78: return 4
    if score >= 65: return 3
    if score >= 50: return 2
    return 1

def _pick_titles(dm_element, top_dim_name, composite, lang):
    """Select honorific title based on day master element and top dimension."""
    element_titles_en = {
        0: {"name": "Jade Scholar",         "prefix": "The Verdant",   "suffix": "of Eternal Spring"},
        1: {"name": "Crimson Phoenix",      "prefix": "The Blazing",   "suffix": "of the Rising Sun"},
        2: {"name": "Golden Sage",          "prefix": "The Mountain",  "suffix": "of Solid Ground"},
        3: {"name": "Iron Commander",       "prefix": "The Platinum",  "suffix": "of Unyielding Will"},
        4: {"name": "Azure Sage",           "prefix": "The Deep",      "suffix": "of Endless Flow"},
    }
    element_titles_cn = {
        0: {"name": "青木帝君",  "prefix": "玉面", "suffix": "春风化雨"},
        1: {"name": "烈焰帝君",  "prefix": "赤焰", "suffix": "如日中天"},
        2: {"name": "厚土天尊",  "prefix": "黄金", "suffix": "稳如泰山"},
        3: {"name": "白金将星",  "prefix": "铁血", "suffix": "百炼成钢"},
        4: {"name": "玄水真人",  "prefix": "沧海", "suffix": "上善若水"},
    }
    dim_titles_en = {
        'element_balance': ('Element Seer', 'of Perfect Harmony'),
        'pattern_power': ('Destined Strategist', 'of Hidden Patterns'),
        'noble_luck': ('Heaven-Blessed', 'of Auspicious Stars'),
        'social_harmony': ('Silver Tongue', 'of Boundless Connections'),
        'career_wealth': ('Prosperity Lord', 'of Abundant Fortune'),
        'overall_aura': ('Cosmic Chosen', 'of the Grand Design'),
    }
    dim_titles_cn = {
        'element_balance': ('五行尊者', '通晓造化'),
        'pattern_power': ('天命军师', '洞察玄机'),
        'noble_luck': ('天佑之子', '贵人云集'),
        'social_harmony': ('八面玲珑', '四海皆友'),
        'career_wealth': ('财神眷顾', '富贵天成'),
        'overall_aura': ('大道之子', '天命所归'),
    }

    if lang == 'zh':
        et = element_titles_cn.get(dm_element, element_titles_cn[2])
        dt = dim_titles_cn.get(top_dim_name, dim_titles_cn['overall_aura'])
        if composite >= 88:
            return f"「{et['name']}」· {dt[0]}"
        elif composite >= 70:
            return f"「{et['suffix']}」· {dt[1]}"
        else:
            return f"「{dt[1]}」"
    else:
        et = element_titles_en.get(dm_element, element_titles_en[2])
        dt = dim_titles_en.get(top_dim_name, dim_titles_en['overall_aura'])
        if composite >= 88:
            return f"「{et['name']}」— {dt[0]}"
        elif composite >= 70:
            return f"「{et['prefix']} {dt[0]}」"
        else:
            return f"「{dt[1]}」"


def compute_scores(bazi_data, lang='zh'):
    """Compute 6-dimension fun scores + composite + title from BaZi data."""
    pillars = bazi_data['pillars']
    dm = bazi_data['day_master']
    dm_element = _el(dm['element'])
    dm_idx = TIAN_GAN.index(dm['stem'])

    stems = []
    branches = []
    shi_shens = []
    stem_els = []
    branch_els = []

    for key in ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']:
        p = pillars[key]
        si = TIAN_GAN.index(p['stem'])
        bi = DI_ZHI.index(p['branch'])
        stems.append(si)
        branches.append(bi)
        shi_shens.append(p['shi_shen'])
        stem_els.append(_el(p['stem_element']))
        branch_els.append(_el(p['branch_element']))

    # ── 1. 元素平衡 Element Balance ──
    all_el = stem_els + branch_els
    unique_els = len(set(all_el))
    el_balance = unique_els * 20
    if unique_els <= 2:
        el_balance = max(10, el_balance - 10)
    if unique_els == 5:
        el_balance = min(100, el_balance + 5)
    el_balance = max(5, min(100, el_balance))

    # ── 2. 格局潜力 Pattern Power ──
    pat = 50
    has_7kill = any('七杀' in s for s in shi_shens)
    has_seal  = any('印' in s for s in shi_shens)
    has_wealth = any('财' in s for s in shi_shens)
    has_officer = any('正官' in s for s in shi_shens)
    has_eating = any('食神' in s for s in shi_shens)
    has_hurting = any('伤官' in s for s in shi_shens)
    has_sibling = any('比肩' in s for s in shi_shens)
    has_rob = any('劫财' in s for s in shi_shens)

    if has_7kill and has_seal:
        pat += 25  # 杀印相生 — powerful
    if has_wealth and has_officer:
        pat += 15  # 财官相生
    if has_eating and has_wealth:
        pat += 10  # 食神生财
    if has_hurting and has_officer:
        pat -= 15  # 伤官见官
    if has_sibling and has_rob and (not has_wealth):
        pat -= 10  # 比劫夺财
    if has_seal and has_eating:
        pat += 8   # 印食相济
    pat = max(5, min(95, pat))

    # ── 3. 贵人缘分 Noble Luck ──
    noble = 40
    # 六合
    for i in range(4):
        for j in range(i+1, 4):
            if {branches[i], branches[j]} in [set(h) for h in SIX_HE]:
                noble += 12
    # 三合
    bset = set(branches)
    for combo in TRIPLE_HE:
        overlap = len(bset & combo)
        if overlap == 3:
            noble += 20
        elif overlap == 2:
            noble += 8
    # 六冲 — penalty
    for i in range(4):
        for j in range(i+1, 4):
            if {branches[i], branches[j]} in [set(c) for c in SIX_CHONG]:
                noble -= 15
    # 自刑 — slight penalty
    noble = max(5, min(100, noble))

    # ── 4. 人际关系 Social Harmony ──
    soc = 50
    if has_officer:
        soc += 15
    if has_rob:
        soc -= 10
    if has_sibling:
        soc += 8
    if has_eating:
        soc += 6
    if has_hurting:
        soc -= 8
    # Element generates another positive flow
    next_el = (dm_element + 1) % 5
    prev_el = (dm_element - 1) % 5
    if next_el in stem_els:
        soc += 8
    if prev_el in stem_els:
        soc += 4
    soc = max(5, min(100, soc))

    # ── 5. 财运事业 Career & Wealth ──
    car = 45
    wealth_count = sum(1 for s in shi_shens if '财' in s)
    officer_count = sum(1 for s in shi_shens if '官' in s)
    if wealth_count > 0:
        car += 18
    if officer_count > 0:
        car += 12
    if wealth_count >= 2:
        car += 10
    if wealth_count >= 3:
        car += 8
    car -= has_rob * 8
    car -= has_hurting * 6
    if has_seal:
        car += 6  # 印星护身助事业
    car = max(5, min(100, car))

    # ── 6. 综合气场 Overall Aura ──
    aura = (el_balance * 0.12 + pat * 0.22 + noble * 0.18 + soc * 0.15 + car * 0.18) + 10
    aura = max(10, min(100, aura))

    # ── Composite ──
    composite = round(el_balance * 0.12 + pat * 0.22 + noble * 0.15 +
                      soc * 0.13 + car * 0.18 + aura * 0.20)
    composite = max(1, min(100, composite))

    # ── Tier & Chosen One Check ──
    if composite >= 85:
        chosen_tier = 5
        chosen_label = {'zh': '天选之命 · 万中无一', 'en': 'The Chosen One · One in Ten Thousand'}[lang]
        chosen_emoji = '👑'
    elif composite >= 72:
        chosen_tier = 4
        chosen_label = {'zh': '非凡之命 · 人中龙凤', 'en': 'Extraordinary · Among the Elite'}[lang]
        chosen_emoji = '⭐'
    elif composite >= 58:
        chosen_tier = 3
        chosen_label = {'zh': '上等之命 · 得天独厚', 'en': 'Favored · Blessed by Heaven'}[lang]
        chosen_emoji = '✨'
    elif composite >= 42:
        chosen_tier = 2
        chosen_label = {'zh': '中等之命 · 不偏不倚', 'en': 'Balanced · Steady and True'}[lang]
        chosen_emoji = '🌿'
    else:
        chosen_tier = 1
        chosen_label = {'zh': '磨砺之命 · 苦尽甘来', 'en': 'Tempered · Rising Through Fire'}[lang]
        chosen_emoji = '🔥'

    # ── Dimension Names ──
    dim_names = {
        'zh': ['五行平衡', '格局潜力', '贵人缘分', '人际和谐', '财运事业', '综合气场'],
        'en': ['Element\nBalance', 'Pattern\nPower', 'Noble\nLuck', 'Social\nHarmony', 'Career\nWealth', 'Overall\nAura'],
    }
    names = dim_names.get(lang, dim_names['zh'])

    dim_keys = ['element_balance', 'pattern_power', 'noble_luck',
                'social_harmony', 'career_wealth', 'overall_aura']
    dim_values = [el_balance, pat, noble, soc, car, aura]

    # ── Honorific Title ──
    # Find the top dimension
    top_idx = dim_values.index(max(dim_values))
    top_dim_key = dim_keys[top_idx]
    title = _pick_titles(dm_element, top_dim_key, composite, lang)

    # ── Star rating (visual) ──
    stars = '★' * chosen_tier + '☆' * (5 - chosen_tier)

    return {
        'dimensions': {k: round(v) for k, v in zip(dim_keys, dim_values)},
        'dimension_names': names,  # list of 6 names
        'dimension_keys': dim_keys,
        'composite': composite,
        'chosen_tier': chosen_tier,
        'chosen_label': chosen_label,
        'chosen_emoji': chosen_emoji,
        'title': title,
        'stars': stars,
    }


def generate_hex_svg(scores, lang='zh', size=300):
    """Generate an inline SVG hexagon radar chart from scores."""
    dim_keys = scores['dimension_keys']
    dim_values = [scores['dimensions'][k] for k in dim_keys]
    dim_names = scores['dimension_names']

    # 6 axes unit vectors (top = -90°, clockwise)
    axes = [
        (0, -1),      # 0: top
        (0.866, -0.5),# 1: upper-right
        (0.866, 0.5), # 2: lower-right
        (0, 1),       # 3: bottom
        (-0.866, 0.5),# 4: lower-left
        (-0.866, -0.5),#5: upper-left
    ]
    cx = cy = size // 2
    r_max = size * 0.4

    def vertex(ratio, i):
        x = cx + r_max * ratio * axes[i][0]
        y = cy + r_max * ratio * axes[i][1]
        return f"{x:.1f},{y:.1f}"

    bg_polygons = []
    grid_lines = []
    # Background rings at 20, 40, 60, 80, 100%
    for pct in [20, 40, 60, 80, 100]:
        r = pct / 100
        pts = ' '.join(vertex(r, i) for i in range(6))
        bg_polygons.append(f'<polygon points="{pts}" fill="none" stroke="rgba(139,69,19,0.08)" stroke-width="1"/>')

    # Axis lines from center
    for i in range(6):
        x, y = cx + r_max * axes[i][0], cy + r_max * axes[i][1]
        grid_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="rgba(139,69,19,0.06)" stroke-width="1"/>')

    # Score polygon
    score_pts = ' '.join(vertex(dim_values[i] / 100, i) for i in range(6))
    score_poly = f'<polygon points="{score_pts}" fill="rgba(139,69,19,0.25)" stroke="#5c2e0e" stroke-width="2" stroke-linejoin="round"/>'
    score_points = ''
    for i in range(6):
        x, y = (cx + r_max * (dim_values[i] / 100) * axes[i][0],
                cy + r_max * (dim_values[i] / 100) * axes[i][1])
        score_points += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#5c2e0e"/>'

    # Axis labels (slightly outside the ring)
    label_offset = size * 0.48
    labels = ''
    for i in range(6):
        lx = cx + label_offset * axes[i][0]
        ly = cy + label_offset * axes[i][1]
        name = dim_names[i].replace('\n', '<tspan dy="6">')
        if '\n' in dim_names[i]:
            parts = dim_names[i].split('\n')
            labels += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="10" fill="#8b7355" font-family="Georgia,serif"><tspan x="{lx:.1f}" dy="-6">{parts[0]}</tspan><tspan x="{lx:.1f}" dy="12">{parts[1]}</tspan></text>'
        else:
            labels += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="#8b7355" font-family="Georgia,serif">{name}</text>'

    # Score values near each vertex
    score_labels = ''
    for i in range(6):
        score_val = dim_values[i]
        offset_mult = 1.15 if dim_values[i] > 60 else 1.3
        lx = cx + r_max * offset_mult * axes[i][0]
        ly = cy + r_max * offset_mult * axes[i][1]
        score_labels += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="13" fill="#5c2e0e" font-weight="bold" font-family="Georgia,serif">{score_val}</text>'

    # Center composite score
    cc = scores['composite']
    center_text = f'<text x="{cx}" y="{cy - 8}" text-anchor="middle" font-size="22" fill="#5c2e0e" font-weight="bold" font-family="Georgia,serif">{cc}</text><text x="{cx}" y="{cy + 12}" text-anchor="middle" font-size="9" fill="#8b7355" font-family="Georgia,serif">/{"" if lang == "zh" else " "}100</text>'

    bg = '\n'.join(bg_polygons)
    gl = '\n'.join(grid_lines)

    svg = f'''<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg" style="display:block;margin:0 auto;">
  <defs>
    <filter id="hex-glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  {bg}
  {gl}
  <circle cx="{cx}" cy="{cy}" r="2" fill="#5c2e0e" opacity="0.3"/>
  {score_poly}
  {score_points}
  {score_labels}
  {labels}
  {center_text}
</svg>'''
    return svg

