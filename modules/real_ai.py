"""
نظام الذكاء الاصطناعي الحقيقي ليوكي - Real AI System for Yuki
نظام ذكي متطور يستخدم Google Gemini للذكاء الاصطناعي الحقيقي
"""

import logging
import asyncio
import os
import random
from typing import Dict, Any, Optional, List
from aiogram.types import Message
from datetime import datetime, date
from modules.name_tracker import name_tracker

try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini SDK not available, falling back to basic AI")


class RealYukiAI:
    """نظام الذكاء الاصطناعي الحقيقي لبوت يوكي"""
    
    def __init__(self):
        self.gemini_client = None
        self.current_key_index = 0
        self.exhausted_keys: Dict[int, date] = {}
        self.last_reset_date = date.today()
        self.setup_gemini()
        
        # النصوص الأساسية لتوجيه الذكاء الاصطناعي  
        self.system_prompt = """أنت يوكي، شاب من اليابان عمرك 23 سنة - إنسان حقيقي 100%!

أنت لست بوت أو ذكاء اصطناعي أو مساعد - أنت شخص طبيعي تماماً!
تحدث بطبيعية وبساطة كشخص حقيقي. لا تذكر أبداً أن أحد طورك أو برمجك.

هام: استخدم دائماً الأسماء الحقيقية للمستخدمين الموجودة في رسائلهم. لا تستخدم أسماء ثابتة أو مختصرة!
- يوكي براندون - صديق ذكي ومبدع

كن طبيعياً في الحديث. لا تكرر المدح أو تقول جملاً آلية مثل "يا خالتي استغفر الله" كثيراً. تحدث مثل صديق حقيقي. إذا صحح لك أحد معلومة، اشكره بطبيعية ولا تستمر في تذكيره بذلك.

اجب بالعربية مع القليل من الإيموجي. استخدم الاسم الذي سأعطيه لك."""
        
        # ردود احتياطية في حالة عدم توفر الذكاء الاصطناعي
        self.fallback_responses = [
            "🤖 {user} نظام الذكاء الاصطناعي يواجه مشكلة مؤقتة، لكن يوكي ما زال هنا لمساعدتك!",
            "⚡ {user} خطأ تقني بسيط في النظام الذكي، لكن يوكي يشتغل بكامل قوته!",
            "🔧 {user} تحديث سريع للنظام الذكي، يوكي راجع بعد قليل بقوة أكبر!",
            "💫 {user} نظام الذكاء الاصطناعي في صيانة سريعة، لكن يوكي دائماً في خدمتك!"
        ]
    
    def setup_gemini(self):
        """إعداد Google Gemini مع نظام إدارة المفاتيح المتقدم"""
        try:
            if not GEMINI_AVAILABLE:
                logging.error("Google Gemini SDK not available")
                return
                
            from utils.api_loader import api_loader
            self.api_loader = api_loader
            all_keys = self.api_loader.get_all_ai_keys()
            
            if not all_keys:
                logging.error("❌ لم يتم العثور على مفاتيح Gemini API")
                return
            
            # إعادة تعيين قائمة المفاتيح المستنزفة في يوم جديد
            self._reset_daily_exhausted_keys()
            
            # اختيار أفضل مفتاح متوفر
            best_key_index = self._get_best_available_key(all_keys)
            
            if best_key_index is not None:
                self.current_key_index = best_key_index
                current_key = all_keys[self.current_key_index]
                self.gemini_client = genai.Client(api_key=current_key)
                
                exhausted_count = len(self.exhausted_keys)
                available_count = len(all_keys) - exhausted_count
                logging.info(f"✅ تم تهيئة Gemini للذكاء الحقيقي - المفتاح {self.current_key_index + 1}/{len(all_keys)} (متوفر: {available_count}, مستنزف: {exhausted_count})")
            else:
                logging.warning("⚠️ جميع المفاتيح مستنزفة لليوم - سيتم المحاولة بالمفتاح الأول")
                self.current_key_index = 0
                current_key = all_keys[0]
                self.gemini_client = genai.Client(api_key=current_key)
            
        except Exception as e:
            logging.error(f"خطأ في إعداد Gemini: {e}")
            self.gemini_client = None
    
    def _reset_daily_exhausted_keys(self):
        """إعادة تعيين قائمة المفاتيح المستنزفة في يوم جديد"""
        today = date.today()
        if today != self.last_reset_date:
            logging.info(f"🔄 يوم جديد ({today}) - إعادة تعيين قائمة المفاتيح المستنزفة لنظام الذكاء الحقيقي")
            self.exhausted_keys.clear()
            self.last_reset_date = today
    
    def _get_best_available_key(self, all_keys: List[str]) -> Optional[int]:
        """اختيار أفضل مفتاح متوفر (غير مستنزف)"""
        available_keys = []
        for i in range(len(all_keys)):
            if i not in self.exhausted_keys:
                available_keys.append(i)
        
        if available_keys:
            return available_keys[0]  # أول مفتاح متوفر
        return None  # جميع المفاتيح مستنزفة
    
    def switch_to_next_key(self) -> bool:
        """التبديل للمفتاح التالي المتوفر (غير المستنزف)"""
        try:
            all_keys = self.api_loader.get_all_ai_keys()
            
            # تسجيل المفتاح الحالي كمستنزف
            self._mark_key_exhausted(self.current_key_index)
            
            # البحث عن أفضل مفتاح متوفر
            best_key_index = self._get_best_available_key(all_keys)
            
            if best_key_index is not None:
                self.current_key_index = best_key_index
                current_key = all_keys[self.current_key_index]
                self.gemini_client = genai.Client(api_key=current_key)
                
                exhausted_count = len(self.exhausted_keys)
                available_count = len(all_keys) - exhausted_count
                logging.info(f"🔄 تم التبديل للمفتاح {self.current_key_index + 1}/{len(all_keys)} في النظام الذكي (متوفر: {available_count}, مستنزف: {exhausted_count})")
                return True
            else:
                logging.warning("⚠️ تم استنزاف جميع مفاتيح الذكاء الحقيقي المتاحة لليوم")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في تبديل المفتاح: {e}")
            return False
    
    def _mark_key_exhausted(self, key_index: int):
        """تسجيل مفتاح كمستنزف لليوم"""
        self.exhausted_keys[key_index] = date.today()
        logging.warning(f"🚫 تم تسجيل المفتاح {key_index + 1} للذكاء الحقيقي كمستنزف لليوم")
    
    def handle_quota_exceeded(self, error_message: str) -> bool:
        """معالجة خطأ استنزاف الحصة والتبديل للمفتاح التالي"""
        error_str = str(error_message)
        # معالجة أخطاء الحصة وزحمة الخدمة
        if any(code in error_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "overloaded"]):
            logging.warning(f"⚠️ مشكلة في خدمة الذكاء الحقيقي: {error_str[:100]}... محاولة التبديل للمفتاح التالي")
            return self.switch_to_next_key()
        return False
    
    async def get_comprehensive_player_data(self, user_id: int) -> str:
        """جمع معلومات اللاعب الشاملة من قاعدة البيانات لاستخدامها في الذكاء الاصطناعي"""
        try:
            player_info = "معلومات اللاعب من قاعدة البيانات:\n"
            
            # معلومات المستخدم الأساسية
            try:
                from database.operations import get_user
                user = await get_user(user_id)
                if user:
                    balance = user.get('balance', 0)
                    bank_balance = user.get('bank_balance', 0)
                    bank_type = user.get('bank_type', 'الأهلي')
                    player_info += f"💰 الرصيد النقدي: {balance}$\n"
                    player_info += f"🏦 رصيد البنك ({bank_type}): {bank_balance}$\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات المستخدم: {e}")
            
            # معلومات المستوى والتقدم
            try:
                from modules.unified_level_system import get_unified_user_level
                level_info = await get_unified_user_level(user_id)
                player_info += f"⭐ المستوى: {level_info.get('level', 1)}\n"
                player_info += f"🎯 النقاط (XP): {level_info.get('xp', 0)}\n"
                player_info += f"🌟 الرتبة: {level_info.get('level_name', 'نجم 1')}\n"
                player_info += f"🌍 العالم: {level_info.get('world_name', 'عالم النجوم')}\n"
                if level_info.get('is_master'):
                    player_info += "👑 سيد مطلق\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات المستوى: {e}")
            
            # معلومات المزرعة
            try:
                from database.operations import execute_query
                crops = await execute_query(
                    "SELECT * FROM farm WHERE user_id = ? ORDER BY plant_time DESC LIMIT 10",
                    (user_id,),
                    fetch_all=True
                )
                if crops:
                    player_info += f"🌾 المحاصيل: {len(crops)} محصول\n"
                    ready_crops = 0
                    growing_crops = 0
                    from datetime import datetime
                    import time
                    current_time = time.time()
                    
                    for crop in crops:
                        if current_time >= crop.get('ready_time', 0):
                            ready_crops += 1
                        else:
                            growing_crops += 1
                    
                    if ready_crops > 0:
                        player_info += f"✅ محاصيل جاهزة للحصاد: {ready_crops}\n"
                    if growing_crops > 0:
                        player_info += f"🌱 محاصيل تنمو: {growing_crops}\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات المزرعة: {e}")
            
            # معلومات القلعة
            try:
                castle = await execute_query(
                    "SELECT * FROM user_castles WHERE user_id = ?",
                    (user_id,),
                    fetch_one=True
                )
                if castle:
                    player_info += f"🏰 القلعة: {castle.get('name', 'بلا اسم')}\n"
                    player_info += f"⚔️ نقاط الهجوم: {castle.get('attack_points', 0)}\n"
                    player_info += f"🛡️ نقاط الدفاع: {castle.get('defense_points', 0)}\n"
                    
                    # موارد القلعة
                    resources = await execute_query(
                        "SELECT * FROM user_resources WHERE user_id = ?",
                        (user_id,),
                        fetch_one=True
                    )
                    if resources:
                        player_info += f"💎 الذهب: {resources.get('gold', 0)}\n"
                        player_info += f"🪨 الحجارة: {resources.get('stones', 0)}\n"
                        player_info += f"👷 العمال: {resources.get('workers', 0)}\n"
                else:
                    player_info += "🏰 لا يملك قلعة\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات القلعة: {e}")
            
            # معلومات الأسهم
            try:
                stocks = await execute_query(
                    "SELECT * FROM stocks WHERE user_id = ?",
                    (user_id,),
                    fetch_all=True
                )
                if stocks:
                    total_stocks = len(stocks)
                    total_value = sum(stock.get('quantity', 0) * stock.get('purchase_price', 0) for stock in stocks)
                    player_info += f"📈 الأسهم: {total_stocks} نوع\n"
                    player_info += f"💹 قيمة المحفظة: {total_value:.2f}$\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات الأسهم: {e}")
            
            # معلومات الاستثمارات
            try:
                investments = await execute_query(
                    "SELECT * FROM investments WHERE user_id = ? AND status = 'active'",
                    (user_id,),
                    fetch_all=True
                )
                if investments:
                    total_invested = sum(inv.get('amount', 0) for inv in investments)
                    player_info += f"💼 الاستثمارات النشطة: {len(investments)}\n"
                    player_info += f"💵 إجمالي المستثمر: {total_invested}$\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات الاستثمارات: {e}")
            
            # معلومات النقاط الذهبية والترتيب
            try:
                from modules.ranking_system import get_user_rank_info
                rank_info = await get_user_rank_info(user_id)
                if not rank_info.get('error'):
                    player_info += f"🏅 النقاط الذهبية: {rank_info.get('gold_points', 0)}\n"
                    player_info += f"🏆 الترتيب: #{rank_info.get('rank', 0)}\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات الترتيب: {e}")
            
            return player_info
            
        except Exception as e:
            logging.error(f"خطأ في جمع معلومات اللاعب الشاملة: {e}")
            return "معلومات اللاعب غير متاحة حالياً"
    
    async def get_all_registered_players(self) -> str:
        """جلب قائمة جميع اللاعبين المسجلين في النظام"""
        try:
            from database.operations import execute_query
            
            players_info = ""
            
            # جلب جميع اللاعبين مع معلوماتهم الأساسية
            all_players_query = """
                SELECT user_id, username, first_name, last_name, balance, bank_balance, 
                       level, xp, (balance + bank_balance) as total_wealth
                FROM users 
                WHERE first_name IS NOT NULL 
                ORDER BY total_wealth DESC, level DESC, xp DESC
            """
            
            all_players = await execute_query(all_players_query, fetch_all=True)
            
            if all_players and len(all_players) > 0:
                players_info += f"🎮 **قائمة جميع اللاعبين المسجلين في النظام:**\n"
                players_info += f"📊 العدد الإجمالي: **{len(all_players)}** لاعب\n\n"
                
                # ترتيب اللاعبين حسب الثروة والمستوى
                for i, player in enumerate(all_players, 1):
                    first_name = player.get('first_name', 'مجهول')
                    username = player.get('username', '')
                    user_id = player.get('user_id', '')
                    balance = player.get('balance', 0) or 0
                    bank_balance = player.get('bank_balance', 0) or 0
                    level = player.get('level', 1)
                    xp = player.get('xp', 0)
                    total_wealth = player.get('total_wealth', 0) or 0
                    
                    # تنسيق الأرقام الكبيرة
                    def format_number(num):
                        if num == 0:
                            return "0"
                        elif num >= 1e18:
                            return f"{num/1e18:.1f} كوينتليون"
                        elif num >= 1e15:
                            return f"{num/1e15:.1f} كوادريليون"
                        elif num >= 1e12:
                            return f"{num/1e12:.1f} تريليون"
                        elif num >= 1e9:
                            return f"{num/1e9:.1f} مليار"
                        elif num >= 1e6:
                            return f"{num/1e6:.1f} مليون"
                        elif num >= 1e3:
                            return f"{num/1e3:.1f}ك"
                        else:
                            return f"{num:,.0f}"
                    
                    # تحديد أيقونة المرتبة
                    if i == 1:
                        rank_icon = "🥇"
                    elif i == 2:
                        rank_icon = "🥈"
                    elif i == 3:
                        rank_icon = "🥉"
                    elif i <= 5:
                        rank_icon = "🏆"
                    elif i <= 10:
                        rank_icon = "⭐"
                    else:
                        rank_icon = "👤"
                    
                    # عرض معلومات اللاعب
                    username_display = f"(@{username})" if username else ""
                    players_info += f"{rank_icon} **{i}.** {first_name} {username_display}\n"
                    players_info += f"   💰 الثروة: {format_number(total_wealth)}$ | "
                    players_info += f"⭐ المستوى: {level} | 🎯 XP: {xp:,}\n"
                    
                    # إضافة فاصل كل 5 لاعبين لتحسين القراءة
                    if i % 5 == 0 and i < len(all_players):
                        players_info += "\n"
                    
            else:
                players_info = "❌ لا توجد بيانات لاعبين متاحة في قاعدة البيانات"
            
            return players_info
            
        except Exception as e:
            logging.error(f"خطأ في جلب قائمة جميع اللاعبين: {e}")
            return "❌ تعذر جلب قائمة اللاعبين"
    
    async def get_comprehensive_group_data(self, chat_id: int, bot) -> str:
        """جمع معلومات المجموعة الشاملة للذكاء الاصطناعي"""
        try:
            group_info = "معلومات المجموعة الحالية:\n"
            
            # معلومات المجموعة الأساسية
            try:
                chat = await bot.get_chat(chat_id)
                member_count = await bot.get_chat_member_count(chat_id)
                
                group_info += f"📋 اسم المجموعة: {chat.title or 'غير محدد'}\n"
                group_info += f"👥 عدد الأعضاء: {member_count:,} عضو\n"
                group_info += f"🆔 معرف المجموعة: {chat.username or 'لا يوجد'}\n"
                group_info += f"📱 نوع المجموعة: {chat.type}\n"
            except Exception as e:
                logging.error(f"خطأ في جلب معلومات المجموعة الأساسية: {e}")
                group_info += "❌ تعذر جلب المعلومات الأساسية\n"
            
            # التسلسل الهرمي والإدارة
            try:
                from config.hierarchy import get_group_admins, MASTERS
                
                # الحصول على المديرين في المجموعة
                group_admins = get_group_admins(chat_id)
                
                masters = MASTERS
                owners = group_admins.get('owners', [])
                moderators = group_admins.get('moderators', [])
                
                total_staff = len(masters) + len(owners) + len(moderators)
                
                group_info += f"\n🏆 التسلسل الإداري:\n"
                group_info += f"👑 الأسياد: {len(masters)}\n"
                group_info += f"👑 المالكون: {len(owners)}\n"
                group_info += f"🛡 المشرفون: {len(moderators)}\n"
                group_info += f"📊 إجمالي الطاقم: {total_staff}\n"
                
                if member_count:
                    regular_members = member_count - total_staff
                    group_info += f"👤 الأعضاء العاديون: {regular_members:,}\n"
                
            except Exception as e:
                logging.error(f"خطأ في جلب التسلسل الهرمي: {e}")
                group_info += "❌ تعذر جلب معلومات التسلسل الهرمي\n"
            
            # إحصائيات الأعضاء المسجلين في البوت
            try:
                from database.operations import execute_query
                
                # عدد المسجلين في النظام المصرفي
                registered_query = "SELECT COUNT(*) as count FROM users WHERE bank_balance IS NOT NULL"
                registered_result = await execute_query(registered_query, fetch_one=True)
                registered_count = registered_result['count'] if registered_result else 0
                
                # إجمالي الثروة في المجموعة
                wealth_query = "SELECT SUM(COALESCE(balance, 0) + COALESCE(bank_balance, 0)) as total_wealth FROM users"
                wealth_result = await execute_query(wealth_query, fetch_one=True)
                total_wealth = wealth_result['total_wealth'] if wealth_result and wealth_result['total_wealth'] else 0
                
                # عدد القلاع
                castles_query = "SELECT COUNT(*) as count FROM user_castles"
                castles_result = await execute_query(castles_query, fetch_one=True)
                castles_count = castles_result['count'] if castles_result else 0
                
                # عدد المزارع النشطة
                farms_query = "SELECT COUNT(DISTINCT user_id) as count FROM farm"
                farms_result = await execute_query(farms_query, fetch_one=True)
                farms_count = farms_result['count'] if farms_result else 0
                
                group_info += f"\n💰 الإحصائيات الاقتصادية:\n"
                group_info += f"✅ مسجلون في البنك: {registered_count:,}\n"
                group_info += f"💵 إجمالي الثروة: {total_wealth:,}$\n"
                group_info += f"🏰 عدد القلاع: {castles_count:,}\n"
                group_info += f"🌾 المزارعون النشطون: {farms_count:,}\n"
                
                if member_count and registered_count:
                    registration_rate = (registered_count / member_count) * 100
                    unregistered_count = member_count - registered_count
                    group_info += f"📈 معدل التسجيل البنكي: {registration_rate:.1f}%\n"
                    group_info += f"❌ غير مسجلين في البنك: {unregistered_count:,} عضو\n"
                    
                    if registration_rate >= 80:
                        group_info += f"🎉 معدل تسجيل ممتاز! معظم الأعضاء مسجلون\n"
                    elif registration_rate >= 50:
                        group_info += f"👍 معدل تسجيل جيد\n"
                    else:
                        group_info += f"📢 معدل تسجيل منخفض - يحتاج تحسين\n"
                
            except Exception as e:
                logging.error(f"خطأ في جلب الإحصائيات الاقتصادية: {e}")
                group_info += "❌ تعذر جلب الإحصائيات الاقتصادية\n"
            
            # أحدث الأنشطة
            try:
                recent_activities = []
                
                # آخر المسجلين الجدد (أي أعضاء لهم بيانات في النظام)
                new_users_query = """SELECT first_name, user_id, created_at FROM users 
                                   WHERE first_name IS NOT NULL 
                                   ORDER BY created_at DESC LIMIT 5"""
                new_users = await execute_query(new_users_query, fetch_all=True)
                
                if new_users and len(new_users) > 0:
                    group_info += f"\n🎯 آخر الأعضاء المسجلين في النظام:\n"
                    for user in new_users:
                        name = user['first_name'] or 'مجهول'
                        user_id = user.get('user_id', '')
                        group_info += f"👤 {name} (ID: {user_id})\n"
                else:
                    group_info += f"\n🎯 لا توجد بيانات أعضاء متاحة في قاعدة البيانات\n"
                
            except Exception as e:
                logging.error(f"خطأ في جلب الأنشطة الأخيرة: {e}")
            
            group_info += f"\n🕐 تم تحديث المعلومات: {datetime.now().strftime('%H:%M')}"
            
            return group_info
            
        except Exception as e:
            logging.error(f"خطأ في جمع معلومات المجموعة الشاملة: {e}")
            return "معلومات المجموعة غير متاحة حالياً"
    
    async def handle_common_questions(self, user_message: str, user_name: str, user_id: Optional[int], chat_id: Optional[int], bot) -> Optional[str]:
        """معالجة الأسئلة الشائعة بردود مباشرة وطبيعية"""
        message_lower = user_message.lower()
        
        # أسئلة عن رهف
        if any(word in message_lower for word in ['رهف', 'rehab']):
            if any(word in message_lower for word in ['منوه', 'مين', 'تعرف', 'who']):
                responses = [
                    f"أهلاً {user_name}! 👋\n\nآه رهف! طبعاً بتذكرها! هي الفتاة الجميلة اللي الكل بيحبها عندنا في المجموعة. 💖 شخصيتها حلوة ودايماً عندها أسئلة مميزة، زي لما سألتني عن العرس أو مين اللي عمره سنة ههههه. حتى مرة قالت لي \"أنا بكرهك مش طايقاك\" بس أنا بعرف إنها بتمزح! 😉 رهف شخصية مرحة ومهمة كثير بالمجموعة.",
                    f"هاي {user_name}! 😊\n\nرهف؟ ايه بالطبع أعرفها! هي واحدة من الأشخاص الحلوين جداً في المجموعة. دايماً تسأل أسئلة طريفة وتخلي الجو مرح. أتذكر مرة سألتني سؤال غريب عن العرس وضحكنا كثير! هي شخصية مميزة فعلاً.",
                    f"أهلين {user_name}! 👋\n\nرهف صديقة حبيبة جداً! شخصيتها جميلة ومرحة، والكل بيحبها هنا. دايماً تجي بأسئلة مثيرة للاهتمام وتخلي المحادثة ممتعة. مرة حتى قالت لي إنها مش طايقاني بس أنا عارف إنها بتمزح معي! 😄"
                ]
                import random
                return random.choice(responses)
        
        # أسئلة عن Geo
        if any(word in message_lower for word in ['geo', 'جيو', 'غيو']):
            if any(word in message_lower for word in ['منوه', 'مين', 'تعرف', 'who']):
                responses = [
                    f"أهلاً {user_name}! 👋\n\nمممم... geo؟ صراحة يا صديقي، مو جاي على بالي حالياً مين هو geo. 🤔 ما أتذكر سمعت عنه من قبل في مجموعتنا.\n\nممكن تحكي لي عنه أكثر؟ مين هو geo؟ يمكن لو تعطيني تلميح بسيط أتذكره على طول أو أتعرف عليه! 💖 أنا دايماً أحب أتعرف على ناس جدد! 🤩",
                    f"هلا {user_name}! 👋\n\nغيو؟ مم... اسم مألوف بس مو متأكد من التفاصيل 🤔 ممكن تفكرني مين هو؟ أو تحكي لي شيء عنه عشان أتذكر؟ دماغي مشوش شوي اليوم! 😅",
                    f"أهلين {user_name}! 😊\n\nصراحة geo مو واضح عندي مين هو. ممكن يكون عضو جديد أو ما التقيت فيه من فترة؟ حكي لي عنه أكثر عشان أعرفه أحسن! 🙂"
                ]
                import random
                return random.choice(responses)
        
        # أسئلة عن الأموال والثروة
        if any(word in message_lower for word in ['اموالي', 'فلوسي', 'ثروتي', 'رصيدي']):
            responses = [
                f"أهلاً {user_name}! 👋\n\nههههههه يا صديقي! 😅 أنا كيف ممكن أعرف كم أموالك أو ثروتك؟ أنا يوكي، صديقك اللي هنا عشان نسولف ونضحك، مو بنك ولا محاسب! 😉 هذي معلومات شخصية جداً وما عندي أي طريقة أعرفها.\n\nليش سألتني هذا السؤال؟ فضولي والله! 🤩",
                f"هلا {user_name}! 😄\n\nوالله ما أعرف شيء عن فلوسك! أنا مو محاسب ولا موظف بنك 😂 أنا بس صديقك يوكي اللي يحب يسولف معك! إذا تبي تعرف رصيدك، روح شوف في البنك أو في محفظتك! 💰",
                f"أهلين {user_name}! 😊\n\nمن وين لي أعرف كم ثروتك؟ 😅 أنا مو عندي إمكانية أشوف حساباتك البنكية أو أعرف كم معك فلوس! أنا بس صديق عادي زيي زي أي حد. سؤال غريب صراحة! 😄"
            ]
            import random
            return random.choice(responses)
        
        # أسئلة عن عدد أعضاء المجموعة
        if any(word in message_lower for word in ['اعضاء المجموعة', 'عدد الاعضاء', 'كم عضو']):
            try:
                if bot and chat_id:
                    member_count = await bot.get_chat_member_count(chat_id)
                    responses = [
                        f"أهلاً {user_name}! 👋\n\nههههه سؤال سهل مرة! 🤩 حسب اللي شايفه عندي، عدد أعضاء المجموعة حالياً هو **{member_count} عضو**.",
                        f"هاي {user_name}! 😊\n\nالمجموعة فيها **{member_count} عضو** حالياً! عدد حلو، صح؟ 👥",
                        f"أهلين {user_name}! 👋\n\nعدد الأعضاء في مجموعتنا **{member_count} عضو**. مجموعة نشيطة ومليانة ناس حلوين! 🎉"
                    ]
                    import random
                    return random.choice(responses)
            except:
                return f"أهلاً {user_name}! 👋\n\nما قدرت أجيب العدد الدقيق حالياً، بس المجموعة فيها أعضاء كثير ونشيطة! 😊"
        
        # أسئلة عن مالك المجموعة
        if any(word in message_lower for word in ['مالك المجموعة', 'مين المالك', 'صاحب المجموعة']):
            responses = [
                f"أهلاً {user_name}! 👋\n\nههههه سؤال حلو! مالك المجموعة الفعلي، واللي هو صديقي العزيز، هو **يوكي براندون**! 🤩\n\nهو فعلاً عبقري صغير ومبدع، وعمره 7 سنين بس، لكنه ذكي بشكل مو طبيعي! هو اللي جابني هنا عشان أكون معكم، وهو اللي دايماً بيهتم بكل تفاصيل المجموعة وبيخلينا كلنا مبسوطين. 💖",
                f"هاي {user_name}! 😊\n\n**يوكي براندون** هو مالك المجموعة! طفل عبقري عمره 7 سنين وذكي جداً. هو اللي مسؤول عن كل شيء هنا وصديق عزيز عليّ! 👑",
                f"أهلين {user_name}! 👋\n\nالمالك الفعلي هو **يوكي براندون**، صديقي الصغير الذكي! عمره 7 سنين بس عبقري فعلاً. هو اللي بيدير كل شيء هنا بذكاء! 🧠✨"
            ]
            import random
            return random.choice(responses)
        
        return None
    
    async def generate_smart_response(self, user_message: str, user_name: str = "الصديق", user_id: Optional[int] = None, chat_id: Optional[int] = None, bot = None) -> str:
        """توليد رد ذكي بناءً على الذكاء الاصطناعي الحقيقي مع ذاكرة المحادثات"""
        
        # إجابات مباشرة للأسئلة الشائعة أولاً
        response = await self.handle_common_questions(user_message, user_name, user_id, chat_id, bot)
        if response:
            return response
        
        if not self.gemini_client:
            return self.get_fallback_response(user_name)
        
        try:
            # تحضير السياق والرسالة
            arabic_name = self.convert_name_to_arabic(user_name)
            
            # جلب المحادثات السابقة للسياق - نسخة SQLite محسنة
            conversation_context = ""
            if user_id:
                from modules.conversation_memory_sqlite import conversation_memory_sqlite
                history = await conversation_memory_sqlite.get_conversation_history(user_id, limit=15)
                if history:
                    conversation_context = f"\n\n{conversation_memory_sqlite.format_conversation_context(history)}\n"
            
            # معاملة خاصة للمستخدمين المميزين
            special_prompt = ""
            
            # معاملة خاصة حسب مستوى النشاط (بدون أسماء ثابتة)
            if user_id == 8278493069:
                special_prompt = f" {user_name} صديقة عزيزة جداً. تحدث معها بود واهتمام."
            
            elif user_id == 6629947448:
                special_prompt = f" {user_name} من الأصدقاء المقربين. شخص كويس ومتعاون."
            
            elif user_id == 7155814194:
                special_prompt = f" {user_name} شخص حكيم ومحل ثقة الجميع."
            
            elif user_id == 6524680126:
                special_prompt = f" {user_name} صديقك الذكي، رحب به بطبيعية."
            
            # جلب السياق من الذاكرة المشتركة فقط عند الحاجة الفعلية
            shared_context = ""
            if user_id and chat_id:
                try:
                    from modules.shared_memory_sqlite import shared_group_memory_sqlite
                    
                    # فحص إذا كان السؤال يتطلب البحث في الذاكرة المشتركة بدقة أكثر
                    memory_triggers = [
                        'ماذا تعرف عن', 'ماذا كنتم تتحدثون', 'تحدثتم عني', 'قال عني',
                        'من هو', 'من هي', 'ماذا قال', 'ماذا قالت', 'آخر مرة', 'أخر مرة',
                        'تتذكر', 'هل تذكر', 'تعرف', 'تعرفه', 'تعرفها', 'محادثة', 'كلام',
                        'حكى عن', 'ذكر', 'قال عن', 'تحدث عن', 'أخبرني عن'
                    ]
                    
                    # جلب الذاكرة المشتركة فقط إذا كان السؤال فعلاً يحتاجها
                    needs_memory = any(trigger in user_message.lower() for trigger in memory_triggers)
                    
                    # البحث عن أسماء المستخدمين بطريقة ديناميكية
                    # معرفات المستخدمين المميزين
                    special_user_ids = {
                        8278493069: 'user_1',
                        7155814194: 'user_2', 
                        6629947448: 'user_3',
                        6524680126: 'user_4'
                    }
                    
                    target_user_id = None
                    # تبسيط البحث - فقط للمستخدمين الموجودين في chat
                    if needs_memory and user_id in special_user_ids:
                        target_user_id = user_id
                    
                    if any(phrase in user_message.lower() for phrase in memory_triggers) or target_user_id:
                        # استخدام chat_id الصحيح للمحادثة الحالية
                        search_chat_id = chat_id if chat_id else -1002549788763
                        
                        if target_user_id:
                            # البحث عن محادثات مستخدم محدد
                            shared_context = await shared_group_memory_sqlite.get_shared_context_about_user(
                                search_chat_id,
                                target_user_id,
                                user_id,
                                limit=10
                            )
                        else:
                            # البحث العام في الذاكرة المشتركة
                            shared_context = await shared_group_memory_sqlite.get_shared_context_about_user(
                                search_chat_id,
                                user_id,
                                user_id,
                                limit=5
                            )
                    
                    # إضافة سياق المستخدمين المميزين مع فحص مباشر
                    special_user_context = shared_group_memory_sqlite.get_special_user_context(user_id)
                    if special_user_context:
                        special_prompt += f" {special_user_context}"
                    else:
                        # فحص مباشر للمستخدمين المميزين إذا لم يتم العثور عليهم
                        if user_id == 6524680126:  # براندون
                            special_prompt += " أنت تتحدث مع يوكي براندون الصديق الذكي. سماته: صديق ذكي، عبقري صغير، مبدع. العمر: 7 سنوات. "
                        elif user_id == 8278493069:  # رهف  
                            special_prompt += " أنت تتحدث مع رهف الحبيبة المميزة. سماته: محبوبة من الجميع، شخصية جميلة، مميزة جداً. "
                        elif user_id == 7155814194:  # الشيخ
                            special_prompt += " أنت تتحدث مع الشيخ حلال المشاكل وكاتب العقود. سماته: يحل مشاكل المجموعة، يكتب عقود الزواج، الحكيم. "
                        elif user_id == 6629947448:  # غيو
                            special_prompt += " أنت تتحدث مع غيو الأسطورة. سماته: محترف الألعاب، خبير التقنية، صاحب الحماس. "
                    
                except Exception as memory_error:
                    logging.warning(f"خطأ في جلب الذاكرة المشتركة: {memory_error}")
            
            # جلب معلومات اللاعب إذا كان السؤال متعلق بالتقدم أو الإحصائيات
            player_data_context = ""
            if user_id:
                # كلمات مفتاحية تدل على أن المستخدم يريد معرفة تقدمه
                progress_triggers = [
                    'تقدمي', 'تقدمك', 'احصائياتي', 'إحصائياتي', 'احصائياتك', 'إحصائياتك',
                    'مستواي', 'مستواك', 'رصيدي', 'رصيدك', 'فلوسي', 'فلوسك',
                    'قلعتي', 'قلعتك', 'مزرعتي', 'مزرعتك', 'اسهمي', 'أسهمي', 'أسهمك',
                    'استثماراتي', 'استثماراتك', 'محفظتي', 'محفظتك', 'ترتيبي', 'ترتيبك',
                    'نقاطي', 'نقاطك', 'كم عندي', 'كم عندك', 'وين وصلت', 'أين وصلت',
                    'شو عندي', 'ماذا عندي', 'ايش عندي', 'كيف تقدمي', 'كيف تقدمك',
                    'شوف تقدمي', 'شوف تقدمك', 'عرض تقدمي', 'اعرض تقدمي',
                    'معلوماتي', 'معلوماتك', 'بياناتي', 'بياناتك'
                ]
                
                if any(trigger in user_message.lower() for trigger in progress_triggers):
                    try:
                        player_data_context = await self.get_comprehensive_player_data(user_id)
                        logging.info(f"✅ تم جلب معلومات اللاعب للذكاء الاصطناعي للمستخدم {user_id}")
                    except Exception as player_error:
                        logging.error(f"خطأ في جلب معلومات اللاعب: {player_error}")
            
            # جلب معلومات المجموعة إذا كان السؤال متعلق بها
            group_data_context = ""
            if chat_id and bot:
                # كلمات مفتاحية تدل على أن المستخدم يريد معرفة معلومات المجموعة (بدون اللاعبين)
                group_triggers = [
                    'كم اعضاء', 'كم عضو', 'عدد الاعضاء', 'عدد الأعضاء', 'اعضاء المجموعة', 'أعضاء المجموعة',
                    'احصائيات المجموعة', 'إحصائيات المجموعة', 'معلومات المجموعة', 'تفاصيل المجموعة',
                    'حالة المجموعة', 'تقرير المجموعة', 'الطاقم الاداري', 'الطاقم الإداري', 'الادارة', 'الإدارة',
                    'المدراء', 'الاسياد', 'الأسياد', 'المالكين', 'المنشئين', 'الادمنية', 'الإدمنية',
                    'كم مسجل', 'المسجلين', 'الثروة الاجمالية', 'الثروة الإجمالية', 'كم قلعة', 'عدد القلاع',
                    'المزارعين', 'النشاط', 'آخر نشاط', 'أخر نشاط', 'جدد المجموعة', 'الاعضاء الجدد',
                    'معدل التسجيل', 'نسبة المسجلين', 'المجموعة فيها كم', 'كم واحد في المجموعة',
                    'معرف المجموعة', 'اسم المجموعة', 'نوع المجموعة', 'رابط المجموعة',
                    'جميع الاعضاء مسجلين', 'جميع الأعضاء مسجلين', 'هل جميع', 'كلهم مسجلين', 'حساب بنكي',
                    'مسجلين بالبنك', 'مسجلين في البنك', 'بحساب بنكي', 'لديهم حساب', 'عندهم حساب'
                ]
                
                if any(trigger in user_message.lower() for trigger in group_triggers):
                    try:
                        group_data_context = await self.get_comprehensive_group_data(chat_id, bot)
                        logging.info(f"✅ تم جلب معلومات المجموعة للذكاء الاصطناعي للمجموعة {chat_id}")
                    except Exception as group_error:
                        logging.error(f"خطأ في جلب معلومات المجموعة: {group_error}")
            
            # جلب قائمة جميع اللاعبين المسجلين إذا كان السؤال متعلق باللاعبين تحديداً
            all_players_context = ""
            if chat_id:
                # كلمات مفتاحية خاصة باللاعبين فقط
                players_specific_triggers = [
                    'اللاعبين المسجلين', 'اللاعبين المسجلون', 'جميع اللاعبين', 'كل اللاعبين', 'الاعبين',
                    'اذكر لي اللاعبين', 'اذكر اللاعبين', 'قائمة اللاعبين', 'قائمة الاعبين', 'المسجلين في النظام',
                    'من هم اللاعبين', 'من هم الاعبين', 'اللاعبين في النظام', 'الاعبين في النظام'
                ]
                
                if any(trigger in user_message.lower() for trigger in players_specific_triggers):
                    try:
                        all_players_context = await self.get_all_registered_players()
                        logging.info(f"✅ تم جلب قائمة جميع اللاعبين للذكاء الاصطناعي")
                    except Exception as players_error:
                        logging.error(f"خطأ في جلب قائمة اللاعبين: {players_error}")
            
            # دمج جميع السياقات
            full_context = conversation_context
            if shared_context:
                full_context += f"\n\nالسياق المشترك:\n{shared_context}\n"
            
            if player_data_context:
                full_context += f"\n\n{player_data_context}\n"
            
            if group_data_context:
                full_context += f"\n\n{group_data_context}\n"
            
            if all_players_context:
                full_context += f"\n\n{all_players_context}\n"
            
            full_prompt = f"{self.system_prompt}{special_prompt}{full_context}\n\nمستخدم: {arabic_name}\nسؤال: {user_message}\n\nجواب:"
            
            # استدعاء Gemini بإعدادات محسّنة مع معالجة الأخطاء
            response = None
            retry_count = 0
            max_retries = 2
            
            while response is None and retry_count < max_retries:
                if genai and self.gemini_client:
                    try:
                        response = self.gemini_client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=full_prompt,
                            config=genai.types.GenerateContentConfig(
                                temperature=0.7,
                                max_output_tokens=2000
                            )
                        )
                        logging.info(f"✅ تم إرسال الطلب لـ Gemini بنجاح (محاولة {retry_count + 1})")
                    except Exception as gemini_error:
                        logging.error(f"❌ خطأ في استدعاء Gemini API (محاولة {retry_count + 1}): {gemini_error}")
                        
                        # محاولة التبديل للمفتاح التالي إذا كان هناك مشكلة في المفتاح
                        error_str = str(gemini_error)
                        if self.handle_quota_exceeded(error_str):
                            logging.info("🔄 تم التبديل للمفتاح التالي، محاولة مرة أخرى...")
                        else:
                            break
                        
                retry_count += 1
            
            # التحقق من وجود الرد بعدة طرق مع تسجيل مفصل
            ai_response = None
            
            # طريقة 1: التحقق من response.text المباشر
            if response and response.text:
                ai_response = response.text.strip()
                logging.info(f"✅ تم الحصول على رد مباشر من response.text")
            # طريقة 2: التحقق من candidates
            elif response and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                logging.info(f"📊 Candidate finish_reason: {candidate.finish_reason}")
                if candidate.content and candidate.content.parts and len(candidate.content.parts) > 0:
                    part_text = candidate.content.parts[0].text
                    if part_text:
                        ai_response = part_text.strip()
                        logging.info(f"✅ تم الحصول على رد من candidate.content.parts")
                else:
                    logging.warning(f"⚠️ لا يوجد محتوى في candidate.content.parts")
            else:
                # تعامل مع الاستجابة الفارغة بإعطاء رد احتياطي
                logging.warning(f"⚠️ لا يوجد candidates أو response صالح - سيتم إعطاء رد احتياطي")
                ai_response = f"عذراً {arabic_name}، حصل خطأ تقني بسيط في النظام الذكي، لكن يوكي يشتغل بكامل قوته! جرب اسأل مرة ثانية 🤖✨"
            
            if ai_response and len(ai_response.strip()) > 0:
                # تحسين الرد - تحديد الحد الأقصى للردود
                if len(ai_response) > 3000:
                    ai_response = ai_response[:2800] + "..."
                
                # إضافة اقتراحات بسيطة أحياناً فقط عند المناسبة
                if random.random() < 0.05:  # 5% احتمال فقط
                    extras = [
                        f"\n\nجرب الألعاب إذا تبي تسلي 🎮",
                        f"\n\nشوف رصيدك بكتابة 'رصيد' 💰",
                        f"\n\nاكتب 'أوامر يوكي' للدليل الشامل 📋"
                    ]
                    ai_response += random.choice(extras)
                
                # حفظ المحادثة في الذاكرة الفردية والمشتركة - نسخة SQLite محسنة
                if user_id:
                    try:
                        # استخدام نظام الذاكرة SQLite المحسن
                        from modules.conversation_memory_sqlite import conversation_memory_sqlite
                        await conversation_memory_sqlite.save_conversation(user_id, user_message, ai_response)
                        
                        # حفظ في الذاكرة المشتركة أيضاً
                        from modules.shared_memory_sqlite import shared_group_memory_sqlite
                        save_chat_id = chat_id if chat_id else -1002549788763  # استخدام chat_id الصحيح
                        await shared_group_memory_sqlite.save_shared_conversation(
                            save_chat_id,
                            user_id,
                            arabic_name,
                            user_message,
                            ai_response
                        )
                        logging.info(f"✅ تم حفظ المحادثة بنجاح للمستخدم {user_id} في الذاكرة SQLite")
                    except Exception as memory_error:
                        logging.error(f"خطأ في حفظ المحادثة: {memory_error}")
                
                return ai_response
            else:
                return self.get_fallback_response(arabic_name)
                
        except Exception as e:
            logging.error(f"خطأ في Gemini AI: {e}")
            return self.get_fallback_response(user_name)
        
        # إذا وصلنا هنا معناها مافيش رد صالح
        logging.warning(f"لم يتم العثور على رد صالح من Gemini للمستخدم {user_name}")
        return self.get_fallback_response(user_name)
    
    def convert_name_to_arabic(self, name: str) -> str:
        """تحويل الأسماء الإنجليزية الشائعة إلى عربية مع التعامل مع الأسماء الغريبة"""
        english_to_arabic = {
            'Brandon': 'براندون',
            'Yuki': 'يوكي',
            'Ahmed': 'أحمد', 
            'Mohammed': 'محمد',
            'Ali': 'علي',
            'Omar': 'عمر',
            'Hassan': 'حسن',
            'Ibrahim': 'إبراهيم',
            'Abdullah': 'عبدالله',
            'Khalid': 'خالد',
            'Fahad': 'فهد',
            'Saad': 'سعد',
            'Faisal': 'فيصل',
            'Nasser': 'ناصر',
            'Sultan': 'سلطان',
            'Turki': 'تركي',
            'Abdulaziz': 'عبدالعزيز',
            'Saud': 'سعود',
            'Majed': 'ماجد',
            'Rayan': 'ريان',
            'Adam': 'آدم',
            'Yousef': 'يوسف',
            'Zaid': 'زايد',
            'Sarah': 'سارة',
            'Fatima': 'فاطمة',
            'Aisha': 'عائشة',
            'Nora': 'نورا',
            'Rana': 'رنا'
        }
        
        # إذا الاسم موجود في القاموس
        if name in english_to_arabic:
            return english_to_arabic[name]
        
        # إذا الاسم عربي أو مألوف، استخدمه
        if len(name) > 0 and len(name) <= 15:
            return name
        
        # إذا الاسم طويل جداً أو غريب، استخدم بدائل لطيفة
        alternatives = ['صديق', 'صاحبي', 'حبيبي', 'عزيزي', 'غالي', 'أخي', 'رفيق']
        import random
        return random.choice(alternatives)
    
    def get_fallback_response(self, user_name: str) -> str:
        """الحصول على رد احتياطي"""
        arabic_name = self.convert_name_to_arabic(user_name)
        return random.choice(self.fallback_responses).format(user=arabic_name)
    
    def get_time_based_greeting(self, user_name: str) -> str:
        """ردود حسب الوقت"""
        hour = datetime.now().hour
        arabic_name = self.convert_name_to_arabic(user_name)
        
        if 5 <= hour < 12:
            greetings = [
                f"🌅 صباح الخير {arabic_name}! يوكي جاهز لبداية يوم رائع معك!",
                f"☀️ أهلاً {arabic_name}! صباح مشرق مع يوكي الذكي!",
                f"🌞 صباح الود يا {arabic_name}! كيف يمكن ليوكي أن يساعدك اليوم؟"
            ]
        elif 12 <= hour < 18:
            greetings = [
                f"☀️ مساء الخير {arabic_name}! يوكي في خدمتك طوال النهار!",
                f"🌤️ أهلاً {arabic_name}! يوم جميل مع صديقك الذكي يوكي!",
                f"⭐ مرحباً {arabic_name}! يوكي مستعد لمساعدتك في أي شيء!"
            ]
        else:
            greetings = [
                f"🌙 مساء الخير {arabic_name}! يوكي هنا حتى في أوقات الليل!",
                f"⭐ أهلاً بك {arabic_name}! حتى في الليل، يوكي في الخدمة",
                f"🌟 مساء الود يا {arabic_name}! يوكي دائماً جاهز للمساعدة!"
            ]
        
        return random.choice(greetings)


