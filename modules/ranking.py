import sqlite3
import random
from database import get_db, format_number

class RankingSystem:
    def get_richest_users(self, limit=10):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        users = c.fetchall()
        conn.close()
        return users

    def get_top_thieves(self, limit=10):
        # في تطبيق حقيقي، سيتم تخزين سجلات السرقة
        # هنا سنستخدم بيانات عشوائية للتوضيح
        return [("User" + str(i), random.randint(1000000, 100000000)) for i in range(1, limit+1)]

    def get_user_rank(self, user_id):
        # في تطبيق حقيقي، سيتم حساب الترتيب بناء على الرصيد
        return random.randint(1, 10000)