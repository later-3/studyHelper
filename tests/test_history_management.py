import unittest
import os
import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.history_management import (
    load_history,
    save_submission,
    get_all_user_submissions,
    get_class_submissions
)

class TestHistoryManagement(unittest.TestCase):

    def setUp(self):
        """每个测试前都创建一个临时的、空的历史文件。"""
        self.test_file = f'test_history_{uuid.uuid4()}.json'
        import history_management
        history_management.HISTORY_FILE = self.test_file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

    def tearDown(self):
        """每个测试后都删除临时文件。"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_load_history_empty(self):
        """测试加载一个空的历史文件。"""
        self.assertEqual(load_history(), [])

    def test_save_and_load_submission(self):
        """测试保存和加载一条记录。"""
        save_submission("user1", "q1", "1+1=2")
        history = load_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['user_id'], "user1")
        self.assertEqual(history[0]['question_id'], "q1")

    def test_get_all_user_submissions(self):
        """测试根据用户ID筛选记录。"""
        save_submission("user1", "q1", "t1")
        save_submission("user2", "q2", "t2")
        save_submission("user1", "q3", "t3")
        
        user1_subs = get_all_user_submissions("user1")
        self.assertEqual(len(user1_subs), 2)
        user3_subs = get_all_user_submissions("user3")
        self.assertEqual(len(user3_subs), 0)

    def test_get_submissions_by_class(self):
        """测试根据班级（学生ID列表）筛选记录。"""
        save_submission("student_A", "q1", "t1")
        save_submission("student_B", "q2", "t2")
        save_submission("student_C", "q3", "t3")

        class1_students = ["student_A", "student_B"]
        class1_subs = get_class_submissions(class1_students)
        self.assertEqual(len(class1_subs), 2)

        class2_students = ["student_D"]
        class2_subs = get_class_submissions(class2_students)
        self.assertEqual(len(class2_subs), 0)

    def test_submission_with_ai_analysis_only(self):
        """测试仅在submission中有ai_analysis字段时，答题历史应能正确显示。"""
        # 构造一条只在submission中有ai_analysis的记录
        ai_analysis = {
            "subject": "物理",
            "is_correct": True,
            "error_analysis": "",
            "correct_answer": "F=ma",
            "solution_steps": "牛顿第二定律",
            "knowledge_point": "力学基础",
            "common_mistakes": "公式记错"
        }
        submission = {
            "submission_id": str(uuid.uuid4()),
            "user_id": "user1",
            "timestamp": "2025-07-12T10:00:00",
            "subject": "物理",
            "image_path": "data/submissions/user1/physics.png",
            "ocr_text": "F=ma",
            "ai_analysis": ai_analysis
        }
        # 保存到历史
        with open(self.test_file, 'w', encoding='utf-8') as f:
            json.dump([submission], f)
        # 加载历史
        history = load_history()
        self.assertEqual(len(history), 1)
        self.assertIn('ai_analysis', history[0])
        self.assertEqual(history[0]['ai_analysis']['subject'], "物理")
        self.assertTrue(history[0]['ai_analysis']['is_correct'])

    def test_multi_subject_and_correctness(self):
        """测试不同学科、对错的题目都能被收录（兼容老格式和新格式）。"""
        # 1. 老格式：只存question_id，题库查找
        # 构造题库
        question_bank = {
            "q1": {
                "question_id": "q1",
                "canonical_text": "白日依山尽",
                "subject": "语文",
                "master_analysis": {"is_correct": True, "subject": "语文"}
            },
            "q2": {
                "question_id": "q2",
                "canonical_text": "1+1=3",
                "subject": "数学",
                "master_analysis": {"is_correct": False, "subject": "数学"}
            }
        }
        # 保存两条老格式记录
        save_submission("user1", "q1", "白日依山尽")
        save_submission("user1", "q2", "1+1=3")
        # 2. 新格式：submission有ai_analysis
        submission = {
            "submission_id": str(uuid.uuid4()),
            "user_id": "user1",
            "timestamp": "2025-07-12T11:00:00",
            "subject": "英语",
            "image_path": "data/submissions/user1/english.png",
            "ocr_text": "My name are Bob.",
            "ai_analysis": {
                "subject": "英语",
                "is_correct": False,
                "error_analysis": "主谓不一致",
                "correct_answer": "My name is Bob.",
                "solution_steps": "主语单数用is",
                "knowledge_point": "主谓一致",
                "common_mistakes": "are/is混用"
            }
        }
        with open(self.test_file, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data.append(submission)
            f.seek(0)
            json.dump(data, f)
            f.truncate()
        # 3. 检查所有学科和对错都被收录
        history = load_history()
        subjects = set()
        correctness = set()
        for sub in history:
            if 'ai_analysis' in sub:
                subjects.add(sub['ai_analysis'].get('subject'))
                correctness.add(sub['ai_analysis'].get('is_correct'))
            else:
                # 老格式，查题库
                qid = sub.get('question_id')
                q = question_bank.get(qid)
                if q:
                    subjects.add(q.get('subject'))
                    correctness.add(q.get('master_analysis', {}).get('is_correct'))
        self.assertIn("英语", subjects)
        self.assertIn("语文", subjects)
        self.assertIn("数学", subjects)
        self.assertIn(True, correctness)
        self.assertIn(False, correctness)

if __name__ == '__main__':
    unittest.main()