"""
مُحمل API Keys من ملف api.txt
API Keys Loader from api.txt file
"""

import logging
import os
from typing import Dict, List, Optional


class APIKeysLoader:
    """مُحمل مفاتيح API من ملف api.txt"""
    
    def __init__(self, file_path: str = "api.txt"):
        self.file_path = file_path
        self.api_keys = {}
        self.bot_tokens = []
        self.ai_keys = []
        self.youtube_key = None
        self.load_keys()
    
    def load_keys(self):
        """تحميل جميع المفاتيح من الملف"""
        try:
            if not os.path.exists(self.file_path):
                logging.warning(f"ملف {self.file_path} غير موجود")
                return
                
            with open(self.file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            current_key_type = None
            
            for line in lines:
                line = line.strip()
                if not line:  # تجاهل الأسطر الفارغة
                    continue
                    
                # التحقق من نوع المفتاح
                if line.lower().startswith('ai '):
                    current_key_type = 'ai'
                    continue
                elif line.lower().startswith('tokenbot'):
                    current_key_type = 'bot_token'
                    continue
                elif line.lower().startswith('apiyutube'):
                    current_key_type = 'youtube'
                    continue
                elif line.lower().startswith('openai'):
                    current_key_type = 'openai'
                    continue
                elif line.lower().startswith('anthropic'):
                    current_key_type = 'anthropic'
                    continue
                
                # معالجة القيم حسب النوع
                if current_key_type == 'ai' and line.startswith('AIzaSy'):
                    self.ai_keys.append(line)
                    logging.info(f"تم تحميل مفتاح AI: {line[:10]}...")
                elif current_key_type == 'bot_token' and ':' in line:
                    self.bot_tokens.append(line)
                    self.api_keys['BOT_TOKEN'] = line
                    logging.info(f"تم تحميل توكن البوت: {line.split(':')[0]}...")
                elif current_key_type == 'youtube' and line.startswith('AIzaSy'):
                    self.youtube_key = line
                    self.api_keys['YOUTUBE_API_KEY'] = line
                    logging.info(f"تم تحميل مفتاح YouTube: {line[:10]}...")
                elif current_key_type == 'openai' and line.startswith('sk-'):
                    self.api_keys['OPENAI_API_KEY'] = line
                    logging.info(f"تم تحميل مفتاح OpenAI: {line[:10]}...")
                elif current_key_type == 'anthropic' and line.startswith('sk-ant-'):
                    self.api_keys['ANTHROPIC_API_KEY'] = line
                    logging.info(f"تم تحميل مفتاح Anthropic: {line[:15]}...")
            
            # تعيين مفاتيح Gemini (استخدام أول مفتاح AI كمفتاح أساسي)
            if self.ai_keys:
                self.api_keys['GEMINI_API_KEY'] = self.ai_keys[0]
                self.api_keys['GOOGLE_API_KEY'] = self.ai_keys[0]
                logging.info(f"تم تعيين مفتاح Gemini الأساسي: {self.ai_keys[0][:10]}...")
            
            logging.info(f"تم تحميل {len(self.api_keys)} مفاتيح من {self.file_path}")
            
        except Exception as e:
            logging.error(f"خطأ في تحميل ملف المفاتيح: {e}")
    
    def get_key(self, key_name: str) -> Optional[str]:
        """الحصول على مفتاح محدد"""
        return self.api_keys.get(key_name)
    
    def get_random_ai_key(self) -> Optional[str]:
        """الحصول على مفتاح AI عشوائي"""
        import random
        if self.ai_keys:
            return random.choice(self.ai_keys)
        return None
    
    def get_all_ai_keys(self) -> List[str]:
        """الحصول على جميع مفاتيح AI"""
        return self.ai_keys.copy()
    
    def set_environment_variables(self):
        """تعيين متغيرات البيئة من المفاتيح المحملة"""
        for key, value in self.api_keys.items():
            os.environ[key] = value
            logging.debug(f"تم تعيين متغير البيئة: {key}")
    
    def reload_keys(self):
        """إعادة تحميل المفاتيح من الملف"""
        self.api_keys.clear()
        self.ai_keys.clear()
        self.bot_tokens.clear()
        self.youtube_key = None
        self.load_keys()
    
    def get_status(self) -> Dict[str, any]:
        """الحصول على حالة المفاتيح المحملة"""
        return {
            'total_keys': len(self.api_keys),
            'ai_keys_count': len(self.ai_keys),
            'bot_tokens_count': len(self.bot_tokens),
            'has_youtube_key': self.youtube_key is not None,
            'has_gemini_key': 'GEMINI_API_KEY' in self.api_keys,
            'has_openai_key': 'OPENAI_API_KEY' in self.api_keys,
            'has_anthropic_key': 'ANTHROPIC_API_KEY' in self.api_keys,
            'has_bot_token': 'BOT_TOKEN' in self.api_keys,
            'keys_loaded': list(self.api_keys.keys())
        }


# إنشاء مثيل المُحمل العام
api_loader = APIKeysLoader()