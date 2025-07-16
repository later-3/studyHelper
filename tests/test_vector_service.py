# tests/test_vector_service.py

import unittest
import os
import shutil
import uuid
import sys

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import vector_service

class TestVectorService(unittest.TestCase):

    def setUp(self):
        """Set up a temporary, isolated ChromaDB for each test."""
        # Create a unique directory for the test database
        self.test_db_path = f'test_chroma_db_{uuid.uuid4()}'
        os.makedirs(self.test_db_path, exist_ok=True)
        
        # Override the service's client to use our temporary, in-memory database path
        vector_service.client = vector_service.chromadb.PersistentClient(path=self.test_db_path)
        self.collection_name = f"test_collection_{uuid.uuid4().hex}"

    def tearDown(self):
        """Clean up the temporary database directory after each test."""
        if os.path.exists(self.test_db_path):
            shutil.rmtree(self.test_db_path)

    def test_01_get_or_create_collection(self):
        """Test that a collection can be successfully created."""
        collection = vector_service.get_or_create_collection(self.collection_name)
        self.assertIsNotNone(collection, "Collection should be created.")
        self.assertEqual(collection.name, self.collection_name)

    def test_02_add_document(self):
        """Test that a document can be added to a collection."""
        collection = vector_service.get_or_create_collection(self.collection_name)
        doc_id = "doc1"
        document = "What is the capital of France?"
        metadata = {"subject": "Geography"}

        success = vector_service.add_document(collection, document, metadata, doc_id)
        self.assertTrue(success, "Document should be added successfully.")

        # Verify the document was added
        retrieved = collection.get(ids=[doc_id])
        self.assertEqual(len(retrieved['ids']), 1)
        self.assertEqual(retrieved['documents'][0], document)
        self.assertEqual(retrieved['metadatas'][0]['subject'], "Geography")

    def test_03_find_similar_documents(self):
        """Test that similarity search returns relevant results."""
        collection = vector_service.get_or_create_collection(self.collection_name)
        
        # Add some documents
        vector_service.add_document(collection, "The Eiffel Tower is in Paris.", {"topic": "monuments"}, "doc1")
        vector_service.add_document(collection, "The primary colors are red, yellow, and blue.", {"topic": "art"}, "doc2")
        vector_service.add_document(collection, "Paris is the capital of France.", {"topic": "capitals"}, "doc3")

        # Query for a similar document
        query_text = "Which city is the French capital?"
        results = vector_service.find_similar_documents(collection, query_text, n_results=1)
        
        # The most similar document should be doc3
        self.assertIsNotNone(results)
        self.assertEqual(len(results['ids'][0]), 1)
        self.assertEqual(results['ids'][0][0], "doc3", "The most similar document should be about Paris being the capital.")

if __name__ == '__main__':
    unittest.main()