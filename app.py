from flask import Flask, render_template, request, jsonify, session
import json
import os
import uuid
import logging
import traceback
from openai import OpenAI
from dotenv import load_dotenv
from database import init_db, save_single_question, save_selected_questions, get_question_sets, load_question_set, save_answer_record, get_wrong_questions

load_dotenv()


# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.permanent_session_lifetime = 86400 * 365  # 1年

# 初始化数据库
init_db()

def get_user_id():
    """获取或创建用户ID"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session.permanent = True  # 设置为永久session
    return session['user_id']

@app.route('/')
def index():
    get_user_id()  # 确保用户有ID
    load_id = request.args.get('load')
    if load_id:
        return render_template('index.html', load_id=load_id)
    return render_template('index.html')

@app.route('/question_sets_page')
def question_sets_page():
    return render_template('question_sets.html')

@app.route('/wrong_questions_page')
def wrong_questions_page():
    return render_template('wrong_questions.html')

@app.route('/wrong_questions')
def get_wrong_questions_api():
    try:
        user_id = get_user_id()
        wrong_questions = get_wrong_questions(user_id)
        return jsonify({'questions': wrong_questions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_text', methods=['POST'])
def upload_text():
    try:
        logger.info("开始处理文本上传请求")
        data = request.get_json()
        text_content = data.get('text', '')
        choice_count = data.get('choice_count', 1)
        fill_count = data.get('fill_count', 1)
        
        logger.info(f"文本长度: {len(text_content)}, 选择题: {choice_count}, 填空题: {fill_count}")
        
        if not text_content.strip():
            logger.warning("文本内容为空")
            return jsonify({'error': '文本内容不能为空'}), 400
        
        # 生成题目和主题
        result = generate_questions(text_content, choice_count, fill_count)
        
        logger.info("题目生成成功")
        # 不存session，直接返回
        return jsonify({
            'success': True,
            'questions': result['questions'],
            'topic': result['topic'],
            'text_length': len(text_content)
        })
    
    except Exception as e:
        logger.error(f"处理文本上传时发生错误: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

def generate_questions(text, choice_count=1, fill_count=1):
    """生成题目和主题的核心函数"""
    client = OpenAI(
        base_url=os.getenv('OPENAI_BASE_URL'),
        api_key=os.getenv('OPENAI_API_KEY')
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
      "correct_answer": 0,
      "explanation": "答案解释说明"
    }},
    {{
      "id": 2,
      "type": "fill_blank",
      "question": "填空题内容，用______表示空白",
      "correct_answer": "正确答案",
      "explanation": "答案解释说明"
    }}
  ]
}}
"""
    
    try:
        logger.info("开始调用AI生成题目")
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        )
        
        content = response.choices[0].message.content
        logger.info(f"AI返回内容长度: {len(content)}")
        
        # 提取JSON内容，去除markdown格式
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        result = json.loads(content)
        logger.info("AI题目生成成功")
        return result
    except Exception as e:
        logger.error(f"AI调用失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
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
                'correct_answer': 0,
                'explanation': '请参考文本内容进行理解'
            })
            question_id += 1
        
        # 生成填空题
        for i in range(fill_count):
            default_questions.append({
                'id': question_id,
                'type': 'fill_blank',
                'question': f'请填空：文本中提到的关键概念是______。（题目{question_id}）',
                'correct_answer': '关键词',
                'explanation': '请参考文本内容进行理解'
            })
            question_id += 1
            
        return {
            'topic': '文本学习',
            'questions': default_questions
        }





@app.route('/save_single_question', methods=['POST'])
def save_single_question_api():
    try:
        data = request.get_json()
        question_data = data.get('question')
        topic = data.get('topic', '单个题目')
        user_id = get_user_id()
        
        if not question_data:
            return jsonify({'error': '题目数据不能为空'}), 400
        
        set_id = save_single_question(question_data, topic, user_id)
        return jsonify({'success': True, 'set_id': set_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_selected_questions', methods=['POST'])
def save_selected_questions_api():
    try:
        data = request.get_json()
        selected_questions = data.get('selected_questions', [])
        title = data.get('title', '未命名题目集')
        user_id = get_user_id()
        
        if not selected_questions:
            return jsonify({'error': '请选择题目'}), 400
        
        set_id, count = save_selected_questions(selected_questions, None, title, user_id)
        return jsonify({'success': True, 'set_id': set_id, 'count': count})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/question_sets')
def list_question_sets():
    try:
        user_id = get_user_id()
        sets = get_question_sets(user_id)
        return jsonify({'sets': sets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_questions/<int:set_id>')
def load_questions(set_id):
    try:
        user_id = get_user_id()
        
        topic, questions = load_question_set(set_id, user_id)
        if not topic:
            return jsonify({'error': '题目集不存在或无权限访问'}), 404
        
        return jsonify({
            'success': True,
            'questions': questions,
            'topic': topic
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_answer', methods=['POST'])
def save_answer():
    try:
        data = request.get_json()
        set_id = data.get('set_id')
        question_id = data.get('question_id')
        user_answer = data.get('user_answer')
        is_correct = data.get('is_correct')
        
        if set_id and question_id is not None:
            save_answer_record(set_id, question_id, user_answer, is_correct)
            return jsonify({'success': True})
        else:
            return jsonify({'error': '参数不完整'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 全局错误处理器
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"未捕获的异常: {str(e)}")
    logger.error(f"错误详情: {traceback.format_exc()}")
    return jsonify({'error': '服务器内部错误', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)