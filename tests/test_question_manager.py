import unittest
import os
import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.question_manager import (
    generate_question_id,
    load_bank,
    get_question_by_id,
    add_question
)

class TestQuestionManager(unittest.TestCase):

    def setUp(self):
        """为每个测试创建一个临时的题库文件。"""
        self.test_file = f'test_bank_{uuid.uuid4()}.json'
        import question_manager
        question_manager.BANK_FILE = self.test_file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)

    def tearDown(self):
        """测试后删除临时文件。"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_generate_question_id_stability(self):
        """测试ID生成的稳定性。"""
        text1 = "1 + 1 = 3"
        text2 = "1+1=3"
        text3 = " 1 + 1=3 "
        self.assertEqual(generate_question_id(text1), generate_question_id(text2))
        self.assertEqual(generate_question_id(text1), generate_question_id(text3))
        self.assertNotEqual(generate_question_id(text1), generate_question_id("1+1=2"))

    def test_add_and_get_question(self):
        """测试添加和获取题目。"""
        text = "What is the capital of France?"
        q_id = generate_question_id(text)
        analysis = {"subject": "Geography", "correct_answer": "Paris"}
        
        # 初始时应该找不到
        self.assertIsNone(get_question_by_id(q_id))

        # 添加后应该能找到
        add_question(q_id, text, analysis)
        question = get_question_by_id(q_id)
        self.assertIsNotNone(question)
        self.assertEqual(question['canonical_text'], text)
        self.assertEqual(question['master_analysis']['correct_answer'], "Paris")

    def test_add_duplicate_question(self):
        """测试重复添加题目不会覆盖原有数据。"""
        text = "Test question"
        q_id = generate_question_id(text)
        analysis1 = {"subject": "Test", "first_entry": True}
        analysis2 = {"subject": "Test", "first_entry": False}

        add_question(q_id, text, analysis1)
        bank1 = load_bank()
        self.assertTrue(bank1[q_id]['master_analysis']['first_entry'])

        # 尝试用新数据重复添加
        add_question(q_id, text, analysis2)
        bank2 = load_bank()
        # 确认数据没有被覆盖
        self.assertTrue(bank2[q_id]['master_analysis']['first_entry'])

if __name__ == '__main__':
    unittest.main()
