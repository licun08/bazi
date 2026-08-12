"""
BaZi AI - Chinese Four Pillars Astrology
Flask web application with DeepSeek-powered readings.
"""
import os
import sys
import io
import base64
import zlib
from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

# ── Fix paths for Vercel serverless ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

from bazi_calc import BaZiEngine, format_result_for_api
from interpreter import get_reading, is_configured
from solar_time import compute_adjusted_birth_time, search_city
from compatibility import analyze as compat_analyze
from bazi_scores import compute_scores, generate_hex_svg

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
engine = BaZiEngine()

FONT_PATH = os.path.join(BASE_DIR, 'static', 'simhei.ttf')


def _load_font(size: int):
    """Load the bundled Chinese font, fall back to default if missing."""
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def get_lang():
    return request.args.get('lang', 'zh')

def _decode_share_data(data: str):
    """Decode a compressed AI reading embedded in a share URL."""
    if not data:
        return None
    try:
        raw = base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))
        return zlib.decompress(raw).decode('utf-8')
    except Exception:
        return None


def markdown_to_html(text: str) -> str:
    """Convert simple markdown formatting to HTML tags."""
    import re
    # Headings are handled by the template
    
    # Bold: **text** -> <strong>text</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic: *text* -> <em>text</em> (but not ** which is bold)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # List items: - text -> bullet points
    text = re.sub(r'^- (.+)', r'• \1', text, flags=re.MULTILINE)
    return text


@app.route('/')
def index():
    lang = get_lang()
    return render_template('index.html', lang=lang, api_configured=is_configured())

@app.route('/search_city')
def city_search():
    """AJAX endpoint for city autocomplete."""
    q = request.args.get('q', '')
    results = search_city(q)
    return jsonify(results[:10])

@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    # Support both form POST and shareable GET URLs
    g = request.form if request.method == 'POST' else request.args
    lang = g.get('lang', 'zh')
    share_data = g.get('share_data', '')
    try:
        year = int(g['year'])
        month = int(g['month'])
        day = int(g['day'])
        hour = int(g['hour'])
        minute = int(g.get('minute', 0))
        gender = g.get('gender', 'male')
        city = g.get('city', '').strip()

        # Original clock time
        dt = datetime(year, month, day, hour, minute)

        # True solar time correction (uses full adjusted datetime incl. cross-day date)
        adjusted_dt = dt
        solar_info = None
        if city:
            adj = compute_adjusted_birth_time(year, month, day, hour, minute, city)
            if adj['city_found']:
                adjusted_dt = adj['adjusted_datetime']
                solar_info = adj['correction']
        
        # Calculate BaZi using ADJUSTED time
        result = engine.calculate(adjusted_dt)
        formatted = engine.get_formatted_pillars(result)
        bazi_data = format_result_for_api(result, formatted, dt)
        bazi_data['gender'] = gender

        # Compute entertainment scores (deterministic, no API needed)
        scores = compute_scores(bazi_data, lang=lang)
        hex_svg = generate_hex_svg(scores, lang=lang)

        # Share mode:
        #   'full'  = chart + AI reading (form POST, or GET with embedded reading)
        #   'chart' = chart only (GET share link without embedded reading)
        share_mode = 'full'
        reading = None
        if share_data:
            cached = _decode_share_data(share_data)
            if cached is not None:
                reading = cached
            else:
                share_mode = 'chart'
        elif request.method == 'GET':
            share_mode = 'chart'

        if reading is None and share_mode == 'full':
            reading = get_reading(bazi_data, lang=lang)

        reading_html = markdown_to_html(reading) if reading else ''

        return render_template('result.html',
                             bazi=bazi_data,
                             reading=reading_html,
                             scores=scores,
                             hex_svg=hex_svg,
                             lang=lang,
                             solar_info=solar_info,
                             city=city,
                             birth_input={
                                 'year': year, 'month': month, 'day': day,
                                 'hour': hour, 'minute': minute,
                                 'gender': gender, 'city': city, 'lang': lang,
                             },
                             share_mode=share_mode,
                             share_reading=reading or '',
                             api_configured=is_configured())
        
    except ValueError as e:
        return render_template('index.html', 
                             error=f"Invalid date/time: {str(e)}",
                             lang=lang,
                             api_configured=is_configured())
    except Exception as e:
        return render_template('index.html', 
                             error=f"Error: {str(e)}",
                             lang=lang,
                             api_configured=is_configured())

