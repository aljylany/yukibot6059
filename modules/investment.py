import random
from database import get_db, format_number
from config import MIN_GAMBLE
from modules.leveling import leveling_system  # نظام المستويات الجديد

class InvestmentSystem:
    def invest_all(self, user_id):
        conn = get_db()
        c = conn.cursor()
        try:
            # الحصول على الرصيد
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            balance = c.fetchone()[0]
            
            if balance < 200:
                return False, "الحد الأدنى للاستثمار هو 200 ريال! 💸"
            
            # نسبة ربح عشوائية بين 5-25%
            profit_percent = random.randint(5, 25)
            profit = int(balance * profit_percent / 100)
            new_balance = balance + profit
            
            # تحديث الرصيد
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            
            return True, (
                f"استثمار ناجح! ✅\n"
                f"نسبة الربح: {profit_percent}%\n"
                f"مبلغ الربح: {format_number(profit)} ريال\n"
                f"رصيدك الجديد: {format_number(new_balance)} ريال 💰"
            )
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def gamble(self, user_id, amount):
        from config import MIN_GAMBLE
        conn = get_db()
        c = conn.cursor()
        try:
            # التحقق من الحد الأدنى
            if amount < MIN_GAMBLE:
                return False, f"الحد الأدنى للمضاربة هو {format_number(MIN_GAMBLE)} ريال! 💸"
            
            # التحقق من الرصيد
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            balance = c.fetchone()[0]
            if balance < amount:
                return False, "رصيدك لا يكفي للمضاربة بهذا المبلغ! ❌"
            
            # نسبة ربح/خسارة عشوائية
            profit_percent = random.randint(-10, 90)  # -10% إلى +90%
            profit = int(amount * profit_percent / 100)
            new_balance = balance + profit
            
            # تحديث الرصيد
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            
            status = "ناجحة" if profit_percent >= 0 else "فاشلة"
            return True, (
                f"مضاربة {status}! {'🎉' if profit_percent >= 0 else '😢'}\n"
                f"نسبة الربح: {profit_percent}%\n"
                f"المبلغ: {format_number(profit)} ريال {'🟢' if profit_percent >= 0 else '🔴'}\n"
                f"رصيدك الجديد: {format_number(new_balance)} ريال 💰"
            )
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def luck_game(self, user_id, risk_level=50):
        from config import MIN_GAMBLE
        conn = get_db()
        c = conn.cursor()
        try:
            # الحصول على الرصيد
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            balance = c.fetchone()[0]
            
            if balance < MIN_GAMBLE:
                return False, f"الحد الأدنى للعب الحظ هو {format_number(MIN_GAMBLE)} ريال! 💸"
            
            # فرصة الخسارة بناء على مستوى المخاطرة
            if random.random() < (risk_level / 100):
                # خسارة كاملة
                c.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user_id,))
                conn.commit()
                return False, (
                    f"للأسف خسرت بالحظ! 😢\n"
                    f"فلوسك قبل اللعب: {format_number(balance)} ريال\n"
                    f"فلوسك الآن: 0 ريال"
                )
            else:
                # ربح
                multiplier = random.randint(2, 5)
                win_amount = balance * multiplier
                new_balance = balance + win_amount
                c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
                conn.commit()
                return True, (
                    f"مبروك ربحت بالحظ! 🎉\n"
                    f"مضاعف الربح: {multiplier}x\n"
                    f"المبلغ: {format_number(win_amount)} ريال\n"
                    f"رصيدك الجديد: {format_number(new_balance)} ريال 💰"
                )
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()