"""
إعدادات البوت
Bot Configuration Package
"""

from .settings import *
from .database import *

__all__ = ['BOT_TOKEN', 'ADMIN_IDS', 'DATABASE_URL', 'init_database']
