import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from unittest.mock import patch
from apps import app_v2

def mock_get_text_from_image(image_path):
    return ["1+1=3"]

def mock_get_analysis_for_text(ocr_text):
    return '{"is_correct": false, "error_analysis": "错误"}'

@patch('services.ocr_service.get_text_from_image', side_effect=mock_get_text_from_image)
@patch('services.llm_service.get_analysis_for_text', side_effect=mock_get_analysis_for_text)
def test_ai_analysis_workflow(mock_llm, mock_ocr):
    user = {'id': 'test_user'}
    image_path = 'assets/1.jpg'
    ocr_text = "1+1=3"
    master_analysis, ocr_text_out, _, _, logs = app_v2.intelligent_search_logic(user, image_path, ocr_text)
    assert master_analysis is not None
    assert ocr_text_out == ocr_text
    assert "错误" in str(master_analysis) 