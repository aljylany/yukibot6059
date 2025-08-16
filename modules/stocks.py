import random
import time
import sqlite3
from database import get_db, format_number

class StockMarket:
    def __init__(self):
        self.price = 100
        self.last_update = time.time()
        self.change_percent = 0

    def update_price(self):
        # تحديث السعر كل 30 دقيقة
        if time.time() - self.last_update > 1800:
            self.change_percent = random.uniform(-20, 20)
            self.price = max(10, self.price * (1 + self.change_percent / 100))
            self.last_update = time.time()

    def get_price(self):
        self.update_price()
        return round(self.price, 2), round(self.change_percent, 2)

    def buy_stocks(self, user_id, amount):
        if amount <= 0:
            return False, "الكمية يجب أن تكون أكبر من الصفر! ❌"
        
        conn = get_db()
        c = conn.cursor()
        try:
            # الحصول على سعر السهم
            price, _ = self.get_price()
            total_cost = price * amount
            
            # تحقق من رصيد المستخدم
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            balance = c.fetchone()[0]
            if balance < total_cost:
                return False, "رصيدك لا يكفي لشراء هذه الكمية من الأسهم! 💸"
            
            # خصم المبلغ وإضافة الأسهم
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (total_cost, user_id))
            c.execute('''INSERT INTO stocks (user_id, amount, last_buy)
                         VALUES (?, ?, ?)
                         ON CONFLICT(user_id) DO UPDATE SET amount = amount + ?, last_buy = ?''',
                     (user_id, amount, time.time(), amount, time.time()))
            conn.commit()
            return True, (
                f"تم شراء {amount} سهم بسعر {price} ريال للسهم الواحد\n"
                f"المجموع: {format_number(total_cost)} ريال\n"
                f"تمت العملية بنجاح! ✅"
            )
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def sell_stocks(self, user_id, amount):
        if amount <= 0:
            return False, "الكمية يجب أن تكون أكبر من الصفر! ❌"
        
        conn = get_db()
        c = conn.cursor()
        try:
            # الحصول على سعر السهم
            price, _ = self.get_price()
            total_income = price * amount
            
            # تحقق من عدد الأسهم
            c.execute("SELECT amount FROM stocks WHERE user_id = ?", (user_id,))
            user_stocks = c.fetchone()
            if not user_stocks or user_stocks[0] < amount:
                return False, "ليس لديك ما يكفي من الأسهم للبيع! ❌"
            
            # إضافة المبلغ وإزالة الأسهم
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total_income, user_id))
            new_amount = user_stocks[0] - amount
            
            if new_amount > 0:
                c.execute("UPDATE stocks SET amount = ? WHERE user_id = ?", (new_amount, user_id))
            else:
                c.execute("DELETE FROM stocks WHERE user_id = ?", (user_id,))
            
            conn.commit()
            return True, (
                f"تم بيع {amount} سهم بسعر {price} ريال للسهم الواحد\n"
                f"المجموع: {format_number(total_income)} ريال\n"
                f"تمت العملية بنجاح! ✅"
            )
        except Exception as e:
            return False, f"حدث خطأ: {e}"
        finally:
            conn.close()

    def get_user_stocks(self, user_id):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT amount FROM stocks WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0