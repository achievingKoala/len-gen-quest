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
        choice_count = data.get('choice_count', 1)
        fill_count = data.get('fill_count', 1)
        
        if not text_content.strip():
            return jsonify({'error': '文本内容不能为空'}), 400
        
        # 生成题目和主题
        result = generate_questions(text_content, choice_count, fill_count)
        
        # 保存当前题目到全局变量
        global current_questions
        current_questions = result['questions']
        
        return jsonify({
            'success': True,
            'questions': result['questions'],
            'topic': result['topic'],
            'text_length': len(text_content)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_questions(text, choice_count=1, fill_count=1):
    """生成题目和主题的核心函数"""
    client = OpenAI(
        base_url=os.getenv('OPENAI_BASE_URL'),
        api_key=os.getenv('OPENAI_API_KEY'),
    )
    
    total_count = choice_count + fill_count
    
    prompt = f"""
基于以下文本内容，生成一个主题和{total_count}道练习题（{choice_count}道选择题，{fill_count}道填空题）。

文本内容：
{text}

请按以下JSON格式返回：
{{
  "topic": "文本的主要主题（简洁概括）",
  "questions": [
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
}}
"""
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        )
        
        content = response.choices[0].message.content
        # 提取JSON内容，去除markdown格式
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        result = json.loads(content)
        return result
    except Exception as e:
        print(f"AI调用失败: {e}")
        # 如果AI调用失败，返回默认题目和主题
        default_questions = []
        question_id = 1
        
        # 生成选择题
        for i in range(choice_count):
            default_questions.append({
                'id': question_id,
                'type': 'multiple_choice',
                'question': f'根据文本内容，以下哪个说法正确？（题目{question_id}）',
                'options': ['选项A', '选项B', '选项C', '选项D'],
                'correct_answer': 0
            })
            question_id += 1
        
        # 生成填空题
        for i in range(fill_count):
            default_questions.append({
                'id': question_id,
                'type': 'fill_blank',
                'question': f'请填空：文本中提到的关键概念是______。（题目{question_id}）',
                'correct_answer': '关键词'
            })
            question_id += 1
            
        return {
            'topic': '文本学习',
            'questions': default_questions
        }

# 存储当前题目数据
current_questions = []

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        user_answer = data.get('answer')
        
        # 查找对应题目
        question = next((q for q in current_questions if q['id'] == int(question_id)), None)
        if not question:
            return jsonify({'error': '题目不存在'}), 400
        
        # 验证答案
        correct_answer = question['correct_answer']
        is_correct = False
        
        if question['type'] == 'multiple_choice':
            is_correct = user_answer == correct_answer
        elif question['type'] == 'fill_blank':
            is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer,
            'user_answer': user_answer
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)