"""
DeepSeek-powered interpretation of BaZi readings (multi-language).
"""
import os
import json
import requests

def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip())

_load_env()

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

SYSTEM_PROMPTS = {
    'en': """You are a master of Chinese BaZi (Four Pillars of Destiny) astrology. You provide insightful, nuanced readings in English that are:
- Accessible to Western audiences who are new to Chinese metaphysics
- Accurate in terminology (using correct Chinese terms with English explanations)
- Focused on practical life guidance, not fatalistic predictions
- Balanced, mentioning both strengths and areas of growth
- Respectful of the tradition without being superstitious or overly vague

Structure your reading in clear sections with markdown formatting.""",

    'zh': """你是一位精通八字命理的解读师。请用中文为用户提供专业、有深度的命理分析。

你的分析应该：
- 自然平实，不要堆砌术语
- 平衡优缺点，既说天赋也说盲点
- 聚焦性格、事业、感情、人生阶段等实际层面
- 给出具体实用的建议
- 避免套话和模糊表述
- 语气像一位有洞察力的朋友，而不是算命先生

用 markdown 格式组织内容，分小节呈现。""",
}

SECTION_NAMES = {
    'en': ['Core Element Profile', 'Personality & Character', 'Career & Life Path', 'Relationships & Social Dynamics', 'Lucky Elements & Guidance', 'Life Seasons & Timing'],
    'zh': ['日主核心分析', '性格特征', '事业与人生路径', '人际关系', '喜用神与建议', '人生阶段与时机'],
}

def build_prompt(bazi_data: dict, lang: str = 'en') -> str:
    pillars = bazi_data['pillars']
    
    if lang == 'zh':
        prompt = f"""## 出生信息
- 出生时间: {bazi_data['birth_datetime']}
- 生肖: {bazi_data['year_animal']}

## 八字排盘结果

### 日主
- 天干: {bazi_data['day_master']['stem']}（{bazi_data['day_master']['element']}，{bazi_data['day_master']['yinyang']}）
- 日主代表命主自身，此人的核心五行是{bazi_data['day_master']['element']}（{bazi_data['day_master']['yinyang']}）。

### 四柱

"""
        for k, v in pillars.items():
            prompt += f"""**{v['label']}**: {v['stem']}{v['branch']}
- 天干: {v['stem']}（{v['stem_en']}）— 五行: {v['stem_element']}，{v['stem_yinyang']}
- 地支: {v['branch']}（{v['branch_en']}）— 生肖: {v['branch_animal']} — 五行: {v['branch_element']}
- 与日主关系（十神）: {v['shi_shen']}

"""
        
        prompt += """请根据以上八字信息，用中文撰写一份命理分析报告，包含以下六个部分：

## 1. 日主核心分析
解释日主的五行属性及其意义。

## 2. 性格特征
基于四柱组合分析性格特点，既要说到优势也要说到盲点。

## 3. 事业与人生路径
分析适合的工作方向和人生走势。

## 4. 人际关系
分析感情、社交等方面的倾向。

## 5. 实用建议
哪些元素对你有利，哪些需要注意。颜色、环境、习惯等方面。

## 6. 人生阶段与时机
综合判断人生各个阶段的趋势。

控制在600-1000字。自然平实，有洞察力。"""
    else:
        prompt = f"""## Birth Information
- Birth Date & Time: {bazi_data['birth_datetime']}
- Chinese Zodiac Animal: {bazi_data['year_animal']}

## BaZi (Four Pillars) Calculation

### Day Master (日主)
- Stem: {bazi_data['day_master']['stem']} ({bazi_data['day_master']['element']}, {bazi_data['day_master']['yinyang']})
- The Day Master represents the self. This person's core element is {bazi_data['day_master']['element']} ({bazi_data['day_master']['yinyang']}).

### The Four Pillars

"""
        for k, v in pillars.items():
            prompt += f"""**{v['label']}**: {v['stem']}{v['branch']}
- Heavenly Stem: {v['stem']} ({v['stem_en']}) — Element: {v['stem_element']}
- Earthly Branch: {v['branch']} ({v['branch_en']}) — Animal: {v['branch_animal']} — Element: {v['branch_element']}
- Relationship to Day Master (十神): {v['shi_shen']}

"""
        
        prompt += """Please provide a complete BaZi reading in the following format:

## 1. Core Element Profile
Explain the Day Master's element and its significance.

## 2. Personality & Character
Based on the pillar interactions, describe the person's character traits.

## 3. Career & Life Path
Analyze the career implications of the pillar combinations.

## 4. Relationships & Social Dynamics
Based on the relationship stems (十神) in each pillar.

## 5. Lucky Elements & Guidance
Which elements are beneficial and which are challenging.

## 6. Life Seasons & Timing
General guidance based on the pillar energies.

Keep the reading around 500-800 words. Focus on being insightful and personalized rather than generic."""
    
    return prompt


