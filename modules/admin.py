import sqlite3
from database import get_db, format_number

class AdminSystem:
    def add_money(self, user_id, amount):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            return True, f"تم إضافة {format_number(amount)} ريال إلى حساب المستخدم {user_id} ✅"
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def remove_money(self, user_id, amount):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            return True, f"تم خصم {format_number(amount)} ريال من حساب المستخدم {user_id} ✅"
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def ban_user(self, user_id, reason, admin_id):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO bans (user_id, reason, banned_by) VALUES (?, ?, ?)",
                     (user_id, reason, admin_id))
            conn.commit()
            return True, f"تم حظر المستخدم {user_id} ✅"
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def unban_user(self, user_id):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
            conn.commit()
            return True, f"تم إلغاء حظر المستخدم {user_id} ✅"
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()