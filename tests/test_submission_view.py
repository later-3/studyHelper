# tests/test_submission_view.py

import unittest
import os
import streamlit as st
from components.submission_view import render_submission_preview
from PIL import Image

class TestSubmissionView(unittest.TestCase):
    """Test cases for the submission view component."""

    def setUp(self):
        """Create a dummy image file for testing."""
        self.test_dir = "./test_data_temp"
        os.makedirs(self.test_dir, exist_ok=True)
        self.image_path = os.path.join(self.test_dir, "test_image.png")
        
        # Create a simple black image
        img = Image.new('RGB', (60, 30), color = 'black')
        img.save(self.image_path)

    def tearDown(self):
        """Clean up the dummy image file."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_render_submission_preview_runs_without_error(self):
        """ 
        Test that the component rendering function can be called without raising exceptions.
        This is a basic structural test, not a visual one.
        """
        try:
            # In a real Streamlit test, we would use a library to check the output.
            # Here, we just ensure it runs.
            render_submission_preview(self.image_path, "This is a test OCR text.")
            # If it runs without error, we consider it a pass for this basic test.
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"render_submission_preview raised an exception unexpectedly: {e}")

    def test_render_with_non_existent_image(self):
        """
        Test that the component handles a non-existent image path gracefully.
        """
        try:
            # We expect this to run without error and handle it internally (e.g., show an error message).
            render_submission_preview("non_existent_path.png", "Some text")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"render_submission_preview failed to handle non-existent image: {e}")

if __name__ == '__main__':
    unittest.main()
