import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import question_manager as qm
from core import history_management as hm
import logging

logger = logging.getLogger(__name__)

# --- Question Bank Facade ---
def get_question_by_phash(image_path: str):
    """通过图片phash获取问题，包含数据有效性检查"""
    phash = qm.generate_phash(image_path)
    if not phash:
        logger.warning(f"Failed to generate phash for {image_path}")
        return None
        
    question_id = qm.get_question_id_by_phash(phash)
    if question_id:
        question_data = qm.get_question_by_id(question_id)
        if qm.is_valid_question_data(question_data):
            logger.info(f"Valid question found by phash: {phash} -> {question_id}")
            return question_data
        else:
            logger.warning(f"Invalid question data found by phash: {phash} -> {question_id}")
            return None
    return None

def get_question_by_id(question_id: str):
    """通过问题ID获取问题，包含数据有效性检查"""
    question_data = qm.get_question_by_id(question_id)
    if question_data and qm.is_valid_question_data(question_data):
        return question_data
    return None

def add_question(text: str, analysis: dict, image_path: str, existing_question_id: str = None):
    """添加或更新问题，包含数据验证"""
    # 验证输入数据
    if not text or text in ['识别失败', '识别异常']:
        logger.warning(f"Invalid OCR text: {text}")
        return False
        
    if not analysis or not isinstance(analysis, dict):
        logger.warning(f"Invalid analysis data: {analysis}")
        return False
    
    phash = qm.generate_phash(image_path)
    question_id = existing_question_id or qm.generate_question_id(text)
    
    success = qm.add_question(question_id, text, analysis, phash, image_path)
    if success:
        logger.info(f"Successfully added/updated question: {question_id}")
    else:
        logger.error(f"Failed to add/update question: {question_id}")
    
    return success

def generate_question_id(text: str) -> str:
    return qm.generate_question_id(text)

def load_question_bank():
    return qm.load_bank()

def cleanup_invalid_data():
    """清理无效的数据"""
    return qm.cleanup_invalid_data()

# --- Submission History Facade ---
def save_submission(user_id: str, question_id: str, submitted_text: str):
    return hm.save_submission(user_id, question_id, submitted_text)

def get_submissions_by_question(user_id: str, question_id: str):
    return hm.get_submissions_by_question(user_id, question_id)

def get_submissions_by_user(user_id: str):
    """获取指定用户的所有提交记录"""
    return hm.get_all_user_submissions(user_id)

def load_all_submissions():
    return hm.load_history()
