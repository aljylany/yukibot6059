import sqlite3
import time
import random
from database import get_db, format_number
from config import SALARY_AMOUNT, MIN_TRANSFER
from modules.leveling import leveling_system  # نظام المستويات الجديد

class BankingSystem:
    def create_account(self, user_id, username, bank_name=None):
        conn = get_db()
        c = conn.cursor()
        try:
            # تحقق إذا كان المستخدم لديه حساب
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            if c.fetchone():
                return False, "لديك حساب بالفعل!"
            
            # إنشاء رقم حساب عشوائي
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
            
            # إضافة المستخدم الجديد
            c.execute("INSERT INTO users (user_id, username, account_number, balance) VALUES (?, ?, ?, ?)",
                     (user_id, username, account_number, 10000))
            conn.commit()
            return True, f"تم إنشاء حسابك بنجاح! رقم حسابك: `{account_number}`"
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def get_balance(self, user_id):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0

    def give_salary(self, user_id):
        conn = get_db()
        c = conn.cursor()
        try:
            # تحقق من آخر مرة أخذ فيها الراتب (كل 5 دقائق)
            c.execute("SELECT last_salary FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            last_salary = row[0] if row else None
            now = time.time()
            
            if last_salary and now - last_salary < 3 * 60:  # 3 دقائق
                remaining = int(3 * 60 - (now - last_salary))
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                return False, f"⏱ عليك الانتظار {minutes} دقائق و {seconds} ثانية لصرف الراتب التالي"
            
            # إعطاء الراتب
            c.execute("UPDATE users SET balance = balance + ?, last_salary = ? WHERE user_id = ?",
                     (SALARY_AMOUNT, now, user_id))
            conn.commit()
            return True, f"💸 تم إضافة راتبك: {format_number(SALARY_AMOUNT)} ريال"
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def update_balance(self, user_id, amount):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def transfer_money(self, sender_id, receiver_id, amount):
        if amount < MIN_TRANSFER:
            return False, f"الحد الأدنى للتحويل هو {format_number(MIN_TRANSFER)} ريال! 💸"
        
        conn = get_db()
        c = conn.cursor()
        try:
            # التحقق من رصيد المرسل
            c.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
            sender_balance = c.fetchone()
            if not sender_balance or sender_balance[0] < amount:
                return False, "رصيدك غير كافي للتحويل! 💸"
            
            # التحقق من وجود المستقبل
            c.execute("SELECT user_id FROM users WHERE user_id = ?", (receiver_id,))
            if not c.fetchone():
                return False, "المستخدم المستهدف ليس لديه حساب في البوت!"
            
            # تنفيذ التحويل
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, receiver_id))
            conn.commit()
            
            return True, f"تم تحويل {format_number(amount)} ريال بنجاح! ✅"
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()
    
    def add_money(self, user_id, amount):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def remove_money(self, user_id, amount):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def get_last_salary_time(self, user_id):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT last_salary FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None