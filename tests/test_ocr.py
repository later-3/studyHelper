import unittest
import os
from core.ai_services import get_ocr_engine
from ocr.paddle_ocr import extract_text_from_image

class TestOcrDebug(unittest.TestCase):
    def setUp(self):
        self.img_path = 'assets/1.jpg'
        self.log_path = 'logs/app.log'

    def test_ocr_result(self):
        self.assertTrue(os.path.exists(self.img_path), "测试图片不存在")
        ocr_engine = get_ocr_engine()
        text_list = extract_text_from_image(ocr_engine, self.img_path)
        result = "".join(text_list).replace(" ", "")
        print(f"OCR结果: {result}")
        self.assertEqual(result, "1+1=3")

    def test_log_written(self):
        self.assertTrue(os.path.exists(self.log_path), "日志文件不存在")
        with open(self.log_path) as f:
            log_content = f.read()
        self.assertIn("Text extraction successful", log_content)

if __name__ == '__main__':
    unittest.main()
