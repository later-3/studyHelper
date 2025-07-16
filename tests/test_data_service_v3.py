"""
DataServiceV3 测试用例
测试重构后的数据服务功能
"""

import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_service_v3 import DataServiceV3
from core.logger_config import setup_logger

logger = setup_logger('test_data_service_v3', level='DEBUG')

class TestDataServiceV3:
    """DataServiceV3 测试类"""
    
    @pytest.fixture
    def mock_db_config(self):
        """模拟数据库配置"""
        return {
            'host': 'localhost',
            'port': '5432',
            'database': 'test_studyhelper',
            'user': 'test_user',
            'password': 'test_password'
        }
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = MagicMock()
        session.execute.return_value = MagicMock()
        session.commit.return_value = None
        session.__enter__.return_value = session
        return session
    
    @pytest.fixture
    def data_service(self, mock_db_config):
        """创建测试用的DataServiceV3实例"""
        with patch('services.data_service_v3.DataServiceV3._get_database_url') as mock_url:
            mock_url.return_value = "postgresql://test_user:test_password@localhost:5432/test_studyhelper"
            
            with patch('services.data_service_v3.create_engine') as mock_engine:
                mock_engine_instance = MagicMock()
                # 支持 with self.engine.connect() as conn:
                mock_conn = MagicMock()
                mock_engine_instance.connect.return_value.__enter__.return_value = mock_conn
                mock_engine.return_value = mock_engine_instance
                
                with patch('services.data_service_v3.sessionmaker') as mock_sessionmaker:
                    mock_sessionmaker.return_value = MagicMock()
                    
                    service = DataServiceV3()
                    return service
    
    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            'id': 'student_01',
            'name': '小明',
            'role': 'student',
            'email': 'xiaoming@test.com',
            'school_id': 'school_01',
            'grade_id': 'grade_05',
            'class_id': 'class_01'
        }
    
    @pytest.fixture
    def sample_submission_data(self):
        """示例提交数据"""
        return {
            'id': 'sub_001',
            'user_id': 'student_01',
            'question_id': 'q_001',
            'submitted_ocr_text': '1+1=2',
            'image_path': 'data/submissions/test.png',
            'subject': '数学',
            'timestamp': datetime.now().isoformat(),
            'processing_status': 'completed'
        }
    
    @pytest.fixture
    def sample_question_data(self):
        """示例题目数据"""
        return {
            'id': 'q_001',
            'canonical_text': '1+1=2',
            'subject': '数学',
            'difficulty_level': 1,
            'knowledge_points': ['基础加法'],
            'tags': ['简单'],
            'first_submission_image': 'data/submissions/test.png',
            'total_submissions': 1,
            'correct_submissions': 1,
            'accuracy_rate': 100.0,
            'status': 'active'
        }

    def test_init_with_custom_database_url(self):
        """测试使用自定义数据库URL初始化"""
        with patch('services.data_service_v3.create_engine') as mock_engine:
            mock_engine_instance = MagicMock()
            # 支持 with self.engine.connect() as conn:
            mock_conn = MagicMock()
            mock_engine_instance.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.return_value = mock_engine_instance
            
            with patch('services.data_service_v3.sessionmaker') as mock_sessionmaker:
                mock_sessionmaker.return_value = MagicMock()
                
                custom_url = "postgresql://custom:pass@host:5432/db"
                service = DataServiceV3(custom_url)
                
                assert service.database_url == custom_url
                mock_engine.assert_called_once()

    def test_get_session(self, data_service):
        """测试获取数据库会话"""
        with patch.object(data_service, 'SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            
            session = data_service.get_session()
            
            assert session == mock_session
            mock_session_local.assert_called_once()

    def test_get_user_submissions_student_role(self, data_service, mock_session):
        """测试学生角色获取提交记录"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'sub_001',
            'user_id': 'student_01',
            'submitted_ocr_text': '1+1=2',
            'subject': '数学',
            'is_correct': True,
            'user_name': '小明',
            'user_role': 'student'
        }
        mock_session.execute.return_value = [mock_result]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            submissions = data_service.get_user_submissions('student_01', role='student')
            
            assert len(submissions) == 1
            assert submissions[0]['user_id'] == 'student_01'
            assert submissions[0]['submitted_ocr_text'] == '1+1=2'

    def test_get_user_submissions_teacher_role(self, data_service, mock_session):
        """测试教师角色获取提交记录"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'sub_002',
            'user_id': 'student_02',
            'submitted_ocr_text': '2+2=4',
            'subject': '数学',
            'is_correct': True,
            'user_name': '小红',
            'user_role': 'student'
        }
        mock_session.execute.return_value = [mock_result]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            submissions = data_service.get_user_submissions('teacher_01', role='teacher')
            
            assert len(submissions) == 1
            assert submissions[0]['user_id'] == 'student_02'

    def test_get_user_submissions_invalid_role(self, data_service):
        """测试无效角色获取提交记录"""
        submissions = data_service.get_user_submissions('user_01', role='invalid_role')
        assert submissions == []

    def test_get_submissions_by_user(self, data_service):
        """测试获取指定用户的提交记录（兼容性方法）"""
        with patch.object(data_service, 'get_user_submissions') as mock_get:
            mock_get.return_value = [{'id': 'sub_001'}]
            
            result = data_service.get_submissions_by_user('student_01')
            
            mock_get.assert_called_once_with('student_01', role='student')
            assert result == [{'id': 'sub_001'}]

    def test_get_submissions_by_question(self, data_service, mock_session):
        """测试获取指定题目的提交记录"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'sub_001',
            'user_id': 'student_01',
            'question_id': 'q_001',
            'submitted_ocr_text': '1+1=2',
            'user_name': '小明'
        }
        mock_session.execute.return_value = [mock_result]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            submissions = data_service.get_submissions_by_question('student_01', 'q_001')
            
            assert len(submissions) == 1
            assert submissions[0]['question_id'] == 'q_001'

    def test_group_submissions_by_question(self, data_service):
        """测试按题目分组提交记录"""
        submissions = [
            {'question_id': 'q_001', 'timestamp': '2025-01-01T10:00:00'},
            {'question_id': 'q_001', 'timestamp': '2025-01-01T11:00:00'},
            {'question_id': 'q_002', 'timestamp': '2025-01-01T12:00:00'},
            {'ocr_text': 'test', 'timestamp': '2025-01-01T13:00:00'}  # 没有question_id
        ]
        
        grouped = data_service.group_submissions_by_question(submissions)
        
        assert 'q_001' in grouped
        assert 'q_002' in grouped
        assert len(grouped['q_001']) == 2
        assert len(grouped['q_002']) == 1
        # 验证按时间倒序排序
        assert grouped['q_001'][0]['timestamp'] == '2025-01-01T11:00:00'

    def test_get_submission_stats_empty(self, data_service):
        """测试空提交记录的统计"""
        stats = data_service.get_submission_stats([])
        
        assert stats['total_count'] == 0
        assert stats['correct_count'] == 0
        assert stats['incorrect_count'] == 0
        assert stats['accuracy_rate'] == 0
        assert stats['subject_distribution'] == {}
        assert stats['recent_activity'] == {}

    def test_get_submission_stats_with_data(self, data_service):
        """测试有数据的提交记录统计"""
        submissions = [
            {
                'is_correct': True,
                'subject': '数学',
                'timestamp': datetime.now().isoformat()
            },
            {
                'is_correct': False,
                'subject': '数学',
                'timestamp': datetime.now().isoformat()
            },
            {
                'is_correct': True,
                'subject': '语文',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        stats = data_service.get_submission_stats(submissions)
        
        assert stats['total_count'] == 3
        assert stats['correct_count'] == 2
        assert stats['incorrect_count'] == 1
        assert stats['accuracy_rate'] == 66.67
        assert stats['subject_distribution']['数学'] == 2
        assert stats['subject_distribution']['语文'] == 1

    def test_get_question_details(self, data_service, mock_session):
        """测试获取题目详细信息"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'q_001',
            'canonical_text': '1+1=2',
            'subject': '数学',
            'difficulty_level': 1
        }
        mock_session.execute.return_value.fetchone.return_value = mock_result
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            question = data_service.get_question_details('q_001')
            
            assert question['id'] == 'q_001'
            assert question['canonical_text'] == '1+1=2'

    def test_get_question_details_not_found(self, data_service, mock_session):
        """测试获取不存在的题目详情"""
        mock_session.execute.return_value.fetchone.return_value = None
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            question = data_service.get_question_details('nonexistent')
            
            assert question is None

    def test_get_user_info(self, data_service, mock_session):
        """测试获取用户信息"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'student_01',
            'name': '小明',
            'role': 'student',
            'school_name': '测试学校',
            'grade_name': '五年级',
            'class_name': '一班'
        }
        mock_session.execute.return_value.fetchone.return_value = mock_result
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            user_info = data_service.get_user_info('student_01')
            
            assert user_info['id'] == 'student_01'
            assert user_info['name'] == '小明'
            assert user_info['school_name'] == '测试学校'

    def test_get_class_info(self, data_service, mock_session):
        """测试获取班级信息"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'class_01',
            'name': '五年级一班',
            'grade_name': '五年级',
            'school_name': '测试学校',
            'teacher_name': '张老师'
        }
        mock_session.execute.return_value.fetchone.return_value = mock_result
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            class_info = data_service.get_class_info('class_01')
            
            assert class_info['id'] == 'class_01'
            assert class_info['name'] == '五年级一班'
            assert class_info['teacher_name'] == '张老师'

    def test_get_student_performance(self, data_service, mock_session):
        """测试获取学生表现数据"""
        # 模拟统计查询结果
        mock_stats_result = MagicMock()
        mock_stats_result._mapping = {
            'total_submissions': 10,
            'analyzed_submissions': 8,
            'correct_submissions': 6,
            'accuracy_rate': 75.0
        }
        
        # 模拟学科分布查询结果
        mock_subject_result = MagicMock()
        mock_subject_result.subject = '数学'
        mock_subject_result.count = 5
        
        # 模拟最近活动查询结果
        mock_activity_result = MagicMock()
        mock_activity_result.date = datetime.now().date()
        mock_activity_result.count = 2
        
        mock_session.execute.side_effect = [
            Mock(fetchone=Mock(return_value=mock_stats_result)),
            [mock_subject_result],
            [mock_activity_result]
        ]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            performance = data_service.get_student_performance('student_01')
            
            assert performance['total_submissions'] == 10
            assert performance['accuracy_rate'] == 75.0
            assert performance['subject_distribution']['数学'] == 5
            assert str(datetime.now().date()) in performance['recent_activity']

    def test_get_student_performance_error(self, data_service, mock_session):
        """测试获取学生表现数据时发生错误"""
        mock_session.execute.side_effect = Exception("Database error")
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            performance = data_service.get_student_performance('student_01')
            assert performance['total_submissions'] == 0
            assert performance['accuracy_rate'] == 0

    def test_get_class_performance(self, data_service, mock_session):
        """测试获取班级表现数据"""
        # 模拟统计查询结果
        mock_stats_result = MagicMock()
        mock_stats_result._mapping = {
            'student_count': 30,
            'total_submissions': 150,
            'analyzed_submissions': 120,
            'correct_submissions': 90,
            'accuracy_rate': 75.0
        }
        
        # 模拟学科表现查询结果
        mock_subject_result = MagicMock()
        mock_subject_result.subject = '数学'
        mock_subject_result.total = 50
        mock_subject_result.correct = 40
        mock_subject_result.accuracy = 80.0
        
        # 模拟需要关注的学生查询结果
        mock_attention_result = MagicMock()
        mock_attention_result.id = 'student_01'
        mock_attention_result.name = '小明'
        mock_attention_result.submission_count = 10
        mock_attention_result.correct_count = 5
        mock_attention_result.accuracy_rate = 50.0
        
        mock_session.execute.side_effect = [
            Mock(fetchone=Mock(return_value=mock_stats_result)),
            [mock_subject_result],
            [mock_attention_result]
        ]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            performance = data_service.get_class_performance('class_01')
            
            assert performance['student_count'] == 30
            assert performance['accuracy_rate'] == 75.0
            assert performance['subject_performance']['数学']['total'] == 50
            assert len(performance['needs_attention_students']) == 1
            assert performance['needs_attention_students'][0]['name'] == '小明'

    def test_search_submissions_student_role(self, data_service, mock_session):
        """测试学生角色搜索提交记录"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'sub_001',
            'user_id': 'student_01',
            'subject': '数学',
            'is_correct': True
        }
        mock_session.execute.return_value = [mock_result]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            submissions = data_service.search_submissions(
                'student_01', 
                'student',
                subjects=['数学'],
                correctness=[True],
                limit=10
            )
            
            assert len(submissions) == 1
            assert submissions[0]['subject'] == '数学'

    def test_search_submissions_with_date_range(self, data_service, mock_session):
        """测试带日期范围的搜索提交记录"""
        mock_session.execute.return_value = []
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            submissions = data_service.search_submissions(
                'student_01',
                'student',
                date_range=('2025-01-01', '2025-01-31')
            )
            
            # 验证SQL查询包含日期过滤
            mock_session.execute.assert_called_once()
            call_args = mock_session.execute.call_args[0]
            assert 'BETWEEN' in str(call_args[0])

    def test_get_mistake_book_entries(self, data_service, mock_session):
        """测试获取错题本条目"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'mistake_001',
            'user_id': 'student_01',
            'subject': '数学',
            'knowledge_point': '分数计算',
            'mastery_level': 2,
            'submitted_ocr_text': '1/2 + 1/3 = ?'
        }
        mock_session.execute.return_value = [mock_result]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            entries = data_service.get_mistake_book_entries('student_01')
            
            assert len(entries) == 1
            assert entries[0]['subject'] == '数学'
            assert entries[0]['mastery_level'] == 2

    def test_create_mistake_book_entry(self, data_service, mock_session):
        """测试创建错题本条目"""
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            success = data_service.create_mistake_book_entry(
                'student_01',
                'sub_001',
                'q_001',
                '数学',
                '分数计算'
            )
            
            assert success is True
            mock_session.commit.assert_called_once()

    def test_create_mistake_book_entry_error(self, data_service, mock_session):
        """测试创建错题本条目时发生错误"""
        mock_session.execute.side_effect = Exception("Database error")
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            success = data_service.create_mistake_book_entry(
                'student_01',
                'sub_001'
            )
            assert success is False

    def test_update_mistake_book_entry(self, data_service, mock_session):
        """测试更新错题本条目"""
        mock_session.execute.return_value = None
        mock_session.commit.return_value = None
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            success = data_service.update_mistake_book_entry(
                'mistake_001',
                mastery_level=3,
                notes='需要加强练习',
                tags=['重要', '易错']
            )
            
            assert success is True
            mock_session.commit.assert_called_once()

    def test_update_mistake_book_entry_no_changes(self, data_service, mock_session):
        """测试更新错题本条目但没有变化"""
        with patch.object(data_service, 'get_session', return_value=mock_session):
            success = data_service.update_mistake_book_entry('mistake_001')
            
            assert success is False
            mock_session.execute.assert_not_called()

    def test_get_analytics_data_student_role(self, data_service, mock_session):
        """测试获取学生角色的分析数据"""
        # 模拟统计查询结果
        mock_stats_result = MagicMock()
        mock_stats_result._mapping = {
            'total_submissions': 20,
            'analyzed_submissions': 18,
            'correct_submissions': 15,
            'accuracy_rate': 83.33
        }
        
        # 模拟学科分布查询结果
        mock_subject_result = MagicMock()
        mock_subject_result.subject = '数学'
        mock_subject_result.count = 10
        
        # 模拟每日活动查询结果
        mock_activity_result = MagicMock()
        mock_activity_result.date = datetime.now().date()
        mock_activity_result.count = 3
        
        mock_session.execute.side_effect = [
            Mock(fetchone=Mock(return_value=mock_stats_result)),
            [mock_subject_result],
            [mock_activity_result]
        ]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            analytics = data_service.get_analytics_data('student_01', 'student')
            
            assert analytics['total_submissions'] == 20
            assert analytics['accuracy_rate'] == 83.33
            assert analytics['subject_distribution']['数学'] == 10
            assert str(datetime.now().date()) in analytics['daily_activity']

    def test_get_analytics_data_with_date_range(self, data_service, mock_session):
        """测试带日期范围的分析数据"""
        mock_session.execute.side_effect = [
            Mock(fetchone=Mock(return_value=Mock(_mapping={
                'total_submissions': 0,
                'analyzed_submissions': 0,
                'correct_submissions': 0,
                'accuracy_rate': 0
            }))),
            [],
            []
        ]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            analytics = data_service.get_analytics_data(
                'student_01',
                'student',
                start_date='2025-01-01',
                end_date='2025-01-31'
            )
            
            # 验证SQL查询包含日期过滤
            mock_session.execute.assert_called()
            call_args = mock_session.execute.call_args_list[0][0]
            assert 'BETWEEN' in str(call_args[0])

    def test_get_analytics_data_error(self, data_service, mock_session):
        """测试获取分析数据时发生错误"""
        mock_session.execute.side_effect = Exception("Database error")
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            analytics = data_service.get_analytics_data('student_01', 'student')
            assert analytics == {}

    def test_close(self, data_service):
        """测试关闭数据服务"""
        with patch.object(data_service, 'engine') as mock_engine:
            data_service.close()
            mock_engine.dispose.assert_called_once()

    def test_database_connection_error(self):
        """测试数据库连接错误"""
        with patch('services.data_service_v3.create_engine') as mock_engine:
            mock_engine.side_effect = Exception("Connection failed")
            
            with patch('services.data_service_v3.sessionmaker') as mock_sessionmaker:
                mock_sessionmaker.return_value = MagicMock()
                with pytest.raises(Exception):
                    DataServiceV3()

    def test_session_error_handling(self, data_service, mock_session):
        """测试会话错误处理"""
        mock_session.execute.side_effect = Exception("SQL error")
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            # 测试各种方法在数据库错误时的行为
            submissions = data_service.get_user_submissions('student_01', 'student')
            assert submissions == []
            
            question = data_service.get_question_details('q_001')
            assert question is None
            
            user_info = data_service.get_user_info('student_01')
            assert user_info is None

    def test_performance_with_large_dataset(self, data_service, mock_session):
        """测试大数据集性能"""
        # 模拟大量数据
        large_dataset = []
        for i in range(1000):
            mock_result = MagicMock()
            mock_result._mapping = {
                'id': f'sub_{i:03d}',
                'user_id': 'student_01',
                'submitted_ocr_text': f'Question {i}',
                'subject': '数学',
                'is_correct': i % 2 == 0,
                'timestamp': datetime.now().isoformat()
            }
            large_dataset.append(mock_result)
        
        mock_session.execute.return_value = large_dataset
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            submissions = data_service.get_user_submissions('student_01', 'student')
            
            assert len(submissions) == 1000
            # 验证数据完整性
            assert all('id' in sub for sub in submissions)
            assert all('user_id' in sub for sub in submissions)

    def test_edge_cases(self, data_service):
        """测试边界情况"""
        # 测试空字符串输入
        submissions = data_service.get_user_submissions('', 'student')
        assert submissions == []
        
        # 测试None输入
        submissions = data_service.get_user_submissions(None, 'student')
        assert submissions == []
        
        # 测试特殊字符
        submissions = data_service.get_user_submissions('user@#$%', 'student')
        assert submissions == []

    def test_data_consistency(self, data_service, mock_session):
        """测试数据一致性"""
        # 模拟一致的查询结果
        mock_result = MagicMock()
        mock_result._mapping = {
            'id': 'sub_001',
            'user_id': 'student_01',
            'question_id': 'q_001',
            'submitted_ocr_text': '1+1=2',
            'subject': '数学',
            'is_correct': True,
            'timestamp': '2025-01-01T10:00:00'
        }
        mock_session.execute.return_value = [mock_result]
        mock_session.__enter__.return_value = mock_session
        
        with patch.object(data_service, 'get_session', return_value=mock_session):
            # 多次调用应该返回相同结果
            result1 = data_service.get_user_submissions('student_01', 'student')
            result2 = data_service.get_user_submissions('student_01', 'student')
            
            assert result1 == result2
            assert len(result1) == 1
            assert result1[0]['id'] == 'sub_001' 