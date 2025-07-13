#!/usr/bin/env python3
"""
数据清理脚本
删除包含"(Image match)"和无效OCR文本的记录
"""

import json
import os
import logging
from typing import List, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 文件路径
SUBMISSION_HISTORY_FILE = 'data/submission_history.json'
QUESTION_BANK_FILE = 'data/question_bank.json'

def is_bad_submission(submission: Dict[str, Any]) -> bool:
    """
    判断是否为不好的提交记录
    """
    submitted_text = submission.get('submitted_ocr_text', '')
    
    # 检查是否为"(Image match)"
    if submitted_text == "(Image match)":
        return True
    
    # 检查是否为无效的OCR文本（包含大量换行符的乱码）
    if submitted_text and '\n' in submitted_text:
        lines = submitted_text.split('\n')
        # 如果大部分行都是单个字符，可能是OCR错误
        single_char_lines = sum(1 for line in lines if len(line.strip()) == 1)
        if len(lines) > 5 and single_char_lines / len(lines) > 0.7:
            return True
    
    # 检查是否为"识别异常"或"识别失败"
    if submitted_text in ["识别异常", "识别失败"]:
        return True
    
    return False

def is_bad_question(question: Dict[str, Any]) -> bool:
    """
    判断是否为不好的题目记录
    """
    canonical_text = question.get('canonical_text', '')
    
    # 检查是否为无效的OCR文本
    if canonical_text and '\n' in canonical_text:
        lines = canonical_text.split('\n')
        # 如果大部分行都是单个字符，可能是OCR错误
        single_char_lines = sum(1 for line in lines if len(line.strip()) == 1)
        if len(lines) > 5 and single_char_lines / len(lines) > 0.7:
            return True
    
    # 检查是否为空或无效文本
    if not canonical_text or canonical_text.strip() == "":
        return True
    
    return False

def cleanup_submission_history():
    """
    清理答题历史数据
    """
    logger.info("开始清理答题历史数据...")
    
    if not os.path.exists(SUBMISSION_HISTORY_FILE):
        logger.warning(f"文件不存在: {SUBMISSION_HISTORY_FILE}")
        return
    
    try:
        with open(SUBMISSION_HISTORY_FILE, 'r', encoding='utf-8') as f:
            submissions = json.load(f)
        
        original_count = len(submissions)
        logger.info(f"原始记录数: {original_count}")
        
        # 过滤掉不好的记录
        good_submissions = []
        bad_submissions = []
        
        for submission in submissions:
            if is_bad_submission(submission):
                bad_submissions.append(submission)
            else:
                good_submissions.append(submission)
        
        logger.info(f"删除的记录数: {len(bad_submissions)}")
        logger.info(f"保留的记录数: {len(good_submissions)}")
        
        # 显示被删除的记录详情
        for bad_sub in bad_submissions:
            logger.info(f"删除记录: {bad_sub.get('submission_id', 'N/A')} - {bad_sub.get('submitted_ocr_text', 'N/A')}")
        
        # 保存清理后的数据
        with open(SUBMISSION_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(good_submissions, f, ensure_ascii=False, indent=4)
        
        logger.info("答题历史数据清理完成")
        
    except Exception as e:
        logger.error(f"清理答题历史数据时出错: {e}")

def cleanup_question_bank():
    """
    清理题库数据
    """
    logger.info("开始清理题库数据...")
    
    if not os.path.exists(QUESTION_BANK_FILE):
        logger.warning(f"文件不存在: {QUESTION_BANK_FILE}")
        return
    
    try:
        with open(QUESTION_BANK_FILE, 'r', encoding='utf-8') as f:
            question_bank = json.load(f)
        
        original_count = len(question_bank)
        logger.info(f"原始题目数: {original_count}")
        
        # 过滤掉不好的题目
        good_questions = {}
        bad_questions = {}
        
        for question_id, question in question_bank.items():
            if is_bad_question(question):
                bad_questions[question_id] = question
            else:
                good_questions[question_id] = question
        
        logger.info(f"删除的题目数: {len(bad_questions)}")
        logger.info(f"保留的题目数: {len(good_questions)}")
        
        # 显示被删除的题目详情
        for question_id, question in bad_questions.items():
            logger.info(f"删除题目: {question_id} - {question.get('canonical_text', 'N/A')}")
        
        # 保存清理后的数据
        with open(QUESTION_BANK_FILE, 'w', encoding='utf-8') as f:
            json.dump(good_questions, f, ensure_ascii=False, indent=4)
        
        logger.info("题库数据清理完成")
        
    except Exception as e:
        logger.error(f"清理题库数据时出错: {e}")

def main():
    """
    主函数
    """
    logger.info("开始数据清理流程...")
    
    # 清理答题历史
    cleanup_submission_history()
    
    # 清理题库
    cleanup_question_bank()
    
    logger.info("数据清理流程完成")

if __name__ == "__main__":
    main() 