"""
BaZi AI - Chinese Four Pillars Astrology
Flask web application with DeepSeek-powered readings.
"""
import os
import sys
from flask import Flask, render_template, request, jsonify
from datetime import datetime

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

def get_lang():
    return request.args.get('lang', 'zh')

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

@app.route('/calculate', methods=['POST'])
def calculate():
    lang = request.form.get('lang', 'zh')
    try:
        year = int(request.form['year'])
        month = int(request.form['month'])
        day = int(request.form['day'])
        hour = int(request.form['hour'])
        minute = int(request.form.get('minute', 0))
        gender = request.form.get('gender', 'male')
        city = request.form.get('city', '').strip()
        
        # Original clock time
        dt = datetime(year, month, day, hour, minute)
        
        # True solar time correction
        adjusted_dt = dt
        solar_info = None
        if city:
            adj = compute_adjusted_birth_time(year, month, day, hour, minute, city)
            if adj['city_found']:
                adjusted_dt = datetime(year, month, day, adj['adjusted_hour'], adj['adjusted_minute'])
                solar_info = adj['correction']
        
        # Calculate BaZi using ADJUSTED time
        result = engine.calculate(adjusted_dt)
        formatted = engine.get_formatted_pillars(result)
        bazi_data = format_result_for_api(result, formatted, dt)
        bazi_data['gender'] = gender
        
        reading = get_reading(bazi_data, lang=lang)
        reading_html = markdown_to_html(reading)

        # Compute entertainment scores
        scores = compute_scores(bazi_data, lang=lang)
        hex_svg = generate_hex_svg(scores, lang=lang)

        return render_template('result.html',
                             bazi=bazi_data,
                             reading=reading_html,
                             scores=scores,
                             hex_svg=hex_svg,
                             lang=lang,
                             solar_info=solar_info,
                             city=city,
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

@app.route('/api/v1/reading', methods=['POST'])
def api_reading():
    try:
        data = request.get_json()
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data.get('hour', 12))
        minute = int(data.get('minute', 0))
        lang = data.get('lang', 'zh')
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8899))
    print(f"✨ BaZi AI running at http://127.0.0.1:{port}")
    print(f"🔮 DeepSeek API: {'Configured ✅' if is_configured() else 'NOT configured ⚠️'}")
    app.run(host='127.0.0.1', port=port, debug=True)
