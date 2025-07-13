from ocr.paddle_ocr import extract_text_from_image
import logging

logger = logging.getLogger(__name__)

def get_text_from_image(image_input):
    """OCR服务的统一入口点。"""
    logger.info("OCR service called.")
    return extract_text_from_image(image_input)
