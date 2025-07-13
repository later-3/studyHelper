from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

# 初始化OCR引擎，针对简单数学表达式优化参数
# 禁用文档预处理功能，避免不必要的旋转和变形
logger.info("Initializing PaddleOCR engine with optimized parameters...")
ocr_engine = PaddleOCR(
    lang='en',  # 使用英文模型，对数字和符号识别更好
    use_doc_orientation_classify=False,  # 禁用文档方向分类
    use_doc_unwarping=False,  # 禁用文档矫正
    use_textline_orientation=False,  # 禁用文本行方向分类
    text_det_limit_side_len=64,  # 设置检测限制
    text_det_limit_type='min'  # 最小边限制
)
logger.info("PaddleOCR engine initialized with optimized parameters.")

def extract_text_from_image(image_input):
    """从图片中提取文本，支持文件路径或Pillow Image对象。"""
    logger.info("Starting text extraction.")
    
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

        logger.debug("Calling ocr_engine.ocr()...")
        # 使用最简单的API调用，移除所有可能引起冲突的参数
        result = ocr_engine.ocr(img_for_ocr)
        logger.debug("ocr_engine.ocr() returned.")
        
        extracted_text = []
        if result and len(result) > 0:
            # 新版本PaddleOCR的结果结构不同
            for page_result in result:
                if 'rec_texts' in page_result:
                    # 直接获取识别到的文本列表
                    page_texts = page_result['rec_texts']
                    extracted_text.extend(page_texts)
                    logger.info(f"Found texts: {page_texts}")
        
        if not extracted_text:
            logger.warning("No text detected.")
            return ["识别失败"]

        logger.info(f"Text extraction successful: {extracted_text}")
        return extracted_text

    except Exception as e:
        logger.error("OCR process failed with an exception.", exc_info=True)
        return ["识别异常"]