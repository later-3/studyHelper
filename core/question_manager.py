import json
import hashlib
import datetime
import imagehash
from PIL import Image
import logging

logger = logging.getLogger(__name__)

BANK_FILE = '/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/data/question_bank.json'
PHASH_MAP_FILE = '/Users/xulater/studyHelper/studyhelper-demo/studyhelper-demo-final/data/phash_to_question_id.json'

def _normalize_text(text: str) -> str:
    return "".join(text.split()).lower()

def generate_question_id(text: str) -> str:
    normalized = _normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def generate_phash(image_path: str) -> str:
    try:
        with Image.open(image_path) as img:
            return str(imagehash.phash(img))
    except Exception as e:
        logger.error(f"Failed to generate phash for {image_path}: {e}")
        return None

def load_bank():
    try:
        with open(BANK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_phash_map():
    try:
        with open(PHASH_MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_question_by_id(question_id: str):
    bank = load_bank()
    return bank.get(question_id)

def get_question_id_by_phash(phash: str):
    phash_map = load_phash_map()
    return phash_map.get(phash)

def is_valid_question_data(question_data: dict) -> bool:
    """检查问题数据是否有效"""
    if not question_data:
        return False
    
    # 检查是否有有效的OCR文本
    canonical_text = question_data.get('canonical_text', '')
    if not canonical_text or canonical_text in ['识别失败', '识别异常']:
        return False
    
    # 检查是否有有效的AI分析结果
    master_analysis = question_data.get('master_analysis', {})
    if not master_analysis or not isinstance(master_analysis, dict):
        return False
    
    # 检查AI分析结果是否有基本内容
    if not master_analysis.get('subject') and not master_analysis.get('solution_steps'):
        return False
    
    return True

def add_question(question_id: str, text: str, analysis: dict, phash: str, image_path: str):
    bank = load_bank()
    phash_map = load_phash_map()

    # 检查文本是否有效
    if not text or text in ['识别失败', '识别异常']:
        logger.warning(f"Invalid OCR text: {text}, skipping question addition")
        return False

    if question_id in bank:
        # 更新现有问题
        known_hashes = bank[question_id].get('known_p_hashes', [])
        if phash and phash not in known_hashes:
            known_hashes.append(phash)
        bank[question_id]['known_p_hashes'] = known_hashes
        
        # 如果新的分析结果更好，更新它
        if analysis and isinstance(analysis, dict):
            bank[question_id]['master_analysis'] = analysis
            bank[question_id]['canonical_text'] = text
    else:
        # 创建新问题
        bank[question_id] = {
            "question_id": question_id,
            "canonical_text": text,
            "first_submission_image": image_path,
            "subject": analysis.get("subject", "未指定") if analysis else "未指定",
            "master_analysis": analysis if analysis else {},
            "first_seen_timestamp": datetime.datetime.now().isoformat(),
            "known_p_hashes": [phash] if phash else []
        }
    
    # 更新phash映射
    if phash:
        phash_map[phash] = question_id

    # 保存数据
    try:
        with open(BANK_FILE, 'w', encoding='utf-8') as f:
            json.dump(bank, f, ensure_ascii=False, indent=4)
        with open(PHASH_MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(phash_map, f, ensure_ascii=False, indent=4)
        logger.info(f"Successfully saved question {question_id} with phash {phash}")
        return True
    except Exception as e:
        logger.error(f"Failed to save question data: {e}")
        return False

def cleanup_invalid_data():
    """清理无效的数据"""
    bank = load_bank()
    phash_map = load_phash_map()
    cleaned_phash_map = {}
    
    # 清理无效的问题数据
    valid_question_ids = set()
    for question_id, question_data in list(bank.items()):
        if is_valid_question_data(question_data):
            valid_question_ids.add(question_id)
        else:
            logger.warning(f"Removing invalid question data: {question_id}")
            del bank[question_id]
    
    # 清理phash映射
    for phash, question_id in phash_map.items():
        if question_id in valid_question_ids:
            cleaned_phash_map[phash] = question_id
        else:
            logger.warning(f"Removing invalid phash mapping: {phash} -> {question_id}")
    
    # 保存清理后的数据
    try:
        with open(BANK_FILE, 'w', encoding='utf-8') as f:
            json.dump(bank, f, ensure_ascii=False, indent=4)
        with open(PHASH_MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned_phash_map, f, ensure_ascii=False, indent=4)
        logger.info("Successfully cleaned up invalid data")
        return True
    except Exception as e:
        logger.error(f"Failed to cleanup data: {e}")
        return False