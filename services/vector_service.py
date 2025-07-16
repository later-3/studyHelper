# services/vector_service.py

import chromadb
import logging
import os

logger = logging.getLogger("studyhelper_app")

# --- ChromaDB Client Initialization ---

# Get the project root directory to build the persistent path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'chroma_db')

# Ensure the database directory exists
os.makedirs(DB_PATH, exist_ok=True)

# Initialize a persistent ChromaDB client
# This will save the database to disk in the specified path
client = chromadb.PersistentClient(path=DB_PATH)

# --- Constants ---
# Define a default collection name for our questions
DEFAULT_COLLECTION_NAME = "questions_collection"

# --- Service Functions ---

def get_or_create_collection(name: str = DEFAULT_COLLECTION_NAME):
    """
    Retrieves an existing collection or creates a new one if it doesn't exist.

    Args:
        name (str): The name of the collection.

    Returns:
        chromadb.Collection: The collection object.
    """
    try:
        collection = client.get_or_create_collection(name=name)
        logger.info(f"Successfully connected to ChromaDB collection: '{name}'")
        return collection
    except Exception as e:
        logger.error(f"Failed to get or create ChromaDB collection '{name}': {e}", exc_info=True)
        return None

def add_document(collection, document: str, metadata: dict, doc_id: str):
    """
    Adds a single document and its metadata to the specified collection.
    The document text will be automatically converted to a vector embedding.

    Args:
        collection (chromadb.Collection): The collection to add to.
        document (str): The text content of the document.
        metadata (dict): A dictionary of metadata associated with the document.
        doc_id (str): The unique ID for the document.

    Returns:
        bool: True if the document was added successfully, False otherwise.
    """
    if not all([collection, document, metadata, doc_id]):
        logger.warning("add_document called with invalid arguments.")
        return False
    try:
        collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        logger.info(f"Successfully added document with ID '{doc_id}' to collection '{collection.name}'.")
        return True
    except Exception as e:
        # ChromaDB can raise various exceptions, including for duplicate IDs
        logger.error(f"Failed to add document ID '{doc_id}' to collection '{collection.name}': {e}", exc_info=True)
        return False

def find_similar_documents(collection, query_text: str, n_results: int = 5):
    """
    Finds documents in the collection that are semantically similar to the query text.

    Args:
        collection (chromadb.Collection): The collection to search in.
        query_text (str): The text to find similar documents for.
        n_results (int): The number of similar documents to return.

    Returns:
        list: A list of results, or an empty list if an error occurs or no results are found.
    """
    if not all([collection, query_text]):
        logger.warning("find_similar_documents called with invalid arguments.")
        return []
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        logger.info(f"Found {len(results.get('ids', [[]])[0])} similar documents for query: '{query_text[:50]}...'")
        return results
    except Exception as e:
        logger.error(f"Failed to query collection '{collection.name}': {e}", exc_info=True)
        return []