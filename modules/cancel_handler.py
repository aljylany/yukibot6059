"""
معالج إلغاء الأوامر المطلقة
Cancel Handler for Ultimate Commands
"""

import logging
from typing import Dict, Optional
import asyncio
from datetime import datetime, timedelta

# قاموس لحفظ الأوامر الجارية والقابلة للإلغاء
ACTIVE_COMMANDS: Dict[int, Dict] = {}  # {user_id: {command_type, start_time, chat_id}}


def start_cancellable_command(user_id: int, command_type: str, chat_id: int) -> None:
    """تسجيل بداية أمر قابل للإلغاء"""
    ACTIVE_COMMANDS[user_id] = {
        'command_type': command_type,
        'start_time': datetime.now(),
        'chat_id': chat_id,
        'cancelled': False
    }
    logging.info(f"بداية أمر قابل للإلغاء: {command_type} للمستخدم {user_id}")


def cancel_command(user_id: int) -> bool:
    """إلغاء الأمر الجاري للمستخدم"""
    if user_id in ACTIVE_COMMANDS and not ACTIVE_COMMANDS[user_id]['cancelled']:
        ACTIVE_COMMANDS[user_id]['cancelled'] = True
        logging.info(f"تم إلغاء الأمر للمستخدم {user_id}")
        return True
    return False


def is_command_cancelled(user_id: int) -> bool:
    """التحقق من إلغاء الأمر"""
    return user_id in ACTIVE_COMMANDS and ACTIVE_COMMANDS[user_id]['cancelled']


def finish_command(user_id: int) -> None:
    """إنهاء الأمر وإزالته من القائمة"""
    if user_id in ACTIVE_COMMANDS:
        del ACTIVE_COMMANDS[user_id]
        logging.info(f"تم إنهاء الأمر للمستخدم {user_id}")


def get_active_command(user_id: int) -> Optional[str]:
    """الحصول على نوع الأمر الجاري"""
    if user_id in ACTIVE_COMMANDS and not ACTIVE_COMMANDS[user_id]['cancelled']:
        return ACTIVE_COMMANDS[user_id]['command_type']
    return None


def cleanup_old_commands() -> None:
    """تنظيف الأوامر القديمة (أكثر من 5 دقائق)"""
    current_time = datetime.now()
    to_remove = []
    
    for user_id, command_info in ACTIVE_COMMANDS.items():
        if current_time - command_info['start_time'] > timedelta(minutes=5):
            to_remove.append(user_id)
    
    for user_id in to_remove:
        del ACTIVE_COMMANDS[user_id]