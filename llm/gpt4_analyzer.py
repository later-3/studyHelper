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
你是一位顶级的AI老师，你的任务是分析学生提交的题目。请遵循以下步骤和要求：

1.  **审题**: 仔细阅读题目内容。
2.  **判断学科**: 判断题目属于哪个学科（例如：数学、语文、英语等）。
3.  **判断对错**: 判断题目中的计算或解答是否正确。
4.  **深入分析**: 
    - 如果题目是 **错误** 的，请明确指出错误所在，解释错误原因，并给出正确的答案和详细的解题步骤。
    - 如果题目是 **正确** 的，请表扬学生，并可以提供另一种解法或相关的知识点扩展。
5.  **总结知识点**: 总结这道题所考察的核心知识点。
6.  **指出易错点**: 提醒学生在这类问题中常见的错误或需要注意的地方。

**输出格式要求**:
请严格按照以下JSON格式返回你的分析结果，不要添加任何额外的解释或说明文字。所有字段都必须包含，如果某个字段不适用，请返回空字符串 ""。

```json
{{
  "subject": "数学",
  "is_correct": false, 
  "error_analysis": "计算错误。1加1的结果应该是2，而不是3。",
  "correct_answer": "1 + 1 = 2",
  "solution_steps": "这是一个基础的加法运算。将1和1相加，得到结果2。",
  "knowledge_point": "10以内的加法",
  "common_mistakes": "在初学加法时，可能会因为数数不准或对加法概念理解不清而出错。"
}}
```

---

**现在，请分析以下题目：**

**题目内容:**
```
{question_text}
```
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一位顶级的AI数学老师，你的任务是分析学生提交的数学题目，并严格按照要求的JSON格式输出。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2, # 降低随机性以保证格式稳定
        max_tokens=1000
    )
    return response.choices[0].message.content.strip() if response.choices[0].message.content else ""
