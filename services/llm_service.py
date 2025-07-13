from llm.gpt4_analyzer import analyze_question_with_gpt4

def get_analysis_for_text(text: str):
    """LLM服务的统一入口点。"""
    # 未来可以在这里添加路由逻辑，比如根据题目类型选择不同的大模型
    return analyze_question_with_gpt4(text)