@app.route('/og-image')
def og_image():
    """Generate a 1200x630 share-card image for a BaZi chart (used by og:image)."""
    g = request.args
    lang = g.get('lang', 'zh')
    try:
        year = int(g['year'])
        month = int(g['month'])
        day = int(g['day'])
        hour = int(g.get('hour', 12))
        minute = int(g.get('minute', 0))
        gender = g.get('gender', 'male')
        city = g.get('city', '').strip()

        dt = datetime(year, month, day, hour, minute)
        adjusted_dt = dt
        if city:
            adj = compute_adjusted_birth_time(year, month, day, hour, minute, city)
            if adj['city_found']:
                adjusted_dt = adj['adjusted_datetime']

        result = engine.calculate(adjusted_dt)
        formatted = engine.get_formatted_pillars(result)
        bazi_data = format_result_for_api(result, formatted, dt)
        bazi_data['gender'] = gender
        scores = compute_scores(bazi_data, lang=lang)
    except Exception:
        return '', 400

    W, H = 1200, 630
    img = Image.new('RGB', (W, H), '#f5f0e8')
    d = ImageDraw.Draw(img)

    # ── Frames ──
    d.rectangle([24, 24, W - 24, H - 24], outline='#8b4513', width=3)
    d.rectangle([36, 36, W - 36, H - 36], outline='#c8a878', width=1)

    # ── Title ──
    f_title = _load_font(56)
    title = '八字命盘 · AI 解读' if lang == 'zh' else 'BaZi Chart · AI Reading'
    d.text((W // 2, 92), title, font=f_title, fill='#5c2e0e', anchor='mm')

    f_sub = _load_font(30)
    sub = f"生肖 {bazi_data['year_animal']} · {bazi_data['baZi']}"
    d.text((W // 2, 152), sub, font=f_sub, fill='#8b7355', anchor='mm')

    # ── Four pillars ──
    pillar_keys = ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']
    labels_cn = ['年 柱', '月 柱', '日 柱', '时 柱']
    labels_en = ['YEAR', 'MONTH', 'DAY', 'HOUR']
    box_w, box_h = 230, 240
    xs = [105, 358, 611, 864]
    top = 185
    f_label = _load_font(26)
    f_char = _load_font(74)
    f_shi = _load_font(26)

    for i, key in enumerate(pillar_keys):
        p = bazi_data['pillars'][key]
        x = xs[i]
        is_day = key == 'day_pillar'
        fill = '#fff8eb' if is_day else '#fffdf8'
        d.rectangle([x, top, x + box_w, top + box_h], fill=fill,
                    outline='#8b2500' if is_day else '#8b4513', width=2)
        label = labels_cn[i] if lang == 'zh' else labels_en[i]
        d.text((x + box_w // 2, top + 36), label, font=f_label, fill='#b8a88a', anchor='mm')
        d.text((x + box_w // 2, top + 110), f"{p['stem']}{p['branch']}",
               font=f_char, fill='#8b2500' if is_day else '#5c2e0e', anchor='mm')
        d.text((x + box_w // 2, top + 205), p['shi_shen'].split(' (')[0],
               font=f_shi, fill='#8b4513', anchor='mm')

    # ── Day master + score row ──
    f_dm = _load_font(36)
    dm = bazi_data['day_master']
    dm_text = f"日主 {dm['stem']}（{dm['element']} · {dm['yinyang']}）"
    d.text((W // 2, 468), dm_text, font=f_dm, fill='#2c2416', anchor='mm')

    f_score = _load_font(40)
    score_text = f"综合评分 {scores['composite']} / 100 · {scores['title']}"
    d.text((W // 2, 528), score_text, font=f_score, fill='#5c2e0e', anchor='mm')

    # ── Footer ──
    f_foot = _load_font(28)
    d.text((W // 2, 588), 'www.bzmli.com', font=f_foot, fill='#b8a88a', anchor='mm')

    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    resp = make_response(buf.getvalue())
    resp.headers['Content-Type'] = 'image/png'
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp


@app.route('/api/v1/reading', methods=['POST'])
def api_reading():
    try:
        data = request.get_json()
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data.get('hour', 12))
        minute = int(data.get('minute', 0))
        lang = data.get('lang', 'en')
        city = data.get('city', '')
        
        dt = datetime(year, month, day, hour, minute)
        if city:
            adj = compute_adjusted_birth_time(year, month, day, hour, minute, city)
            if adj['city_found']:
                dt = datetime(year, month, day, adj['adjusted_hour'], adj['adjusted_minute'])
        
        result = engine.calculate(dt)
        formatted = engine.get_formatted_pillars(result)
        bazi_data = format_result_for_api(result, formatted, 
            datetime(year, month, day, hour, minute))
        reading = get_reading(bazi_data, lang=lang)
        
        return jsonify({
            'success': True,
            'bazi': bazi_data,
            'reading': reading,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


@app.route('/compatibility', methods=['GET', 'POST'])
def compatibility():
    lang = get_lang()
    if request.method == 'GET':
        return render_template('compatibility.html', lang=lang, api_configured=is_configured())
    
    # POST - calculate both charts
    try:
        year1 = int(request.form['year1'])
        month1 = int(request.form['month1'])
        day1 = int(request.form['day1'])
        hour1 = int(request.form.get('hour1', 12))
        gender1 = request.form.get('gender1', 'male')
        
        year2 = int(request.form['year2'])
        month2 = int(request.form['month2'])
        day2 = int(request.form['day2'])
        hour2 = int(request.form.get('hour2', 12))
        gender2 = request.form.get('gender2', 'female')
        
        dt1 = datetime(year1, month1, day1, hour1, 0)
        dt2 = datetime(year2, month2, day2, hour2, 0)
        
        # Calculate both charts
        from interpreter import get_compatibility_reading
        
        r1 = engine.calculate(dt1)
        f1 = engine.get_formatted_pillars(r1)
        bazi1 = format_result_for_api(r1, f1, dt1)
        bazi1['gender'] = gender1
        
        r2 = engine.calculate(dt2)
        f2 = engine.get_formatted_pillars(r2)
        bazi2 = format_result_for_api(r2, f2, dt2)
        bazi2['gender'] = gender2
        
        # Compatibility analysis
        compat = compat_analyze(bazi1, bazi2, gender1, gender2)
        reading = get_compatibility_reading(bazi1, bazi2, compat, gender1, gender2, lang)
        reading_html = markdown_to_html(reading)
        
        return render_template('compatibility_result.html',
                             bazi1=bazi1, bazi2=bazi2,
                             compat=compat,
                             reading=reading_html,
                             lang=lang,
                             api_configured=is_configured())
        
    except Exception as e:
        return render_template('compatibility.html',
                             error=str(e),
                             lang=lang,
                             api_configured=is_configured())


@app.route('/bazi-vs-western-astrology')
def guide_bazi_vs_western():
    return render_template('guide_bazi_vs_western.html')


@app.route('/five-elements')
def guide_elements():
    return render_template('guide_elements.html')


@app.route('/robots.txt')
def robots():
    return '''User-agent: *
Allow: /
Sitemap: https://www.bzmli.com/sitemap.xml
''', 200, {'Content-Type': 'text/plain'}


@app.route('/sitemap.xml')
def sitemap():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.bzmli.com/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://www.bzmli.com/compatibility</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.bzmli.com/bazi-vs-western-astrology</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.bzmli.com/five-elements</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>
''', 200, {'Content-Type': 'application/xml'}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8899))
    print(f"✨ BaZi AI running at http://127.0.0.1:{port}")
    print(f"🔮 DeepSeek API: {'Configured ✅' if is_configured() else 'NOT configured ⚠️'}")
    app.run(host='127.0.0.1', port=port, debug=True)
