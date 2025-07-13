✅ Demo目标（简版智能学习助手）：
📷 拍照上传一道题目 → AI识别题目 → 判断知识点 & 是否掌握 → 推荐一题巩固练习

🔧 Demo 结构与任务拆解
| 模块            | 子任务                | 所用工具                                                               |
| ------------- | ------------------ | ------------------------------------------------------------------ |
| **1. 前端界面**   | 上传照片、展示题目内容、显示推荐题  | [Streamlit](https://streamlit.io)（推荐）或 Gradio                      |
| **2. 题目识别**   | 从图片中提取题目文本         | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 或 百度OCR API |
| **3. AI理解题目** | 用大模型判断题目知识点 & 掌握情况 | OpenAI GPT-4（或 Claude、文心一言）                                        |
| **4. 题目推荐**   | 根据分析结果推荐类似题目       | 可硬编码一批题 + ChatGPT推荐机制                                              |
| **5. 日志记录**   | 存储错题 & 分析结果        | 本地JSON/SQLite数据库                                                   |

🧩 示例使用流程（用户视角）
1. 用户上传一张题目图片
2. 系统提取题目文字（OCR）
3. AI分析题目属于什么知识点，用户是否掌握
4. 若未掌握 → 推荐一题类似练习题 + 解释
5. 系统记录该错题 + 推荐记录

🧪 所需工具安装/准备
A. 开发环境
- Python 3.9+
- 推荐使用虚拟环境（venv）

B. 库安装示例（用 pip）：
```python
pip install streamlit openai paddleocr paddlenlp
pip install opencv-python
```

C. 注册API Key
- OpenAI API Key（用于大模型调用）
- 百度智能云 OCR（可选，免费额度多）


📁 项目结构示意
```bash
studyhelper-demo/
├── app.py                  # Streamlit 主程序
├── ocr_utils.py            # 图像识别工具封装
├── llm_utils.py            # 大模型分析函数封装
├── question_bank.json      # 简单的题库（推荐题用）
├── data/                   # 用户上传图片和错题记录
└── requirements.txt        # 依赖文件
```

📸 示例界面草图（Streamlit）
```python
import streamlit as st
from ocr_utils import ocr_image
from llm_utils import analyze_question, recommend_question

st.title("AI 学习助手 Demo")
uploaded = st.file_uploader("上传作业题图片", type=["jpg", "png"])

if uploaded:
    st.image(uploaded, caption="上传的题目", use_column_width=True)
    question_text = ocr_image(uploaded)
    st.write("识别结果：", question_text)

    knowledge, mastered = analyze_question(question_text)
    st.write(f"识别知识点：{knowledge}")
    st.write(f"掌握情况：{'✅ 已掌握' if mastered else '❌ 需要加强'}")

    if not mastered:
        rec = recommend_question(knowledge)
        st.write("推荐练习：", rec['question'])
        st.write("讲解：", rec['explanation'])
```

✅ 第一步建议任务清单

| 优先级   | 任务         | 说明         |
| ----- | ---------- | ---------- |
| ✅ 必须  | 图像上传 & OCR | 完成基本识别     |
| ✅ 必须  | AI识别知识点    | 用大模型分析题目内容 |
| ✅ 必须  | 推荐机制       | 用固定题库推荐一题  |
| 🔜 可选 | 记录错题       | 存入本地JSON   |
| 🔜 可选 | 多轮对话       | 学生提问时继续答疑  |


📌 示例推荐题库结构（JSON）

```json
{
  "分式计算": [
    {
      "question": "计算：1/3 + 1/6 = ?",
      "explanation": "通分后加法：1/3 = 2/6, 所以答案是 3/6 = 1/2"
    },
    ...
  ]
}
```


🧠 AI提示词设计（Prompt Engineering）

用于分析题目：
```python
prompt = f"""
以下是一道数学题，请判断它主要考察的知识点，并回答学生是否掌握（仅根据题目文本推测）：
题目内容：{question_text}
返回格式：
知识点：XXX
掌握情况：（掌握/不掌握）
"""
```
## StudyHelper Demo 流程图与系统架构设计文档

本方案设计的是一个基于 Web 的智能学习助手 Demo，目标是：

- 用户上传作业题照片
- 系统识别题目内容（OCR）
- 使用大模型分析知识点和掌握情况
- 推荐练习题并展示讲解
- 记录错题，构建学生学习数据基础

---

## 🎯 一、功能流程图（简化）

```text
[用户上传题目图片]
        ↓
[OCR 图像识别] ← PaddleOCR (本地或轻量化模型)
        ↓
[提取题目文本]
        ↓
[调用大模型分析题目]
        ↓
 ┌──────────────┐
 │ 识别知识点     │
 │ 判断掌握情况   │
 └──────────────┘
        ↓
[查询推荐题库并生成推荐题]
        ↓
[展示结果 + 可视化反馈]
        ↓
[记录用户错题与学习行为]
```

---

## 🧱 二、系统架构图（模块划分）

```text
                           ┌───────────────┐
                           │     前端界面     │ ←—— 用户浏览器访问
                           │  Streamlit Web │
                           └─────┬─────────┘
                                 │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
     ┌────────────────┐              ┌───────────────────────┐
     │   图像识别模块   │              │    LLM 分析模块         │
     │   OCR识别        │              │  GPT-4 / Claude / 文心一言 │
     │ - PaddleOCR     │              │  - 知识点识别             │
     └────────────────┘              │  - 掌握情况判断           │
               │                                 │
               ▼                                 ▼
     ┌──────────────────────┐         ┌────────────────────────┐
     │     题库匹配与推荐模块     │←────┤     学生模型与记录模块      │
     │  - 简单 JSON/后续数据库     │    │  - 错题记录/学习数据建模     │
     │  - 推荐题与讲解展示         │    │  - SQLite / JSON            │
     └──────────────────────┘         └────────────────────────┘

```

---

## 🔍 三、模块清单与职责

| 模块       | 功能                 | 说明                              |
| -------- | ------------------ | ------------------------------- |
| 前端界面     | 上传题目图片，展示识别结果、推荐练习 | 使用 Streamlit，快速开发 Web UI        |
| 图像识别模块   | OCR 提取题干文本         | 调用 PaddleOCR 或本地开源 OCR 模型       |
| LLM 分析模块 | 利用大模型分析知识点与掌握情况    | 支持调用 OpenAI / Claude / 文心一言 API |
| 推荐模块     | 根据知识点推荐一题          | 初期硬编码题库，后期可用数据库+算法替代            |
| 错题记录模块   | 保存题目信息、推荐题、反馈      | 存储为 JSON 或使用 SQLite 数据库         |

---

## 🛠️ 四、核心技术栈

| 类别     | 技术                           | 说明                         |
| ------ | ---------------------------- | -------------------------- |
| Web前端  | Streamlit                    | 快速构建 AI Web 应用，支持上传图像、展示结果 |
| OCR    | PaddleOCR                    | 开源中文 OCR 项目，精度高、可离线运行      |
| 大模型API | OpenAI GPT-4 / Claude / 文心一言 | 用于题意理解、知识点识别与推荐讲解          |
| 数据存储   | JSON / SQLite                | 存储错题记录与用户学习画像数据            |
| 推荐系统   | 内置逻辑 + 小型题库匹配                | 可扩展为知识图谱或 Embedding 相似度推荐  |

---

## ✅ 五、Demo 开发目标与风格原则

- 简洁：界面与流程最简但完整，少即是多
- 清晰：每个模块职责单一，易于理解和替换
- 注释：所有代码中文注释，搭配使用文档
- 易扩展：未来支持多题批量分析、多学生并行、错题自动组卷
- 模块化：各功能模块解耦，便于测试、替换、升级

---

## 📘 六、下一步

1. 编写 `requirements.txt` 与目录初始化
2. 构建基本前端 + 上传图片逻辑
3. 封装 OCR 与 LLM API 调用模块
4. 设计推荐题库与数据记录格式
5. 输出带中文文档与注释的初始 Demo 版本

我将依照此架构，输出一个可运行的 Demo 项目，中文注释完整。 你将负责：

- 测试 API key 有效性（如 GPT-4）
- 提供可测试题目图片
- 按需调整大模型提示词与推荐策略

一切准备就绪后，我会生成一套 Demo 源码与说明，部署即用。





