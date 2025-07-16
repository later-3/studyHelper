# services/mistake_book_service.py

import json
import os
from datetime import datetime
import logging
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

MISTAKES_FILE_PATH = os.path.join('data', 'mistakes.json')

def _load_mistakes() -> Dict[str, List[Dict[str, Any]]]:
    """Loads the mistakes data from the JSON file."""
    if not os.path.exists(MISTAKES_FILE_PATH):
        return {}
    try:
        with open(MISTAKES_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error loading mistakes file: {e}", exc_info=True)
        return {}

def _save_mistakes(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Saves the mistakes data to the JSON file."""
    try:
        os.makedirs(os.path.dirname(MISTAKES_FILE_PATH), exist_ok=True)
        with open(MISTAKES_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        logger.error(f"Error saving mistakes file: {e}", exc_info=True)

def add_mistake_if_incorrect(user_id: str, question_id: str, master_analysis: Dict[str, Any], ocr_text: str) -> bool:
    """
    Checks the analysis result and adds the question to the user's mistake book if it was incorrect.

    Args:
        user_id (str): The ID of the user.
        question_id (str): The ID of the question.
        master_analysis (Dict[str, Any]): The AI's analysis result.
        ocr_text (str): The OCR'd text of the question.

    Returns:
        bool: True if a mistake was added, False otherwise.
    """
    if master_analysis.get('is_correct') is True:
        return False

    logger.info(f"Adding question {question_id} to mistake book for user {user_id}.")
    all_mistakes = _load_mistakes()
    user_mistakes = all_mistakes.get(user_id, [])

    # Check if this exact question is already in the mistake book to avoid duplicates
    if any(m['question_id'] == question_id for m in user_mistakes):
        logger.warning(f"Mistake {question_id} already exists for user {user_id}. Skipping.")
        return False

    new_mistake = {
        "mistake_id": f"mistake_{question_id}",
        "question_id": question_id,
        "question_text": ocr_text,
        "knowledge_point": master_analysis.get('knowledge_point', 'N/A'),
        "error_analysis": master_analysis.get('error_analysis', 'N/A'),
        "added_at": datetime.now().isoformat()
    }

    user_mistakes.append(new_mistake)
    all_mistakes[user_id] = user_mistakes
    _save_mistakes(all_mistakes)
    return True

def get_mistakes_by_user(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all mistakes for a given user.

    Args:
        user_id (str): The ID of the user.

    Returns:
        List[Dict[str, Any]]: A list of the user's mistakes, sorted by date.
    """
    all_mistakes = _load_mistakes()
    user_mistakes = all_mistakes.get(user_id, [])
    # Sort by most recent first
    return sorted(user_mistakes, key=lambda x: x['added_at'], reverse=True)
