# -*- coding: utf-8 -*-
"""
Vector Service Module

This module encapsulates all interactions with the vector database.
It handles text embedding, document storage, and similarity searches.
This abstraction allows us to easily swap the underlying vector database
(e.g., from local ChromaDB to a production Milvus/Pinecone) without
changing the application logic.
"""

import chromadb
from chromadb.types import Collection
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorService:
    """A service for handling vector embeddings and similarity search."""

    def __init__(self, db_path: str = "./data/chroma_db"):
        """
        Initializes the VectorService.

        Args:
            db_path (str): Path to the ChromaDB storage directory.
        """
        try:
            # Load a pre-trained sentence transformer model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self._get_or_create_collection()
            logger.info(f"VectorService initialized with DB path: {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {e}", exc_info=True)
            raise

    def _get_or_create_collection(self, collection_name: str = "studyhelper_main") -> Collection:
        """
        Gets or creates a collection in ChromaDB.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            Collection: The ChromaDB collection object.
        """
        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            logger.info(f"Successfully connected to collection '{collection_name}'.")
            return collection
        except Exception as e:
            logger.error(f"Failed to get or create collection '{collection_name}': {e}", exc_info=True)
            raise

    def add_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """
        Adds a batch of documents to the vector store.

        Args:
            ids (List[str]): A list of unique identifiers for the documents.
            documents (List[str]): A list of document texts.
            metadatas (List[Dict[str, Any]]): A list of metadata dictionaries corresponding to the documents.
        """
        if not (len(ids) == len(documents) == len(metadatas)):
            raise ValueError("The lengths of ids, documents, and metadatas must be the same.")

        try:
            # ChromaDB automatically handles embedding if no embeddings are provided.
            # However, for consistency and control, we can embed it ourselves.
            # For simplicity here, we let ChromaDB handle it with its default SentenceTransformer.
            # In a production system, we would use self.model.encode(documents).tolist()
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(documents)} documents.")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}", exc_info=True)
            raise

    def search_similar(self, query_text: str, top_n: int = 5) -> Dict[str, Any]:
        """
        Searches for documents similar to a given query text.

        Args:
            query_text (str): The text to search for.
            top_n (int): The number of similar documents to return.

        Returns:
            Dict[str, Any]: A dictionary containing the search results.
        """
        try:
            # The query_texts argument expects a list
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_n
            )
            logger.info(f"Search for '{query_text[:30]}...' returned {len(results.get('ids', [[]])[0])} results.")
            return results
        except Exception as e:
            logger.error(f"Failed to perform search: {e}", exc_info=True)
            raise

    def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieves a single document by its unique ID.

        Args:
            doc_id (str): The ID of the document to retrieve.

        Returns:
            Dict[str, Any]: A dictionary containing the document data.
        """
        try:
            result = self.collection.get(ids=[doc_id])
            return result
        except Exception as e:
            logger.error(f"Failed to get document by ID '{doc_id}': {e}", exc_info=True)
            raise

    def clear_all_documents(self) -> None:
        """
        Deletes all documents from the collection. 
        Mainly used for testing purposes.
        """
        try:
            collection_name = self.collection.name
            self.client.delete_collection(name=collection_name)
            self.collection = self._get_or_create_collection(collection_name)
            logger.info(f"Successfully cleared all documents from collection '{collection_name}'.")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}", exc_info=True)
            raise
