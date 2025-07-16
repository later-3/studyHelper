# services/mistake_book_service.py

import os
import json
import datetime
import logging

# Get the logger configured in the main app
logger = logging.getLogger("studyhelper_app")

# Define the path for the mistakes JSON file relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
MISTAKES_FILE = os.path.join(DATA_DIR, 'mistakes.json')

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def _load_mistakes():
    """Helper function to load the mistakes data from the JSON file."""
    try:
        with open(MISTAKES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty/corrupt, start with an empty dict
        return {}

def _save_mistakes(data):
    """Helper function to save the mistakes data to the JSON file."""
    try:
        with open(MISTAKES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to save mistakes file: {e}", exc_info=True)
        return False

def add_mistake_if_incorrect(user_id: str, question_id: str, master_analysis: dict, submitted_text: str):
    """
    Checks the analysis result and adds the question to the user's mistake book if it was answered incorrectly.

    Args:
        user_id (str): The ID of the user.
        question_id (str): The unique ID of the question.
        master_analysis (dict): The detailed analysis result from the LLM.
        submitted_text (str): The text that the user submitted (from OCR).

    Returns:
        bool: True if a mistake was added or if the answer was correct, False on error.
    """
    if not master_analysis or not isinstance(master_analysis, dict):
        logger.warning("Invalid master_analysis provided to mistake book service.")
        return False

    # The core logic: only add to the mistake book if the answer is NOT correct.
    if master_analysis.get('is_correct') is not True:
        logger.info(f"Answer is incorrect. Adding question {question_id} to user {user_id}'s mistake book.")
        
        all_mistakes = _load_mistakes()
        user_mistakes = all_mistakes.get(user_id, [])

        # Check if this exact question is already in the mistake book to avoid duplicates
        if any(m['question_id'] == question_id for m in user_mistakes):
            logger.info(f"Question {question_id} is already in the mistake book for user {user_id}. Skipping.")
            return True

        # Create a new mistake entry
        new_mistake = {
            "mistake_id": f"mistake_{user_id}_{question_id}",
            "question_id": question_id,
            "user_id": user_id,
            "submitted_text": submitted_text,
            "added_timestamp": datetime.datetime.now().isoformat(),
            "review_status": "needs_review" # Possible values: needs_review, reviewed, mastered
        }
        
        user_mistakes.append(new_mistake)
        all_mistakes[user_id] = user_mistakes
        
        return _save_mistakes(all_mistakes)
    else:
        logger.info(f"Answer is correct. No mistake added for question {question_id} for user {user_id}.")
        return True # Return True because the operation was successful (no mistake to add)