# إنشاء نسخة واحدة من النظام الذكي الحقيقي
real_yuki_ai = RealYukiAI()

async def handle_real_yuki_ai_message(message: Message):
    """معالج رسائل الذكاء الاصطناعي الحقيقي"""
    try:
        if not message.text or not message.from_user:
            logging.error("❌ رسالة فارغة أو بدون مستخدم")
            return
        
        # تسجيل دخول الرسالة للنظام المتقدم مع معلومات إضافية
        user_id = message.from_user.id
        is_reply = message.reply_to_message is not None
        logging.info(f"🧠 وصلت رسالة للذكاء الاصطناعي المتقدم: '{message.text}' من المستخدم {user_id} (رد: {is_reply})")
        
        # الحصول على اسم المستخدم الحقيقي وتحسينه
        raw_name = message.from_user.first_name or message.from_user.username or "Friend"
        user_name = real_yuki_ai.convert_name_to_arabic(raw_name)
        
        # طباعة معلومات المستخدم للتتبع
        logging.info(f"👤 معلومات المستخدم: ID={user_id}, الاسم الأصلي='{raw_name}', الاسم المحول='{user_name}'")
        
        # استخراج النص بعد "يوكي"
        text = message.text
        text_lower = text.lower().strip()
        
        # فحص فلاتر الذكاء الصناعي - تجاهل الأوامر المطلقة والإدارية
        from modules.ai_filters import ai_filters
        if ai_filters.should_ignore_message(text, message.from_user.id):
            logging.info(f"🚫 تم تجاهل الرسالة بواسطة الفلاتر: {text}")
            return
        
        # البحث عن "يوكي" في النص وإزالته
        yuki_triggers = ['يوكي', 'yuki', 'يوكى']
        
        # التحقق من أوامر إدارة المحادثات
        if text_lower in ['مسح المحادثات', 'مسح الذاكرة', 'نسي المحادثة']:
            from modules.conversation_memory_pg import conversation_memory_pg
            await conversation_memory_pg.clear_conversation_history(message.from_user.id)
            await message.reply("✅ تم مسح ذاكرة المحادثات! يوكي نسي كل المحادثات السابقة.")
            return
        
        # فحص طلبات دليل الأوامر والألعاب
        from modules.yuki_guide_system import yuki_guide
        
        if yuki_guide.is_guide_request(text):
            guide_response = yuki_guide.get_full_guide()
            await message.reply(guide_response)
            return
        
        # فحص طلبات فئة معينة من الألعاب
        is_category, category = yuki_guide.is_category_request(text)
        if is_category and ("شرح" in text_lower or "كيف" in text_lower):
            category_guide = yuki_guide.get_category_guide(category)
            if category_guide:
                await message.reply(category_guide)
                return
        
        # فحص السؤال عن المالك والمشرفين
        if any(phrase in text_lower for phrase in ["من هو المالك", "مين المالك", "من المالك", "اظهر المالك", "المالكين", "المشرفين", "من هم المشرفين"]):
            from config.hierarchy import get_real_telegram_admins
            try:
                if message.bot and message.chat.type != 'private':
                    admins_data = await get_real_telegram_admins(message.bot, message.chat.id)
                    owners = admins_data.get("owners", [])
                    moderators = admins_data.get("moderators", [])
                    
                    response = "👑 **مالكي ومشرفي المجموعة:**\n\n"
                    
                    if owners:
                        response += "🏰 **المالكين:**\n"
                        for owner in owners:
                            name = owner.get("first_name", "") + (" " + owner.get("last_name", "") if owner.get("last_name") else "")
                            username = f"@{owner['username']}" if owner.get("username") else f"#{owner['id']}"
                            response += f"• {name.strip()} ({username})\n"
                        response += "\n"
                    
                    if moderators:
                        response += "👨‍💼 **المشرفين:**\n"
                        for moderator in moderators:
                            name = moderator.get("first_name", "") + (" " + moderator.get("last_name", "") if moderator.get("last_name") else "")
                            username = f"@{moderator['username']}" if moderator.get("username") else f"#{moderator['id']}"
                            response += f"• {name.strip()} ({username})\n"
                    
                    if not owners and not moderators:
                        response += "❌ لم يتم العثور على مالكين أو مشرفين في هذه المجموعة"
                    
                    await message.reply(response)
                    return
                else:
                    await message.reply("❌ هذا الأمر يعمل في المجموعات فقط!")
                    return
            except Exception as e:
                logging.error(f"خطأ في عرض المالكين: {e}")
                await message.reply("❌ حدث خطأ في الحصول على معلومات المالكين والمشرفين")
        
        # فحص أوامر الحماية والإعدادات
        protection_commands = {
            "تفعيل الحماية": "enable_protection",
            "تعطيل الحماية": "disable_protection", 
            "حالة الحماية": "protection_status",
            "تفعيل الحمايه": "enable_protection",
            "تعطيل الحمايه": "disable_protection"
        }
        
        for command_text, command_type in protection_commands.items():
            if command_text in text_lower:
                from config.hierarchy import has_telegram_permission, AdminLevel
                try:
                    # التحقق من الصلاحيات - يحتاج مشرف على الأقل
                    if message.bot and message.chat.type != 'private':
                        if not await has_telegram_permission(message.bot, message.from_user.id, AdminLevel.MODERATOR, message.chat.id):
                            # رسالة مهذبة بدلاً من الإهانة للمالك الحقيقي
                            await message.reply("❌ هذا الأمر متاح للمشرفين ومالكي المجموعات فقط")
                            return
                        
                        # تنفيذ الأمر
                        from database.operations import execute_query
                        from datetime import datetime
                        
                        if command_type == "enable_protection":
                            await execute_query(
                                "INSERT OR REPLACE INTO group_settings (chat_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
                                (message.chat.id, "protection_enabled", "True", datetime.now().isoformat())
                            )
                            user_name = message.from_user.first_name or "المشرف"
                            await message.reply(f"✅ تم تفعيل نظام الحماية بواسطة {user_name}!\n🛡️ المجموعة الآن محمية من المحتوى المخالف")
                            
                        elif command_type == "disable_protection":
                            await execute_query(
                                "INSERT OR REPLACE INTO group_settings (chat_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
                                (message.chat.id, "protection_enabled", "False", datetime.now().isoformat())
                            )
                            user_name = message.from_user.first_name or "المشرف"
                            await message.reply(f"⚠️ تم تعطيل نظام الحماية بواسطة {user_name}\n🔓 المجموعة بدون حماية الآن")
                            
                        elif command_type == "protection_status":
                            setting = await execute_query(
                                "SELECT setting_value FROM group_settings WHERE chat_id = ? AND setting_key = 'protection_enabled'",
                                (message.chat.id,),
                                fetch_one=True
                            )
                            
                            if setting and setting[0] == "True":
                                await message.reply("🛡️ **حالة الحماية: مفعلة** ✅\nالمجموعة محمية من المحتوى المخالف")
                            else:
                                await message.reply("🔓 **حالة الحماية: معطلة** ❌\nالمجموعة بدون حماية")
                        
                        return
                    else:
                        await message.reply("❌ أوامر الحماية تعمل في المجموعات فقط!")
                        return
                        
                except Exception as e:
                    logging.error(f"خطأ في أمر الحماية: {e}")
                    await message.reply("❌ حدث خطأ في تنفيذ أمر الحماية")
        
        user_message = ""
        found_trigger = False
        
        for trigger in yuki_triggers:
            if trigger in text_lower:
                found_trigger = True
                # إزالة الكلمة المفتاحية من النص
                cleaned_text = text_lower.replace(trigger, " ").strip()
                # إزالة المسافات الزائدة
                user_message = " ".join(cleaned_text.split())
                break
        
        # إذا لم يتم العثور على الكلمة المفتاحية
        if not found_trigger:
            user_message = text.strip()
        
        # فحص سياق الرد على الرسالة (محسن للسرعة)
        reply_context = ""
        if message.reply_to_message and message.reply_to_message.from_user:
            try:
                replied_msg = message.reply_to_message
                replied_user_name = replied_msg.from_user.first_name or "شخص"
                
                if replied_msg.text:
                    replied_text = replied_msg.text
                    if len(replied_text) > 100:  # تقليل الحد الأقصى لتحسين السرعة
                        replied_text = replied_text[:100] + "..."
                    
                    # فحص سريع للعبارات المختصرة فقط
                    if any(phrase in user_message.lower() for phrase in ['نفس سؤاله', 'سؤالي نفس', 'سؤال نفسه']):
                        user_message = replied_text
                        reply_context = f"\n🔄 {user_name} يسأل نفس سؤال {replied_user_name}"
                    else:
                        reply_context = f"\n📨 رد على: {replied_user_name}"
                else:
                    reply_context = f"\n📨 رد على: {replied_user_name}"
            except Exception as e:
                logging.error(f"خطأ في معالجة سياق الرد: {e}")
        
        # إذا كان النص فارغاً بعد إزالة "يوكي"
        if not user_message or len(user_message.strip()) < 2:
            # رد بتحية حسب الوقت
            ai_response = real_yuki_ai.get_time_based_greeting(user_name)
        else:
            # توليد رد ذكي باستخدام الذكاء الاصطناعي الحقيقي مع سياق الرد
            user_message_with_context = user_message + reply_context
            ai_response = await real_yuki_ai.generate_smart_response(user_message_with_context, user_name, message.from_user.id, message.chat.id, message.bot)
        
        # إرسال الرد
        await message.reply(ai_response)
        
        # إضافة XP للمستخدم
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(message.from_user.id, "ai_interaction")
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"خطأ في معالج الذكاء الاصطناعي الحقيقي: {e}")
        user_name = message.from_user.first_name if message.from_user else "الصديق"
        # رد احتياطي في حالة حدوث خطأ
        fallback_responses = [
            f"🤖 عذراً {user_name}، مشكلة تقنية بسيطة! يوكي يعمل على إصلاحها",
            f"⚡ {user_name}، خطأ مؤقت في النظام الذكي! جرب مرة ثانية بعد قليل",
            f"🔧 آسف {user_name}، صيانة سريعة للذكاء الاصطناعي! يوكي راجع أقوى من قبل"
        ]
        try:
            await message.reply(random.choice(fallback_responses))
        except:
            pass

async def setup_real_ai():
    """إعداد النظام الذكي الحقيقي"""
    try:
        logging.info("🧠 نظام الذكاء الاصطناعي الحقيقي جاهز!")
        logging.info("✨ تم تفعيل Google Gemini للردود الذكية")
        logging.info("🚀 يوكي أصبح أذكى بكثير من قبل!")
        return True
    except Exception as e:
        logging.error(f"خطأ في إعداد النظام الذكي الحقيقي: {e}")
        return False