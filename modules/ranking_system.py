"""
نظام التصنيف والنقاط الذهبية
عندما يصل اللاعب للحد الأقصى من المال يحصل على نقاط ذهبية
"""

import logging
from datetime import datetime
from database.operations import execute_query
from aiogram.types import Message

# الحد الأقصى للأموال قبل التحويل لنقاط ذهبية
MAX_MONEY_LIMIT = 9223372036854775800
GOLD_POINTS_PER_RESET = 50

async def init_ranking_system():
    """تهيئة جداول نظام التصنيف"""
    try:
        await execute_query("""
            ALTER TABLE users 
            ADD COLUMN gold_points INTEGER DEFAULT 0
        """)
        logging.info("✅ تم إضافة عمود النقاط الذهبية")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            pass  # العمود موجود بالفعل
        else:
            logging.info("ℹ️ عمود النقاط الذهبية موجود بالفعل أو تم إنشاؤه")

async def check_money_limit_and_convert(user_id: int) -> bool:
    """
    فحص إذا وصل المستخدم للحد الأقصى من المال
    إذا وصل، يتم تحويل المال إلى نقاط ذهبية
    """
    try:
        # الحصول على رصيد المستخدم
        user_data = await execute_query(
            "SELECT balance, bank_balance, gold_points FROM users WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if not user_data:
            return False
            
        total_money = user_data.get('balance', 0) + user_data.get('bank_balance', 0)
        current_gold_points = user_data.get('gold_points', 0)
        
        if total_money >= MAX_MONEY_LIMIT:
            # تصفير الأموال وإضافة النقاط الذهبية
            new_gold_points = current_gold_points + GOLD_POINTS_PER_RESET
            
            await execute_query(
                """
                UPDATE users 
                SET balance = 1000, bank_balance = 0, gold_points = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (new_gold_points, datetime.now().isoformat(), user_id)
            )
            
            logging.info(f"🏆 المستخدم {user_id} وصل للحد الأقصى! تم تحويل أمواله إلى {GOLD_POINTS_PER_RESET} نقطة ذهبية")
            return True
            
    except Exception as e:
        logging.error(f"خطأ في فحص حد المال للمستخدم {user_id}: {e}")
        return False
    
    return False

async def get_ranking_list(limit: int = 10) -> list:
    """الحصول على قائمة التصنيف حسب النقاط الذهبية"""
    try:
        result = await execute_query(
            """
            SELECT user_id, first_name, username, gold_points, balance, bank_balance
            FROM users 
            WHERE gold_points > 0
            ORDER BY gold_points DESC, (balance + bank_balance) DESC
            LIMIT ?
            """,
            (limit,),
            fetch_all=True
        )
        
        return result if result else []
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على قائمة التصنيف: {e}")
        return []

async def show_ranking_list(message: Message):
    """عرض قائمة التصنيف"""
    try:
        ranking_data = await get_ranking_list(20)
        
        if not ranking_data:
            await message.reply(
                "🏆 **قائمة التصنيف**\n\n"
                "❌ لا توجد نقاط ذهبية لأي لاعب بعد!\n\n"
                f"💡 **كيف تحصل على نقاط ذهبية؟**\n"
                f"اجمع {MAX_MONEY_LIMIT:,} كوين لتحصل على {GOLD_POINTS_PER_RESET} نقطة ذهبية!"
            )
            return
            
        ranking_text = "🏆 **التصنيف الذهبي**\n\n"
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, player in enumerate(ranking_data):
            rank_icon = medals[i] if i < len(medals) else f"{i+1}️⃣"
            name = player.get('first_name', 'غير معروف')
            gold_points = player.get('gold_points', 0)
            
            ranking_text += f"{rank_icon} **{name}** - {gold_points:,} نقطة\n"
        
        await message.reply(ranking_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة التصنيف: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض قائمة التصنيف")

async def get_user_rank_info(user_id: int) -> dict:
    """الحصول على معلومات ترتيب المستخدم"""
    try:
        # الحصول على بيانات المستخدم
        user_data = await execute_query(
            "SELECT first_name, gold_points, balance, bank_balance FROM users WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if not user_data:
            return {"error": "المستخدم غير موجود"}
        
        gold_points = user_data.get('gold_points', 0)
        
        if gold_points == 0:
            return {
                "name": user_data.get('first_name', 'غير معروف'),
                "gold_points": 0,
                "rank": "غير مصنف",
                "total_money": user_data.get('balance', 0) + user_data.get('bank_balance', 0)
            }
        
        # الحصول على ترتيب المستخدم
        rank_result = await execute_query(
            """
            SELECT COUNT(*) + 1 as user_rank
            FROM users 
            WHERE gold_points > ? OR (gold_points = ? AND (balance + bank_balance) > ?)
            """,
            (gold_points, gold_points, user_data.get('balance', 0) + user_data.get('bank_balance', 0)),
            fetch_one=True
        )
        
        user_rank = rank_result.get('user_rank', 0) if rank_result else 0
        
        return {
            "name": user_data.get('first_name', 'غير معروف'),
            "gold_points": gold_points,
            "rank": user_rank,
            "total_money": user_data.get('balance', 0) + user_data.get('bank_balance', 0)
        }
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على ترتيب المستخدم {user_id}: {e}")
        return {"error": f"خطأ: {e}"}

async def notify_gold_points_earned(message: Message, user_id: int):
    """إشعار المستخدم بحصوله على نقاط ذهبية"""
    try:
        user_info = await get_user_rank_info(user_id)
        
        notification = (
            f"🎉 **تهانينا {message.from_user.first_name}!**\n\n"
            f"🏆 **لقد وصلت للحد الأقصى من الأموال!**\n"
            f"💰 تم تحويل أموالك إلى **{GOLD_POINTS_PER_RESET} نقطة ذهبية**\n\n"
            f"📊 **إحصائياتك الجديدة:**\n"
            f"🥇 النقاط الذهبية: {user_info.get('gold_points', 0):,}\n"
            f"🏅 ترتيبك: {user_info.get('rank', 'غير معروف')}\n"
            f"🪙 رصيدك الحالي: {user_info.get('total_money', 0):,}\n\n"
            f"💡 **اكتب 'قائمة التصنيف' لرؤية ترتيبك مع الآخرين!**"
        )
        
        await message.reply(notification)
        
    except Exception as e:
        logging.error(f"خطأ في إرسال إشعار النقاط الذهبية للمستخدم {user_id}: {e}")