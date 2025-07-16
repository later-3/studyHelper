# scripts/download_models.py

"""
Model Downloader Script

This script is executed during the Docker build process.
Its purpose is to pre-download and cache all the necessary machine learning models
from Hugging Face Hub, so that the application does not need to download them at runtime.

This approach ensures:
1.  Faster application startup.
2.  No runtime dependency on Hugging Face Hub connectivity.
3.  Model version consistency.
"""

from sentence_transformers import SentenceTransformer
from paddleocr import PaddleOCR
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting model download process...")

    # --- Download Sentence Transformer Model ---
    try:
        logger.info("Downloading and caching 'all-MiniLM-L6-v2' model...")
        SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("'all-MiniLM-L6-v2' model downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download Sentence Transformer model: {e}", exc_info=True)
        raise

    # --- Download PaddleOCR Models ---
    # The PaddleOCR constructor automatically downloads and caches its models.
    try:
        logger.info("Downloading and caching PaddleOCR models (det, rec, cls)...")
        # Initialize with only the supported parameters for the current version.
        # The library now likely auto-detects CPU/GPU capabilities.
        PaddleOCR(use_angle_cls=True, lang='ch')
        logger.info("PaddleOCR models downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download PaddleOCR models: {e}", exc_info=True)
        raise

    logger.info("All models have been successfully pre-downloaded and cached.")

if __name__ == "__main__":
    main()
