# StudyHelper - 智能学习助手

StudyHelper 是一款基于 AI 技术的智能学习辅助工具，旨在帮助学生、教师和学校更高效地进行教与学。用户可以上传题目图片，获取即时的、深入的题目分析，并系统地管理和回顾学习历史。

## ✨ 主要功能

*   **🧠 智能搜题**:
    *   **图片搜题**: 上传题目图片，即可自动识别题目内容。
    *   **AI 导师分析**: 利用大语言模型（LLM）对题目进行深入分析，包括判断对错、提供详细解题步骤、总结核心知识点和常见易错点。
    *   **智能缓存**: 通过图像哈希（pHash）和文本哈希技术，秒级响应已分析过的题目，节省时间和计算资源。
    *   **强制刷新**: 如果对分析结果不满意，可强制调用 AI 进行重新分析。

*   **📖 答题历史与学情分析**:
    *   **自动归档**: 所有搜题记录都会被自动保存和归档。
    *   **多维度回顾**: 支持按题目、时间线等多种视图回顾历史记录。
    *   **学情统计**: 提供可视化的学情分析仪表盘，包括提交统计、学科分布、活跃度趋势等，帮助用户洞察学习状况。
    *   **高级筛选**: 可根据学科、正确率、日期范围等条件筛选题目。

*   **👥 多角色用户管理**:
    *   **学生**: 上传题目、查看个人学习历史和分析报告。
    *   **教师**: 查看所管理班级学生的学习情况。
    *   **学校管理员**: 俯瞰全校师生的整体学情数据。

## 🛠️ 技术栈

*   **前端**: [Streamlit](https://streamlit.io/) - 用于快速构建数据应用界面。
*   **OCR 文字识别**: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 用于从图片中精准识别文字。
*   **AI 核心分析**: [OpenAI API](https://openai.com/api/) - 提供强大的语言模型能力进行题目分析。
*   **核心库**: Pandas, Pillow, ImageHash 等。

## 🚀 快速开始

### 1. 环境准备

*   确保您已安装 Python 3.9 或更高版本。
*   (推荐) 创建并激活一个 Python 虚拟环境：
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

### 2. 安装依赖

克隆本项目到本地，然后进入项目目录安装所需的依赖包：

```bash
# 如果您使用 git
# git clone <your-repo-url>
# cd studyhelper-demo-final

pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录下创建一个名为 `.env` 的文件。这是运行应用所必需的，特别是用于配置第三方服务的 API 密钥。

```env
# .env 文件示例
# 将 'your_openai_api_key' 替换为您的真实 OpenAI API Key
OPENAI_API_KEY='your_openai_api_key'

# 如果您使用特定的 OpenAI API Base URL (例如代理), 请取消注释并设置
# OPENAI_API_BASE="https"
```

### 4. 运行应用

一切准备就绪后，在项目根目录下运行以下命令启动 Streamlit 应用：

```bash
streamlit run app.py
```

应用将在您的浏览器中自动打开。

## 📁 项目结构

```
/
├── app.py                   # Streamlit 应用主文件
├── requirements.txt         # Python 依赖库
├── .env                     # 环境变量配置文件 (需自行创建)
├── components/              # UI 组件 (如图表、卡片等)
├── services/                # 核心服务层 (数据、OCR, LLM, 存储)
├── data/                    # 存储应用数据 (JSON数据库、用户提交等)
├── ocr/                     # OCR 相关模块
├── llm/                     # 大语言模型交互模块
├── tests/                   # 测试代码
└── README.md                # 本文档
```