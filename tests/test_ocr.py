import unittest
import os
from PIL import Image
from ocr.paddle_ocr import extract_text_from_image

class TestOcr(unittest.TestCase):

    def setUp(self):
        """设置测试所需的文件路径。"""
        self.correct_math_path = '/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/data/problem_samples/math_correct.png'
        self.wrong_math_path = '/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/data/problem_samples/math_wrong.png'

    def test_extract_from_path_exact(self):
        """测试从文件路径提取精确的文本。"""
        self.assertTrue(os.path.exists(self.correct_math_path), "测试图片文件不存在")
        text_list = extract_text_from_image(self.correct_math_path)
        # 使用更严格的断言，确保识别结果完全符合预期
        self.assertEqual("".join(text_list).replace(" ", ""), "1+1=2")

    def test_extract_from_image_object_exact(self):
        """测试从Pillow Image对象提取精确的文本。"""
        self.assertTrue(os.path.exists(self.wrong_math_path), "测试图片文件不存在")
        with Image.open(self.wrong_math_path) as img:
            text_list = extract_text_from_image(img)
            self.assertEqual("".join(text_list).replace(" ", ""), "1+1=3")

    def test_invalid_input_type(self):
        """测试无效输入类型是否引发TypeError。"""
        with self.assertRaises(TypeError):
            extract_text_from_image(b'this is bytes') # 传递一个不支持的类型

if __name__ == '__main__':
    unittest.main()
