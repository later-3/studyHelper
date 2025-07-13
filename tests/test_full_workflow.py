import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
from PIL import Image

# 在导入被测试模块之前，设置临时文件路径
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import question_manager
from core import history_management

TEST_DIR = f"test_run_{uuid.uuid4().hex}"
if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)

question_manager.BANK_FILE = os.path.join(TEST_DIR, 'test_bank.json')
history_management.HISTORY_FILE = os.path.join(TEST_DIR, 'test_history.json')
question_manager.PHASH_MAP_FILE = os.path.join(TEST_DIR, 'test_phash_map.json')

# 现在可以安全地导入app中的函数了
from apps.app import intelligent_search_logic

class TestFullWorkflow(unittest.TestCase):

    def setUp(self):
        """每个测试前清空测试文件。"""
        with open(question_manager.BANK_FILE, 'w') as f:
            json.dump({}, f)
        with open(history_management.HISTORY_FILE, 'w') as f:
            json.dump([], f)
        with open(question_manager.PHASH_MAP_FILE, 'w') as f:
            json.dump({}, f)
        # 创建一个虚拟的图片文件用于测试
        self.dummy_image_path = os.path.join(TEST_DIR, "dummy_image.png")
        Image.new('RGB', (100, 100), color = 'red').save(self.dummy_image_path)

    @patch('services.ocr_service.get_text_from_image')
    @patch('services.llm_service.get_analysis_for_text')
    def test_cache_miss_workflow(self, mock_get_analysis, mock_get_text):
        """测试缓存未命中时的完整工作流程。"""
        user = {'id': 'student1', 'role': 'student'}
        mock_get_text.return_value = ["全新的题目"]
        mock_analysis_json = {"subject": "测试", "is_correct": True}
        mock_get_analysis.return_value = json.dumps(mock_analysis_json)

        master_analysis, _, _, _ = intelligent_search_logic(user, self.dummy_image_path)

        self.assertIsNotNone(master_analysis)
        self.assertEqual(master_analysis['subject'], "测试")
        mock_get_analysis.assert_called_once()
        self.assertEqual(len(history_management.load_history()), 1)

    @patch('services.ocr_service.get_text_from_image')
    @patch('services.llm_service.get_analysis_for_text')
    def test_cache_hit_workflow(self, mock_get_analysis, mock_get_text):
        """测试缓存命中时的完整工作流程。"""
        user = {'id': 'student1', 'role': 'student'}
        ocr_text = "已经存在的题目"
        question_id = question_manager.generate_question_id(ocr_text)
        preset_analysis = {"subject": "历史", "is_correct": False}
        # 预设一个pHash并将其与question_id关联
        phash = question_manager.generate_phash(self.dummy_image_path)
        question_manager.add_question(question_id, ocr_text, preset_analysis, phash, self.dummy_image_path)

        # 模拟OCR返回相同的文本，尽管在这个流程中它不应该被调用
        mock_get_text.return_value = [ocr_text]

        master_analysis, _, cache_status, _ = intelligent_search_logic(user, self.dummy_image_path)

        self.assertIsNotNone(master_analysis)
        self.assertEqual(master_analysis['subject'], "历史")
        self.assertEqual(cache_status, "phash_hit")
        mock_get_analysis.assert_not_called()
        self.assertEqual(len(history_management.load_history()), 1)

    @classmethod
    def tearDownClass(cls):
        """所有测试结束后，清理测试目录和文件。"""
        import shutil
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

if __name__ == '__main__':
    unittest.main()
