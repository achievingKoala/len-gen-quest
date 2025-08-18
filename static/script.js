class QuizApp {
    constructor() {
        this.questions = [];
        this.userAnswers = {};
        this.selectedQuestions = new Set();
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkLoadParam();
    }

    checkLoadParam() {
        const urlParams = new URLSearchParams(window.location.search);
        const loadId = urlParams.get('load');
        if (loadId) {
            this.loadQuestionSet(parseInt(loadId));
        }
    }

    bindEvents() {
        document.getElementById('file-btn').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });

        document.getElementById('file-input').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files[0]);
        });

        document.getElementById('generate-btn').addEventListener('click', () => {
            this.generateQuestions();
        });

        document.getElementById('submit-quiz').addEventListener('click', () => {
            this.submitQuiz();
        });

        document.getElementById('reset-quiz').addEventListener('click', () => {
            this.resetQuiz();
        });

        document.getElementById('select-all-btn').addEventListener('click', () => {
            this.toggleSelectAll();
        });

        document.getElementById('save-selected-btn').addEventListener('click', () => {
            this.saveSelectedQuestions();
        });

        document.getElementById('load-questions-btn').addEventListener('click', () => {
            this.showLoadDialog();
        });
    }

    async handleFileUpload(file) {
        if (!file) return;
        
        const text = await file.text();
        document.getElementById('text-input').value = text;
    }

    async generateQuestions() {
        const textContent = document.getElementById('text-input').value.trim();
        const choiceCount = parseInt(document.getElementById('choice-count').value);
        const fillCount = parseInt(document.getElementById('fill-count').value);
        
        if (!textContent) {
            alert('请先输入或上传文本内容');
            return;
        }

        this.showLoading('正在生成题目...');

        try {
            const response = await fetch('/upload_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text: textContent,
                    choice_count: choiceCount,
                    fill_count: fillCount
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.questions = data.questions;
                this.topic = data.topic;
                this.selectedQuestions.clear();
                this.displayQuestions();
            } else {
                alert('生成题目失败: ' + data.error);
            }
        } catch (error) {
            alert('网络错误: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayQuestions() {
        const container = document.getElementById('questions-container');
        container.innerHTML = '';
        
        // 显示主题
        if (this.topic) {
            const topicDiv = document.createElement('div');
            topicDiv.className = 'topic-header';
            topicDiv.innerHTML = `
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2196f3;">
                    <h3 style="margin: 0; color: #1976d2;">📖 学习主题</h3>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #424242;">${this.topic}</p>
                </div>
            `;
            container.appendChild(topicDiv);
        }

        this.questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question';
            questionDiv.style.position = 'relative';
            
            // 添加控制按钮
            const controlsHtml = `
                <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 10px; align-items: center;">
                    <input type="checkbox" class="question-checkbox" data-question-id="${question.id}" onchange="app.updateSelection(${question.id}, this.checked)">
                    <button class="btn btn-sm btn-info save-single-btn" onclick="app.saveSingleQuestion(${question.id})">💾</button>
                </div>
            `;
            
            if (question.type === 'multiple_choice') {
                questionDiv.innerHTML = controlsHtml + `
                    <h3>题目 ${index + 1}: ${question.question}</h3>
                    <div class="options">
                        ${question.options.map((option, optIndex) => `
                            <label class="option">
                                <input type="radio" name="question_${question.id}" value="${optIndex}">
                                <span>${option}</span>
                            </label>
                        `).join('')}
                    </div>
                    <button class="btn btn-primary check-answer" data-question-id="${question.id}" style="margin-top: 10px;">检查答案</button>
                    <div class="answer-feedback" id="feedback_${question.id}" style="margin-top: 10px; display: none;"></div>
                `;
            } else if (question.type === 'fill_blank') {
                questionDiv.innerHTML = controlsHtml + `
                    <h3>题目 ${index + 1}: ${question.question}</h3>
                    <input type="text" name="question_${question.id}" placeholder="请输入答案" style="width: 100%; padding: 10px; margin-top: 10px; border: 1px solid #ddd; border-radius: 4px;">
                    <button class="btn btn-primary check-answer" data-question-id="${question.id}" style="margin-top: 10px;">检查答案</button>
                    <div class="answer-feedback" id="feedback_${question.id}" style="margin-top: 10px; display: none;"></div>
                `;
            }
            
            container.appendChild(questionDiv);
        });

        // 绑定检查答案按钮事件
        document.querySelectorAll('.check-answer').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.checkSingleAnswer(e.target.dataset.questionId);
            });
        });

        this.updateSelectedCount();
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('questions-section').style.display = 'block';
    }

    updateSelection(questionId, isSelected) {
        if (isSelected) {
            this.selectedQuestions.add(questionId);
        } else {
            this.selectedQuestions.delete(questionId);
        }
        this.updateSelectedCount();
    }

    updateSelectedCount() {
        const countElement = document.getElementById('selected-count');
        if (countElement) {
            const count = this.selectedQuestions.size;
            countElement.textContent = count > 0 ? `已选择 ${count} 题` : '';
        }
    }

    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.question-checkbox');
        const allSelected = this.selectedQuestions.size === checkboxes.length;
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = !allSelected;
            const questionId = parseInt(checkbox.dataset.questionId);
            if (!allSelected) {
                this.selectedQuestions.add(questionId);
            } else {
                this.selectedQuestions.delete(questionId);
            }
        });
        
        this.updateSelectedCount();
    }

    async saveSingleQuestion(questionId) {
        const question = this.questions.find(q => q.id == questionId);
        if (!question) return;

        try {
            const response = await fetch('/save_single_question', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    question: question,
                    topic: `${this.topic} - 单题收藏`
                })
            });

            const data = await response.json();
            if (data.success) {
                alert('题目保存成功！');
            } else {
                alert('保存失败: ' + data.error);
            }
        } catch (error) {
            alert('保存失败: ' + error.message);
        }
    }

    async saveSelectedQuestions() {
        if (this.selectedQuestions.size === 0) {
            alert('请先选择题目');
            return;
        }

        const title = prompt('请输入题目集名称:', `${this.topic} - 精选题目`);
        if (!title) return;

        const selectedQuestions = this.questions.filter(q => 
            this.selectedQuestions.has(q.id)
        );

        try {
            const response = await fetch('/save_selected_questions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    selected_questions: selectedQuestions,
                    title: title
                })
            });

            const data = await response.json();
            if (data.success) {
                alert(`成功保存 ${data.count} 道题目！`);
                this.selectedQuestions.clear();
                this.updateSelectedCount();
                document.querySelectorAll('.question-checkbox').forEach(cb => cb.checked = false);
            } else {
                alert('保存失败: ' + data.error);
            }
        } catch (error) {
            alert('保存失败: ' + error.message);
        }
    }

    async showLoadDialog() {
        window.open('/question_sets_page', '_blank');
    }

    async loadQuestionSet(setId) {
        try {
            const response = await fetch(`/load_questions/${setId}`);
            const data = await response.json();
            
            if (data.success) {
                this.questions = data.questions;
                this.topic = data.topic;
                this.selectedQuestions.clear();
                this.displayQuestions();
                alert('题目加载成功！');
            } else {
                alert('加载失败: ' + data.error);
            }
        } catch (error) {
            alert('加载失败: ' + error.message);
        }
    }

    checkSingleAnswer(questionId) {
        const question = this.questions.find(q => q.id == questionId);
        if (!question) return;

        let userAnswer;
        if (question.type === 'multiple_choice') {
            const selected = document.querySelector(`[name="question_${question.id}"]:checked`);
            userAnswer = selected ? parseInt(selected.value) : null;
        } else if (question.type === 'fill_blank') {
            const input = document.querySelector(`[name="question_${question.id}"]`);
            userAnswer = input.value.trim();
        }

        // 前端直接判题
        let isCorrect = false;
        if (question.type === 'multiple_choice') {
            isCorrect = userAnswer === question.correct_answer;
        } else if (question.type === 'fill_blank') {
            isCorrect = userAnswer.toLowerCase() === question.correct_answer.toLowerCase();
        }

        const result = {
            correct: isCorrect,
            correct_answer: question.correct_answer,
            user_answer: userAnswer
        };

        this.showAnswerFeedback(questionId, result, question);
    }

    showAnswerFeedback(questionId, result, question) {
        const feedbackDiv = document.getElementById(`feedback_${questionId}`);
        const isCorrect = result.correct;
        
        let correctAnswerText;
        if (question.type === 'multiple_choice') {
            correctAnswerText = question.options[result.correct_answer];
        } else {
            correctAnswerText = result.correct_answer;
        }

        const explanationHtml = question.explanation ? `<br><small><strong>解析：</strong>${question.explanation}</small>` : '';

        feedbackDiv.innerHTML = `
            <div style="padding: 10px; border-radius: 4px; background: ${isCorrect ? '#d4edda' : '#f8d7da'}; color: ${isCorrect ? '#155724' : '#721c24'};">
                ${isCorrect ? '✅ 回答正确！' : '❌ 回答错误'}
                <br><small>正确答案：${correctAnswerText}</small>
                ${explanationHtml}
            </div>
        `;
        feedbackDiv.style.display = 'block';
    }

    async submitQuiz() {
        this.userAnswers = {};
        
        // 收集用户答案
        this.questions.forEach(question => {
            const inputs = document.querySelectorAll(`[name="question_${question.id}"]`);
            
            if (question.type === 'multiple_choice') {
                const selected = document.querySelector(`[name="question_${question.id}"]:checked`);
                this.userAnswers[question.id] = selected ? parseInt(selected.value) : null;
            } else if (question.type === 'fill_blank') {
                this.userAnswers[question.id] = inputs[0].value.trim();
            }
        });

        // 计算得分
        let correct = 0;
        this.questions.forEach(question => {
            const userAnswer = this.userAnswers[question.id];
            if (userAnswer === question.correct_answer) {
                correct++;
            }
        });

        this.displayResults(correct);
    }

    displayResults(correctCount) {
        const total = this.questions.length;
        const percentage = Math.round((correctCount / total) * 100);
        
        const resultsContainer = document.getElementById('results-container');
        resultsContainer.innerHTML = `
            <div class="score">
                得分: ${correctCount}/${total} (${percentage}%)
            </div>
            <div class="results-details">
                ${this.questions.map((question, index) => {
                    const userAnswer = this.userAnswers[question.id];
                    const isCorrect = userAnswer === question.correct_answer;
                    
                    const explanationHtml = question.explanation ? `<br><small><strong>解析：</strong>${question.explanation}</small>` : '';
                    
                    return `
                        <div class="result-item" style="margin: 15px 0; padding: 15px; background: ${isCorrect ? '#d4edda' : '#f8d7da'}; border-radius: 6px;">
                            <strong>题目 ${index + 1}:</strong> ${isCorrect ? '✅ 正确' : '❌ 错误'}
                            <br>
                            <small>你的答案: ${this.formatAnswer(question, userAnswer)} | 正确答案: ${this.formatAnswer(question, question.correct_answer)}</small>
                            ${explanationHtml}
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        document.getElementById('questions-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'block';
    }

    formatAnswer(question, answer) {
        if (question.type === 'multiple_choice') {
            return question.options[answer] || '未选择';
        }
        return answer || '未填写';
    }

    showLoading(message) {
        const container = document.getElementById('questions-container');
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>${message}</span>
            </div>
        `;
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('questions-section').style.display = 'block';
    }

    hideLoading() {
        // Loading will be hidden when displayQuestions is called
    }

    resetQuiz() {
        this.questions = [];
        this.userAnswers = {};
        this.selectedQuestions.clear();
        
        document.getElementById('text-input').value = '';
        document.getElementById('upload-section').style.display = 'block';
        document.getElementById('questions-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
    }
}

// 全局引用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new QuizApp();
});