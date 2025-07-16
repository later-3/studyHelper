# tests/test_mistake_book_service.py

import unittest
import os
import json
import uuid
import sys

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import mistake_book_service

class TestMistakeBookService(unittest.TestCase):

    def setUp(self):
        """Set up a temporary, isolated mistakes file for each test."""
        # Generate a unique filename for the test mistakes file
        self.test_mistakes_file = f'test_mistakes_{uuid.uuid4()}.json'
        # Override the service's file path to use our temporary file
        mistake_book_service.MISTAKES_FILE = self.test_mistakes_file
        # Ensure the file is clean before each test
        if os.path.exists(self.test_mistakes_file):
            os.remove(self.test_mistakes_file)

    def tearDown(self):
        """Clean up the temporary mistakes file after each test."""
        if os.path.exists(self.test_mistakes_file):
            os.remove(self.test_mistakes_file)

    def test_add_mistake_when_incorrect(self):
        """Verify that a mistake is added when the analysis marks the answer as incorrect."""
        user_id = "test_user_01"
        question_id = "q_math_001"
        # Simulate an analysis result for an incorrect answer
        incorrect_analysis = {"is_correct": False, "subject": "Math"}
        submitted_text = "1 + 1 = 3"

        # Call the service function
        success = mistake_book_service.add_mistake_if_incorrect(
            user_id, question_id, incorrect_analysis, submitted_text
        )

        # Assertions
        self.assertTrue(success, "The save operation should succeed.")
        
        # Verify the content of the mistakes file
        with open(self.test_mistakes_file, 'r', encoding='utf-8') as f:
            mistakes_data = json.load(f)
        
        self.assertIn(user_id, mistakes_data, "User ID should be a key in the mistakes data.")
        self.assertEqual(len(mistakes_data[user_id]), 1, "There should be one mistake entry for the user.")
        
        mistake_entry = mistakes_data[user_id][0]
        self.assertEqual(mistake_entry['question_id'], question_id)
        self.assertEqual(mistake_entry['review_status'], "needs_review")

    def test_no_mistake_when_correct(self):
        """Verify that no mistake is added when the analysis marks the answer as correct."""
        user_id = "test_user_02"
        question_id = "q_geo_002"
        # Simulate an analysis result for a correct answer
        correct_analysis = {"is_correct": True, "subject": "Geography"}
        submitted_text = "Capital of France is Paris"

        # Call the service function
        success = mistake_book_service.add_mistake_if_incorrect(
            user_id, question_id, correct_analysis, submitted_text
        )

        # Assertions
        self.assertTrue(success, "The operation should be considered successful.")
        
        # Verify that the mistakes file was NOT created or is empty
        if os.path.exists(self.test_mistakes_file):
            with open(self.test_mistakes_file, 'r', encoding='utf-8') as f:
                mistakes_data = json.load(f)
            self.assertNotIn(user_id, mistakes_data, "User ID should not be in the mistakes data for a correct answer.")
        else:
            # If the file doesn't even exist, that's also a pass
            self.assertTrue(True)

    def test_no_duplicate_mistakes(self):
        """Verify that adding the same incorrect question multiple times does not create duplicate entries."""
        user_id = "test_user_03"
        question_id = "q_eng_003"
        incorrect_analysis = {"is_correct": False, "subject": "English"}
        submitted_text = "I has a book."

        # First call - should add the mistake
        mistake_book_service.add_mistake_if_incorrect(user_id, question_id, incorrect_analysis, submitted_text)
        # Second call - should recognize the duplicate and skip
        mistake_book_service.add_mistake_if_incorrect(user_id, question_id, incorrect_analysis, submitted_text)

        # Verify the content
        with open(self.test_mistakes_file, 'r', encoding='utf-8') as f:
            mistakes_data = json.load(f)
        
        self.assertEqual(len(mistakes_data[user_id]), 1, "There should only be one entry for the same mistake.")

if __name__ == '__main__':
    unittest.main()
