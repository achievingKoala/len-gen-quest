from flask import Flask, render_template, request, jsonify
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_text', methods=['POST'])
def upload_text():
    try:
        data = request.get_json()
        text_content = data.get('text', '')
        
        if not text_content.strip():
            return jsonify({'error': '文本内容不能为空'}), 400
        
        # 生成题目 (这里先返回模拟数据，后续可接入AI)
        questions = generate_questions(text_content)
        
        return jsonify({
            'success': True,
            'questions': questions,
            'text_length': len(text_content)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_questions(text):
    """生成题目的核心函数"""
    client = OpenAI(
        base_url=os.getenv('OPENAI_BASE_URL'),
        api_key=os.getenv('OPENAI_API_KEY'),
    )
    
    prompt = f"""
基于以下文本内容，生成2道练习题（1道选择题，1道填空题）。

文本内容：
{text}

请按以下JSON格式返回：
[
  {{
    "id": 1,
    "type": "multiple_choice",
    "question": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": 0
  }},
  {{
    "id": 2,
    "type": "fill_blank",
    "question": "填空题内容，用______表示空白",
    "correct_answer": "正确答案"
  }}
]
"""
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        )
        
        content = response.choices[0].message.content
        questions = json.loads(content)
        return questions
    except Exception as e:
        # 如果AI调用失败，返回默认题目
        return [
            {
                'id': 1,
                'type': 'multiple_choice',
                'question': '根据文本内容，以下哪个说法正确？',
                'options': ['选项A', '选项B', '选项C', '选项D'],
                'correct_answer': 0
            },
            {
                'id': 2,
                'type': 'fill_blank',
                'question': '请填空：文本中提到的关键概念是______。',
                'correct_answer': '关键词'
            }
        ]

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        user_answer = data.get('answer')
        
        # 这里可以添加答案验证逻辑
        is_correct = True  # 简化处理
        
        return jsonify({
            'correct': is_correct,
            'explanation': '答案解析...'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)