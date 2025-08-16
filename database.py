import sqlite3
import json
from datetime import datetime

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('questions.db')
    
    # 创建或更新question_sets表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS question_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            FOREIGN KEY (set_id) REFERENCES question_sets (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS answer_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            user_answer TEXT,
            is_correct BOOLEAN,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (set_id) REFERENCES question_sets (id)
        )
    ''')
    conn.commit()
    conn.close()

def save_single_question(question_data, topic, user_id):
    """保存单个题目到现有或新建题目集"""
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    # 查找现有题目集（按用户ID）
    cursor.execute('SELECT id FROM question_sets WHERE topic = ? AND user_id = ?', (topic, user_id))
    result = cursor.fetchone()
    
    if result:
        set_id = result[0]
        # 获取下一个题目序号
        cursor.execute('SELECT MAX(question_id) FROM questions WHERE set_id = ?', (set_id,))
        max_id = cursor.fetchone()[0] or 0
        next_question_id = max_id + 1
    else:
        # 创建新题目集
        cursor.execute('INSERT INTO question_sets (topic, user_id) VALUES (?, ?)', (topic, user_id))
        set_id = cursor.lastrowid
        next_question_id = 1
    
    # 保存题目
    options = json.dumps(question_data.get('options')) if question_data.get('options') else None
    explanation = question_data.get('explanation', '')
    cursor.execute('''
        INSERT INTO questions (set_id, question_id, type, question, options, correct_answer, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (set_id, next_question_id, question_data['type'], question_data['question'], 
          options, str(question_data['correct_answer']), explanation))
    
    conn.commit()
    conn.close()
    return set_id

def save_selected_questions(questions_list, selected_ids, title, user_id):
    """保存选中的题目"""
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    # 创建题目集
    cursor.execute('INSERT INTO question_sets (topic, user_id) VALUES (?, ?)', (title, user_id))
    set_id = cursor.lastrowid
    
    # 保存选中题目
    for i, question_id in enumerate(selected_ids):
        question = next((q for q in questions_list if q['id'] == int(question_id)), None)
        if question:
            options = json.dumps(question.get('options')) if question.get('options') else None
            explanation = question.get('explanation', '')
            cursor.execute('''
                INSERT INTO questions (set_id, question_id, type, question, options, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (set_id, i + 1, question['type'], question['question'], 
                  options, str(question['correct_answer']), explanation))
    
    conn.commit()
    conn.close()
    return set_id, len(selected_ids)

def get_question_sets(user_id):
    """获取题目集列表（按用户ID）"""
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT qs.id, qs.topic, qs.created_at, COUNT(q.id) as question_count
        FROM question_sets qs
        LEFT JOIN questions q ON qs.id = q.set_id
        WHERE qs.user_id = ?
        GROUP BY qs.id
        ORDER BY qs.created_at DESC
    ''', (user_id,))
    
    sets = []
    for row in cursor.fetchall():
        sets.append({
            'id': row[0],
            'topic': row[1],
            'created_at': row[2],
            'question_count': row[3]
        })
    
    conn.close()
    return sets

def load_question_set(set_id, user_id):
    """加载题目集（验证用户权限）"""
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    # 获取题目集信息（验证用户权限）
    cursor.execute('SELECT topic FROM question_sets WHERE id = ? AND user_id = ?', (set_id, user_id))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return None, None
    
    topic = result[0]
    
    # 获取题目
    cursor.execute('''
        SELECT question_id, type, question, options, correct_answer, explanation
        FROM questions WHERE set_id = ? ORDER BY question_id
    ''', (set_id,))
    
    questions = []
    for row in cursor.fetchall():
        q = {
            'id': row[0],
            'type': row[1],
            'question': row[2],
            'correct_answer': int(row[4]) if row[1] == 'multiple_choice' else row[4],
            'explanation': row[5] or ''
        }
        if row[3]:
            q['options'] = json.loads(row[3])
        questions.append(q)
    
    conn.close()
    return topic, questions