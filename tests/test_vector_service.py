# -*- coding: utf-8 -*-
"""
Unit Tests for the Vector Service

This test suite ensures that the VectorService class functions correctly,
including document addition, searching, and management.
It uses a temporary directory for the ChromaDB instance to avoid
interfering with any development data.
"""

import unittest
import shutil
import os
from services.vector_service import VectorService

class TestVectorService(unittest.TestCase):
    """Test cases for the VectorService."""

    @classmethod
    def setUpClass(cls):
        """Set up a temporary directory for the test database."""
        cls.test_db_path = "./test_chroma_db_temp"
        # Ensure the directory does not exist before starting
        if os.path.exists(cls.test_db_path):
            shutil.rmtree(cls.test_db_path)
        os.makedirs(cls.test_db_path)
        cls.vector_service = VectorService(db_path=cls.test_db_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary database directory after all tests."""
        if os.path.exists(cls.test_db_path):
            shutil.rmtree(cls.test_db_path)

    def setUp(self):
        """Clear the collection before each test to ensure isolation."""
        self.vector_service.clear_all_documents()
        self.populate_test_data()

    def populate_test_data(self):
        """Populate the collection with some sample data."""
        self.ids = ["q1", "q2", "q3", "q4"]
        self.documents = [
            "What is the formula for the area of a circle?",
            "How do you calculate the circumference of a circle?",
            "What is the Pythagorean theorem?",
            "Explain the concept of photosynthesis."
        ]
        self.metadatas = [
            {"subject": "Math", "topic": "Geometry"},
            {"subject": "Math", "topic": "Geometry"},
            {"subject": "Math", "topic": "Geometry"},
            {"subject": "Science", "topic": "Biology"}
        ]
        self.vector_service.add_documents(self.ids, self.documents, self.metadatas)

    def test_add_documents_successfully(self):
        """Test that documents can be added and retrieved."""
        retrieved = self.vector_service.get_document_by_id("q1")
        self.assertIn("q1", retrieved['ids'])
        self.assertEqual(retrieved['documents'][0], self.documents[0])
        self.assertEqual(retrieved['metadatas'][0]['subject'], "Math")

    def test_add_documents_mismatched_lengths_raises_error(self):
        """Test that adding documents with mismatched list lengths raises a ValueError."""
        with self.assertRaises(ValueError):
            self.vector_service.add_documents(
                ids=["id5"],
                documents=["doc5", "doc6"],
                metadatas=[{"data": "meta5"}]
            )

    def test_search_similar_finds_relevant_documents(self):
        """Test that similarity search returns the most relevant documents."""
        query = "questions about circles"
        results = self.vector_service.search_similar(query, top_n=2)
        
        # The top 2 results should be q1 and q2
        result_ids = results['ids'][0]
        self.assertEqual(len(result_ids), 2)
        self.assertIn("q1", result_ids)
        self.assertIn("q2", result_ids)
        self.assertNotIn("q4", result_ids)

    def test_search_with_metadata_filter(self):
        """Although not explicitly in the service, ChromaDB supports it. This is a placeholder for future extension."""
        # This test demonstrates how a filter *would* be used, preparing for future features.
        results = self.vector_service.collection.query(
            query_texts=["What are geometric concepts?"],
            n_results=3,
            where={"subject": "Math"}
        )
        result_ids = results['ids'][0]
        self.assertIn("q1", result_ids)
        self.assertIn("q2", result_ids)
        self.assertIn("q3", result_ids)
        self.assertEqual(len(result_ids), 3)

    def test_clear_all_documents(self):
        """Test that the collection can be completely cleared."""
        # Verify there is data first
        count_before = self.vector_service.collection.count()
        self.assertEqual(count_before, 4)

        # Clear and verify
        self.vector_service.clear_all_documents()
        count_after = self.vector_service.collection.count()
        self.assertEqual(count_after, 0)

    def test_get_non_existent_document(self):
        """Test that getting a non-existent document returns an empty list."""
        result = self.vector_service.get_document_by_id("non_existent_id")
        self.assertEqual(len(result['ids']), 0)

if __name__ == '__main__':
    unittest.main()
