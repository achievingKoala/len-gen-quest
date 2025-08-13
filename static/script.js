class QuizApp {
    constructor() {
        this.questions = [];
        this.userAnswers = {};
        this.init();
    }

    init() {
        this.bindEvents();
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
    }

    async handleFileUpload(file) {
        if (!file) return;
        
        const text = await file.text();
        document.getElementById('text-input').value = text;
    }

    async generateQuestions() {
        const textContent = document.getElementById('text-input').value.trim();
        
        if (!textContent) {
            alert('请先输入或上传文本内容');
            return;
        }

        try {
            const response = await fetch('/upload_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: textContent })
            });

            const data = await response.json();
            
            if (data.success) {
                this.questions = data.questions;
                this.displayQuestions();
            } else {
                alert('生成题目失败: ' + data.error);
            }
        } catch (error) {
            alert('网络错误: ' + error.message);
        }
    }

    displayQuestions() {
        const container = document.getElementById('questions-container');
        container.innerHTML = '';

        this.questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question';
            
            if (question.type === 'multiple_choice') {
                questionDiv.innerHTML = `
                    <h3>题目 ${index + 1}: ${question.question}</h3>
                    <div class="options">
                        ${question.options.map((option, optIndex) => `
                            <label class="option">
                                <input type="radio" name="question_${question.id}" value="${optIndex}">
                                <span>${option}</span>
                            </label>
                        `).join('')}
                    </div>
                `;
            } else if (question.type === 'fill_blank') {
                questionDiv.innerHTML = `
                    <h3>题目 ${index + 1}: ${question.question}</h3>
                    <input type="text" name="question_${question.id}" placeholder="请输入答案" style="width: 100%; padding: 10px; margin-top: 10px; border: 1px solid #ddd; border-radius: 4px;">
                `;
            }
            
            container.appendChild(questionDiv);
        });

        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('questions-section').style.display = 'block';
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
                    
                    return `
                        <div class="result-item" style="margin: 15px 0; padding: 15px; background: ${isCorrect ? '#d4edda' : '#f8d7da'}; border-radius: 6px;">
                            <strong>题目 ${index + 1}:</strong> ${isCorrect ? '✅ 正确' : '❌ 错误'}
                            <br>
                            <small>你的答案: ${this.formatAnswer(question, userAnswer)} | 正确答案: ${this.formatAnswer(question, question.correct_answer)}</small>
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

    resetQuiz() {
        this.questions = [];
        this.userAnswers = {};
        
        document.getElementById('text-input').value = '';
        document.getElementById('upload-section').style.display = 'block';
        document.getElementById('questions-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new QuizApp();
});