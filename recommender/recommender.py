
import json

def load_question_bank(path="data/sample_questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def recommend_question(knowledge_point: str):
    questions = load_question_bank()
    for q in questions:
        if knowledge_point in q["knowledge_point"]:
            return q
    return None
