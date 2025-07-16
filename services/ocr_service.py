# services/ocr_service.py

from ocr.paddle_ocr import extract_text_from_image
from core.ai_services import get_ocr_engine
import logging

logger = logging.getLogger(__name__)

def get_text_from_image(image_input):
    """
    The main entry point for the OCR service.
    It lazily loads the OCR engine and then calls the extraction function.
    """
    logger.info("OCR service called. Lazily loading OCR engine...")
    # Get the singleton OCR engine instance from our cached resource manager.
    ocr_engine = get_ocr_engine()
    logger.info("after get_ocr_engine")
    # Pass the engine to the actual text extraction function.
    return extract_text_from_image(ocr_engine, image_input)