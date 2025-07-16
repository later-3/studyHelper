# from openai import OpenAI
# import os

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def analyze_question_with_gpt4(text):  # 实际函数定义
#     """
#     使用 GPT 模型分析题目...
#     """
#     prompt = f"""
# 你是一个专业的小学老师，请分析下面这道题，判断其考察的知识点、难度，以及学生可能的掌握情况，并提出一个讲解建议。

# 题目内容：
# {text}
# """
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "你是一个擅长分析学生题目的老师"},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.7
#     )

#     return response.choices[0].message.content.strip()


import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件中的环境变量
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

def analyze_question_with_gpt4(question_text: str) -> str:
    prompt = f"""
你是一位顶级的AI老师，你的任务是分析学生提交的题目并严格以JSON格式返回结果。

**核心指令:** 无论任何情况，你的最终输出**必须**是一个完整的、无任何多余修饰的JSON代码块。

---
**示例 1: 一个错误的数学题**

**输入:**
```
1 + 1 = 3
```

**你的输出:**
```json
{{
  "subject": "数学",
  "is_correct": false,
  "error_analysis": "计算错误。这道题的计算结果是错误的，1加1的正确结果应该是2，而不是3。",
  "correct_answer": "1 + 1 = 2",
  "solution_steps": "这是一个基础的加法运算。将数字1和另一个数字1相加，根据基础加法原则，得到最终结果2。",
  "knowledge_point": "5以内的加法",
  "common_mistakes": "在初学加法时，学生可能会因为数数不准确或者对加法概念理解不清晰而犯错。反复练习是关键。"
}}
```

---
**示例 2: 一个正确的地理题**

**输入:**
```
中国的首都是北京
```

**你的输出:**
```json
{{
  "subject": "地理",
  "is_correct": true,
  "error_analysis": "",
  "correct_answer": "中国的首都是北京。",
  "solution_steps": "这是一个关于国家首都的基本常识题。中国的首都确实是北京。",
  "knowledge_point": "世界各国首都",
  "common_mistakes": "对于中国地理不熟悉的学生，可能会将上海等经济中心误认为是首都。"
}}
```

---

**任务开始**

现在，请严格遵循以上示例的格式，分析以下题目。不要添加任何额外的解释、对话或说明文字，直接输出JSON代码块。

**题目内容:**
```
{question_text}
```
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一位顶级的AI分析专家，你的任务是分析题目，并严格按照用户要求的JSON格式输出，不得包含任何额外文本。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1, # 进一步降低随机性
        max_tokens=1500  # 稍微增加token以容纳更复杂的分析
    )
    return response.choices[0].message.content.strip() if response.choices[0].message.content else ""
