# ocr/paddle_ocr.py

from PIL import Image
import numpy as np
import logging

logger = logging.getLogger("studyhelper_app")

def extract_text_from_image(ocr_engine, image_input):
    """
    Uses a pre-initialized PaddleOCR engine to extract text from an image.
    
    Args:
        ocr_engine: An initialized instance of the PaddleOCR class.
        image_input: A file path (str) or a Pillow Image object.

    Returns:
        A list of extracted text strings.
    """
    logger.info("Starting text extraction using the provided OCR engine.")
    
    if not ocr_engine:
        logger.error("OCR engine is not available.")
        return ["OCR服务异常"]

    try:
        img_for_ocr = None
        if isinstance(image_input, str):
            logger.info(f"Input is a file path: {image_input}")
            img_for_ocr = image_input
        elif isinstance(image_input, Image.Image):
            logger.info(f"Input is a Pillow Image object. Mode: {image_input.mode}, Size: {image_input.size}")
            img_for_ocr = np.array(image_input.convert('RGB'))
        else:
            raise TypeError("输入必须是文件路径 (str) 或 Pillow Image 对象")

        logger.info("Calling ocr_engine.ocr()...")
        result = ocr_engine.ocr(img_for_ocr)
        logger.info(f"Raw OCR Result: {result}")
        print(f"PaddleOCR原始返回: {result}")
        
        extracted_text = []
        # 新版PaddleOCR返回dict，优先用rec_texts
        if result and result[0] is not None:
            if isinstance(result[0], dict) and 'rec_texts' in result[0]:
                txts = result[0]['rec_texts']
            else:
                # 兼容旧格式
                txts = [line[1][0] for line in result[0]]
            extracted_text.extend(txts)
        
        if not extracted_text:
            logger.warning("No text detected in the image.")
            return ["识别失败"]

        logger.info(f"Text extraction successful: {extracted_text}")
        return extracted_text

    except Exception as e:
        logger.error("OCR process failed with an exception.", exc_info=True)
        return ["识别异常"]
