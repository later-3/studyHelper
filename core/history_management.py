import json
import datetime
import uuid

HISTORY_FILE = '/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/data/submission_history.json'

def load_history():
    """加载所有答题历史。"""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_submission(user_id: str, question_id: str, submitted_text: str):
    """保存一条新的、轻量级的答题记录。"""
    history = load_history()
    new_submission = {
        "submission_id": str(uuid.uuid4()),
        "user_id": user_id,
        "question_id": question_id,
        "submitted_ocr_text": submitted_text,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    history.insert(0, new_submission)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)
    return new_submission

def get_submissions_by_question(user_id: str, question_id: str):
    """获取指定用户对指定题目的所有提交记录（兼容旧数据格式）。"""
    history = load_history()
    # 使用 .get() 方法安全地访问 'question_id'，如果键不存在则返回None，避免KeyError
    return [s for s in history if s.get('user_id') == user_id and s.get('question_id') == question_id]

def get_all_user_submissions(user_id: str):
    """获取一个用户的所有提交记录。"""
    history = load_history()
    return [s for s in history if s.get('user_id') == user_id]

def get_class_submissions(student_ids: list):
    """获取一个班级（由学生ID列表定义）的所有提交记录。"""
    history = load_history()
    return [s for s in history if s.get('user_id') in student_ids]