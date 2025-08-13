# 智能题目生成器

基于文本内容自动生成练习题目的Web应用。

## 功能特点

- 📝 支持文本粘贴和文件上传
- 🎯 自动生成多种题型（选择题、填空题）
- 📋 实时做题模式
- 📊 答题结果统计

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python app.py
```

3. 访问 http://localhost:5000

## 项目结构

```
learn-book/
├── app.py              # Flask后端主文件
├── requirements.txt    # Python依赖
├── templates/
│   └── index.html     # 前端页面
└── static/
    ├── style.css      # 样式文件
    └── script.js      # 交互逻辑
```

## 扩展功能

- 接入AI API（如OpenAI、Claude）生成更智能的题目
- 添加更多题型（判断题、简答题等）
- 用户答题历史记录
- 题目难度分级