# core/ai_services.py

import streamlit as st
from services.vector_service import VectorService
from paddleocr import PaddleOCR
import logging
import time
import os

# Configure logging
logger = logging.getLogger(__name__)

# @st.cache_resource
def get_vector_service():
    """
    Gets a singleton instance of the VectorService.
    This is cached by Streamlit for the entire session.
    """
    logger.info("Initializing VectorService for the first time...")
    try:
        service = VectorService()
        logger.info("VectorService initialized and cached successfully.")
        return service
    except Exception as e:
        logger.error(f"Failed to initialize VectorService: {e}", exc_info=True)
        st.error("向量服务初始化失败，请检查后台日志。")
        return None

# @st.cache_resource
def get_ocr_engine():
    logger.info("Initializing PaddleOCR engine for the first time...")
    try:
        t0 = time.time()
        ocr_engine = PaddleOCR(
            lang='en',
            use_textline_orientation=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            text_det_limit_side_len=64,
            text_det_limit_type='min'
        )
        logger.info(f"PaddleOCR engine initialized and cached successfully. 耗时: {time.time()-t0:.2f}秒")
        return ocr_engine
    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR engine: {e}", exc_info=True)
        st.error("OCR服务初始化失败，请检查后台日志。")
        return None
