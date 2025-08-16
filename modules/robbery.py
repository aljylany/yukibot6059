import sqlite3
import time
import random
from database import get_db, format_number
from config import ROBBERY_COOLDOWN
from modules.banking import BankingSystem

banking = BankingSystem()

class RobberySystem:
    def __init__(self, bot):
        self.bot = bot

    def attempt_robbery(self, robber_id, victim_id, bot_id, chat_id):
        conn = get_db()
        c = conn.cursor()
        try:
            # منع المستخدم من سرقة نفسه
            if robber_id == victim_id:
                return False, "❌ لا يمكنك سرقة نفسك!"
            
            # منع المستخدم من سرقة البوت
            if victim_id == bot_id:
                return False, "❌ لا يمكنك سرقة البوت!"
            
            # تحقق من رصيد الضحية
            c.execute("SELECT balance FROM users WHERE user_id = ?", (victim_id,))
            victim_result = c.fetchone()
            
            if not victim_result:
                return False, "الضحية ليس لديها حساب في البوت!"
                
            victim_balance = victim_result[0]
            
            if victim_balance < 1000:
                return False, "الضحية فقير جداً! 🥹"
            
            # نسبة النجاح 40%
            if random.random() < 0.4:
                # سرقة نسبة عشوائية بين 1% و 10% من رصيد الضحية
                steal_percent = random.uniform(0.01, 0.10)
                stolen_amount = int(victim_balance * steal_percent)
                
                # الحد الأدنى للسرقة 1000 ريال
                stolen_amount = max(stolen_amount, 1000)
                
                # لا تسمح بسرقة أكثر من رصيد الضحية
                stolen_amount = min(stolen_amount, victim_balance)
                
                # خصم من الضحية وإضافة للسارق
                c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (stolen_amount, victim_id))
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (stolen_amount, robber_id))
                c.execute("UPDATE users SET last_robbery = ? WHERE user_id = ?", (time.time(), robber_id))
                conn.commit()
                
                return True, f"سرقة ناجحة! 🎉 سرقت {format_number(stolen_amount)} ريال ({steal_percent*100:.1f}% من رصيد الضحية) 💰"
            else:
                # احتساب غرامة 10% من رصيد السارق
                c.execute("SELECT balance FROM users WHERE user_id = ?", (robber_id,))
                robber_balance = c.fetchone()[0]
                fine = int(robber_balance * 0.1)
                
                # الحد الأدنى للغرامة 1000 ريال
                fine = max(fine, 1000)
                
                # لا تسمح بغرامة أكثر من رصيد السارق
                fine = min(fine, robber_balance)
                
                # الحصول على مالك المجموعة
                group_owner = self.get_group_owner(chat_id)
                
                # إذا لم يوجد مالك، تحويل الغرامة إلى البوت
                recipient_id = group_owner if group_owner else bot_id
                
                # خصم الغرامة من السارق
                c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (fine, robber_id))
                
                # إضافة الغرامة للمالك
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (fine, recipient_id))
                
                c.execute("UPDATE users SET last_robbery = ? WHERE user_id = ?", (time.time(), robber_id))
                conn.commit()
                
                recipient_name = "مالك المجموعة" if group_owner else "البوت"
                return False, f"فشلت السرقة! 🚨 الشرطة قبضت عليك ودفعت غرامة {format_number(fine)} ريال (ذهبت لـ{recipient_name})"
                
        except Exception as e:
            import traceback
            print(f"Robbery error: {traceback.format_exc()}")
            return False, f"حدث خطأ أثناء محاولة السرقة: {str(e)}"
        finally:
            conn.close()
    
    def get_group_owner(self, chat_id):
        """الحصول على مالك المجموعة (أول أدمن في القائمة)"""
        try:
            # الحصول على قائمة المشرفين
            admins = self.bot.get_chat_administrators(chat_id)
            
            # البحث عن المالك (الذي لديه صلاحية owner)
            for admin in admins:
                if admin.status == "creator":
                    return admin.user.id
            
            return None
        except Exception as e:
            print(f"Error getting group owner: {str(e)}")
            return None