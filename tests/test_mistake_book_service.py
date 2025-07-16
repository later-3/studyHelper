# tests/test_mistake_book_service.py

import unittest
import os
import json
from services import mistake_book_service

class TestMistakeBookService(unittest.TestCase):
    """Test cases for the Mistake Book Service."""

    def setUp(self):
        """Set up a temporary mistakes file for testing."""
        # Use a path that includes a directory to avoid FileNotFoundError
        self.test_dir = "./test_data_temp"
        self.test_file_path = os.path.join(self.test_dir, "test_mistakes.json")
        mistake_book_service.MISTAKES_FILE_PATH = self.test_file_path
        
        # Create the temporary directory
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        """Clean up the temporary directory and its contents after testing."""
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)

    def test_add_mistake_for_incorrect_answer(self):
        """Test that a mistake is added only when the answer is incorrect."""
        user_id = "student_test_01"
        question_id = "q_math_001"
        ocr_text = "What is 2+2?"
        correct_analysis = {"is_correct": True}
        incorrect_analysis = {
            "is_correct": False, 
            "knowledge_point": "Basic Arithmetic", 
            "error_analysis": "Calculation error"
        }

        # Case 1: Correct answer, should not add a mistake
        added = mistake_book_service.add_mistake_if_incorrect(user_id, question_id, correct_analysis, ocr_text)
        self.assertFalse(added)
        mistakes = mistake_book_service.get_mistakes_by_user(user_id)
        self.assertEqual(len(mistakes), 0)

        # Case 2: Incorrect answer, should add a mistake
        added = mistake_book_service.add_mistake_if_incorrect(user_id, question_id, incorrect_analysis, ocr_text)
        self.assertTrue(added)
        mistakes = mistake_book_service.get_mistakes_by_user(user_id)
        self.assertEqual(len(mistakes), 1)
        self.assertEqual(mistakes[0]['question_id'], question_id)
        self.assertEqual(mistakes[0]['knowledge_point'], "Basic Arithmetic")

    def test_add_mistake_avoids_duplicates(self):
        """Test that the same mistake is not added twice for the same user."""
        user_id = "student_test_02"
        question_id = "q_sci_002"
        ocr_text = "What is H2O?"
        incorrect_analysis = {"is_correct": False}

        # Add the mistake for the first time
        mistake_book_service.add_mistake_if_incorrect(user_id, question_id, incorrect_analysis, ocr_text)
        mistakes = mistake_book_service.get_mistakes_by_user(user_id)
        self.assertEqual(len(mistakes), 1)

        # Try to add the same mistake again
        added = mistake_book_service.add_mistake_if_incorrect(user_id, question_id, incorrect_analysis, ocr_text)
        self.assertFalse(added) # Should return False as it was not added
        mistakes = mistake_book_service.get_mistakes_by_user(user_id)
        self.assertEqual(len(mistakes), 1) # Count should still be 1

    def test_get_mistakes_by_user_returns_correct_data(self):
        """Test that mistakes for different users are handled correctly."""
        user1 = "student_01"
        user2 = "student_02"
        analysis = {"is_correct": False}

        # Add mistakes for both users
        mistake_book_service.add_mistake_if_incorrect(user1, "q1", analysis, "q1_text")
        mistake_book_service.add_mistake_if_incorrect(user2, "q2", analysis, "q2_text")
        mistake_book_service.add_mistake_if_incorrect(user1, "q3", analysis, "q3_text")

        # Check mistakes for user1
        user1_mistakes = mistake_book_service.get_mistakes_by_user(user1)
        self.assertEqual(len(user1_mistakes), 2)
        self.assertEqual(user1_mistakes[0]['question_id'], "q3") # Sorted by date, q3 is newest
        self.assertEqual(user1_mistakes[1]['question_id'], "q1")

        # Check mistakes for user2
        user2_mistakes = mistake_book_service.get_mistakes_by_user(user2)
        self.assertEqual(len(user2_mistakes), 1)
        self.assertEqual(user2_mistakes[0]['question_id'], "q2")

        # Check for a user with no mistakes
        user3_mistakes = mistake_book_service.get_mistakes_by_user("student_03")
        self.assertEqual(len(user3_mistakes), 0)

if __name__ == '__main__':
    unittest.main()