def get_reading(bazi_data: dict, lang: str = 'en') -> str:
    if not DEEPSEEK_API_KEY:
        msg = {
            'en': "⚠️ **DeepSeek API key not configured.**\n\nSet your DEEPSEEK_API_KEY.",
            'zh': "⚠️ **DeepSeek API 密钥未配置。**\n\n请在 .env 文件中设置 DEEPSEEK_API_KEY。"
        }
        return msg.get(lang, msg['en'])
    
    prompt = build_prompt(bazi_data, lang)
    system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS['en'])
    
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.7,
        'max_tokens': 3000,
    }
    
    try:
        resp = requests.post(
            f'{DEEPSEEK_BASE_URL}/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return "⚠️ **Request timed out.** DeepSeek API did not respond."
    except requests.exceptions.HTTPError as e:
        return f"⚠️ **API Error ({resp.status_code}):** {str(e)}"
    except Exception as e:
        return f"⚠️ **Error generating reading:** {str(e)}"


def get_compatibility_reading(bazi1: dict, bazi2: dict, compat: dict, gender1: str = 'male', gender2: str = 'female', lang: str = 'zh') -> str:
    """Generate a compatibility reading using DeepSeek."""
    if not DEEPSEEK_API_KEY:
        return "API key not configured."
    
    if lang == 'zh':
        prompt = f"""请根据以下两个人的八字信息，撰写一份合婚分析报告。

## 第一人信息
- 出生时间: {bazi1['birth_datetime']}
- 生肖: {bazi1['year_animal']}
- 日主: {bazi1['day_master']['stem']}（{bazi1['day_master']['element']}，{bazi1['day_master']['yinyang']}）
- 八字: {bazi1['baZi']}

"""
        for k, v in bazi1['pillars'].items():
            prompt += f"- {v['label']}: {v['stem']}{v['branch']}（{v['stem_en']}{v['branch_en']}，{v['branch_animal']}）→ {v['shi_shen']}\n"

        prompt += f"""
## 第二人信息
- 出生时间: {bazi2['birth_datetime']}
- 生肖: {bazi2['year_animal']}
- 日主: {bazi2['day_master']['stem']}（{bazi2['day_master']['element']}，{bazi2['day_master']['yinyang']}）
- 八字: {bazi2['baZi']}

"""
        for k, v in bazi2['pillars'].items():
            prompt += f"- {v['label']}: {v['stem']}{v['branch']}（{v['stem_en']}{v['branch_en']}，{v['branch_animal']}）→ {v['shi_shen']}\n"

        prompt += f"""
## 合婚结果
- 生肖配对: {compat['zodiac']['animal1']} + {compat['zodiac']['animal2']}（{compat['zodiac']['desc']}）
- 日主关系: {compat['day_master']['desc']}
- 综合评分: {compat['score']}分（{compat['verdict']}）

请根据以上八字信息，写一份合婚分析报告，包含：

1. 整体评价：两人的缘分如何
2. 性格匹配：性格是否互补
3. 优势之处：合在哪里
4. 注意事项：冲克在哪里，如何化解
5. 综合建议

语气专业温和，用中文。600-1000字。"""
    else:
        prompt = f"""Please analyze the compatibility between these two people based on their BaZi (Four Pillars) charts.

## Person 1
- Birth: {bazi1['birth_datetime']}
- Zodiac: {bazi1['year_animal']}
- Day Master: {bazi1['day_master']['stem']} ({bazi1['day_master']['element']}, {bazi1['day_master']['yinyang']})
- BaZi: {bazi1['baZi']}

"""
        for k, v in bazi1['pillars'].items():
            prompt += f"- {v['label']}: {v['stem']}{v['branch']} → {v['shi_shen']}\n"

        prompt += f"""
## Person 2
- Birth: {bazi2['birth_datetime']}
- Zodiac: {bazi2['year_animal']}
- Day Master: {bazi2['day_master']['stem']} ({bazi2['day_master']['element']}, {bazi2['day_master']['yinyang']})
- BaZi: {bazi2['baZi']}

"""
        for k, v in bazi2['pillars'].items():
            prompt += f"- {v['label']}: {v['stem']}{v['branch']} → {v['shi_shen']}\n"

        prompt += f"""
## Compatibility Analysis
- Zodiac match: {compat['zodiac']['animal1']} + {compat['zodiac']['animal2']} ({compat['zodiac']['desc']})
- Element relationship: {compat['day_master']['desc']}
- Overall score: {compat['score']} ({compat['verdict_en']})

Write a compatibility reading covering:
1. Overall assessment
2. Personality fit
3. Strengths of this match
4. Potential challenges
5. Practical advice

Natural, insightful English. 400-700 words."""

    system = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS['en'])
    
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.7,
        'max_tokens': 3000,
    }
    
    try:
        resp = requests.post(
            f'{DEEPSEEK_BASE_URL}/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


def is_configured() -> bool:
    return bool(DEEPSEEK_API_KEY)
