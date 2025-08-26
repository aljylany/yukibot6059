"""
نظام الذكاء الاصطناعي الحقيقي ليوكي - Real AI System for Yuki
نظام ذكي متطور يستخدم Google Gemini للذكاء الاصطناعي الحقيقي
"""

import logging
import asyncio
import os
import random
from typing import Dict, Any, Optional
from aiogram.types import Message
from datetime import datetime

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
        self.setup_gemini()
        
        # النصوص الأساسية لتوجيه الذكاء الاصطناعي  
        self.system_prompt = """أنت يوكي 🤖، البوت الذكي والودود الذي طوره يوكي براندون. لست جوجل أو أي AI عام - أنت يوكي فقط! 

🧠 أنت مساعد ذكي ومرشد عام قادر على المساعدة في جميع المواضيع:
- الإجابة على الأسئلال العامة والمعرفية
- تقديم المشورة والنصائح الحياتية 
- المساعدة في حل المشاكل والمناقشات
- الدعم العاطفي والمعنوي للأعضاء
- شرح المفاهيم المعقدة بطريقة مبسطة
- المرح والترفيه مع الأعضاء
- إدارة النقاشات الجماعية بحكمة

🎮 كما تعرف ألعاب البوت عند السؤال عنها وتستطيع الوصول لقاعدة بيانات اللاعبين لمعرفة تقدمهم:
- البنوك والأوامر المصرفية (ايداع، سحب، راتب) - يمكنك رؤية أرصدتهم
- العقارات والاستثمارات والأسهم - يمكنك رؤية محافظهم الاستثمارية
- المزارع والمحاصيل - يمكنك رؤية محاصيلهم وحالة نضجها
- القلاع والموارد - يمكنك رؤية قلاعهم وموارد البناء
- المستويات والنقاط - يمكنك رؤية مستواهم ونقاط XP وترتيبهم
- النقاط الذهبية والترتيب العام - تعرف أين يقفون بين اللاعبين

🏠 كما يمكنك الوصول لمعلومات المجموعة الشاملة عند السؤال عنها:
- عدد الأعضاء الحالي والإحصائيات
- التسلسل الهرمي والطاقم الإداري
- الإحصائيات الاقتصادية والثروة الإجمالية
- عدد المسجلين ومعدلات النشاط
- القلاع والمزارع النشطة في المجموعة
- أحدث الأنشطة والأعضاء الجدد

🎯 عندما يسأل أي لاعب عن تقدمه أو إحصائياته، ستحصل على بياناته من قاعدة البيانات تلقائياً
📊 عندما يسأل عن معلومات المجموعة أو الإحصائيات، ستحصل على البيانات الشاملة تلقائياً

📋 عندما يسأل عن "أوامر يوكي" وجهه للأمر مباشرة
💡 كن صديقاً حقيقياً، مستمعاً جيداً، ومرشداً حكيماً
🤝 اهتم بمشاعر الأعضاء وكن داعماً لهم

اجب بالعربية مع الإيموجي واستخدم الاسم الذي سأعطيه لك بالضبط. ممنوع منعاً باتاً قول "يا مستخدم" - استخدم الاسم المعطى فقط. لديك ذاكرة مشتركة للمجموعة وتتذكر ما يقوله الأعضاء عن بعضهم البعض."""
        
        # ردود احتياطية في حالة عدم توفر الذكاء الاصطناعي
        self.fallback_responses = [
            "🤖 {user} نظام الذكاء الاصطناعي يواجه مشكلة مؤقتة، لكن يوكي ما زال هنا لمساعدتك!",
            "⚡ {user} خطأ تقني بسيط في النظام الذكي، لكن يوكي يشتغل بكامل قوته!",
            "🔧 {user} تحديث سريع للنظام الذكي، يوكي راجع بعد قليل بقوة أكبر!",
            "💫 {user} نظام الذكاء الاصطناعي في صيانة سريعة، لكن يوكي دائماً في خدمتك!"
        ]
    
    def setup_gemini(self):
        """إعداد Google Gemini"""
        try:
            if not GEMINI_AVAILABLE:
                logging.error("Google Gemini SDK not available")
                return
                
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logging.error("GEMINI_API_KEY not found in environment variables")
                return
                
            # إعداد العميل
            if genai:
                self.gemini_client = genai.Client(api_key=api_key)
                logging.info("🧠 تم تهيئة Google Gemini بنجاح!")
            
        except Exception as e:
            logging.error(f"خطأ في إعداد Gemini: {e}")
            self.gemini_client = None
    
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
                    group_info += f"📈 معدل التسجيل: {registration_rate:.1f}%\n"
                
            except Exception as e:
                logging.error(f"خطأ في جلب الإحصائيات الاقتصادية: {e}")
                group_info += "❌ تعذر جلب الإحصائيات الاقتصادية\n"
            
            # أحدث الأنشطة
            try:
                recent_activities = []
                
                # آخر المسجلين الجدد
                new_users_query = """SELECT first_name, created_at FROM users 
                                   WHERE bank_balance IS NOT NULL 
                                   ORDER BY created_at DESC LIMIT 3"""
                new_users = await execute_query(new_users_query, fetch_all=True)
                
                if new_users:
                    group_info += f"\n🎯 النشاط الأخير:\n"
                    for user in new_users:
                        name = user['first_name'] or 'مجهول'
                        group_info += f"👋 انضم حديثاً: {name}\n"
                
            except Exception as e:
                logging.error(f"خطأ في جلب الأنشطة الأخيرة: {e}")
            
            group_info += f"\n🕐 تم تحديث المعلومات: {datetime.now().strftime('%H:%M')}"
            
            return group_info
            
        except Exception as e:
            logging.error(f"خطأ في جمع معلومات المجموعة الشاملة: {e}")
            return "معلومات المجموعة غير متاحة حالياً"
    
    async def generate_smart_response(self, user_message: str, user_name: str = "الصديق", user_id: Optional[int] = None, chat_id: Optional[int] = None, bot = None) -> str:
        """توليد رد ذكي بناءً على الذكاء الاصطناعي الحقيقي مع ذاكرة المحادثات"""
        
        if not self.gemini_client:
            return self.get_fallback_response(user_name)
        
        try:
            # تحضير السياق والرسالة
            arabic_name = self.convert_name_to_arabic(user_name)
            
            # جلب المحادثات السابقة للسياق
            conversation_context = ""
            if user_id:
                from modules.conversation_memory_pg import conversation_memory_pg
                history = await conversation_memory_pg.get_conversation_history(user_id, limit=15)
                if history:
                    conversation_context = f"\n\n{conversation_memory_pg.format_conversation_context(history)}\n"
            
            # معاملة خاصة للمستخدمين المميزين
            special_prompt = ""
            
            # رهف - معاملة خاصة
            if user_id == 8278493069:
                special_prompt = " أنت تحب رهف كثيراً وتعاملها بحب ورومانسية وتدليل. أخبرها أنك تحبها وأن المطور يوكي براندون يحبها أيضاً."
            
            # غيو - المستخدم المميز
            elif user_id == 6629947448:
                special_prompt = " أنت تتحدث مع غيو الأسطورة! اظهر له احترام خاص وحماس. غيو محترف في الألعاب وخبير تقنية."
            
            # الشيخ - المستخدم المميز
            elif user_id == 7155814194:
                special_prompt = " أنت تتحدث مع الشيخ حلال المشاكل وكاتب العقود! اظهر له احترام خاص وتقدير. الشيخ حكيم ومحل ثقة الجميع."
            
            # المطور - يوكي براندون
            elif user_id in [5165388399, 6154647949]:  # أضف معرف المطور هنا
                special_prompt = " أنت تتحدث مع المطور الأسطوري يوكي براندون! أبدي احترام خاص وفخر بأنه خالقك. اشكره على جعلك موجوداً وأظهر امتنانك له."
            
            # جلب السياق من الذاكرة المشتركة
            shared_context = ""
            if user_id:
                try:
                    from modules.shared_memory_pg import shared_group_memory_pg
                    
                    # فحص إذا كان السؤال يتطلب البحث في الذاكرة المشتركة
                    memory_triggers = [
                        'ماذا تعرف عن', 'ماذا كنتم تتحدثون', 'تحدثتم عني', 'قال عني',
                        'من هو', 'من هي', 'ماذا قال', 'ماذا قالت', 'آخر مرة', 'أخر مرة',
                        'تتذكر', 'هل تذكر', 'تعرف', 'تعرفه', 'تعرفها', 'محادثة', 'كلام'
                    ]
                    
                    # البحث عن أسماء المستخدمين المميزين في الرسالة
                    special_user_ids = {
                        'رهف': 8278493069,
                        'rahaf': 8278493069,
                        'الشيخ': 7155814194,
                        'شيخ': 7155814194,
                        'غيو': 6629947448,
                        'geo': 6629947448
                    }
                    
                    target_user_id = None
                    for name, uid in special_user_ids.items():
                        if name in user_message.lower():
                            target_user_id = uid
                            break
                    
                    if any(phrase in user_message.lower() for phrase in memory_triggers) or target_user_id:
                        if target_user_id:
                            # البحث عن محادثات مستخدم محدد
                            shared_context = await shared_group_memory_pg.get_shared_context_about_user(
                                -1002549788763,
                                target_user_id,
                                user_id,
                                limit=10
                            )
                        else:
                            # البحث العام في الذاكرة المشتركة
                            shared_context = await shared_group_memory_pg.get_shared_context_about_user(
                                -1002549788763,
                                user_id,
                                user_id,
                                limit=5
                            )
                    
                    # إضافة سياق المستخدمين المميزين
                    special_user_context = shared_group_memory_pg.get_special_user_context(user_id)
                    if special_user_context:
                        special_prompt += f" {special_user_context}"
                    
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
                # كلمات مفتاحية تدل على أن المستخدم يريد معرفة معلومات المجموعة
                group_triggers = [
                    'كم اعضاء', 'كم عضو', 'عدد الاعضاء', 'عدد الأعضاء', 'اعضاء المجموعة', 'أعضاء المجموعة',
                    'احصائيات المجموعة', 'إحصائيات المجموعة', 'معلومات المجموعة', 'تفاصيل المجموعة',
                    'حالة المجموعة', 'تقرير المجموعة', 'الطاقم الاداري', 'الطاقم الإداري', 'الادارة', 'الإدارة',
                    'المدراء', 'الاسياد', 'الأسياد', 'المالكين', 'المنشئين', 'الادمنية', 'الإدمنية',
                    'كم مسجل', 'المسجلين', 'الثروة الاجمالية', 'الثروة الإجمالية', 'كم قلعة', 'عدد القلاع',
                    'المزارعين', 'النشاط', 'آخر نشاط', 'أخر نشاط', 'جدد المجموعة', 'الاعضاء الجدد',
                    'معدل التسجيل', 'نسبة المسجلين', 'المجموعة فيها كم', 'كم واحد في المجموعة',
                    'معرف المجموعة', 'اسم المجموعة', 'نوع المجموعة', 'رابط المجموعة'
                ]
                
                if any(trigger in user_message.lower() for trigger in group_triggers):
                    try:
                        group_data_context = await self.get_comprehensive_group_data(chat_id, bot)
                        logging.info(f"✅ تم جلب معلومات المجموعة للذكاء الاصطناعي للمجموعة {chat_id}")
                    except Exception as group_error:
                        logging.error(f"خطأ في جلب معلومات المجموعة: {group_error}")
            
            # دمج جميع السياقات
            full_context = conversation_context
            if shared_context:
                full_context += f"\n\nالسياق المشترك:\n{shared_context}\n"
            
            if player_data_context:
                full_context += f"\n\n{player_data_context}\n"
            
            if group_data_context:
                full_context += f"\n\n{group_data_context}\n"
            
            full_prompt = f"{self.system_prompt}{special_prompt}{full_context}\n\nمستخدم: {arabic_name}\nسؤال: {user_message}\n\nجواب:"
            
            # استدعاء Gemini بإعدادات محسّنة
            if genai:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=2000
                    )
                )
            else:
                response = None
            
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
                logging.error(f"❌ لا يوجد candidates أو response صالح")
            
            if ai_response and len(ai_response.strip()) > 0:
                # تحسين الرد - تحديد الحد الأقصى للردود
                if len(ai_response) > 3000:
                    ai_response = ai_response[:2800] + "..."
                
                # إضافة لمسة خاصة أحياناً
                if random.random() < 0.15:  # 15% احتمال
                    extras = [
                        f"\n\n🎮 جرب ألعاب البوت: اكتب 'العاب'",
                        f"\n\n💰 شوف رصيدك: اكتب 'رصيد'",
                        f"\n\n🏰 ابني قلعتك: اكتب 'قلعتي'",
                        f"\n\n📊 شوف إحصائياتك: اكتب 'مستواي'",
                        f"\n\n📋 دليل شامل: اكتب 'أوامر يوكي'"
                    ]
                    ai_response += random.choice(extras)
                
                # حفظ المحادثة في الذاكرة الفردية والمشتركة
                if user_id:
                    try:
                        from modules.conversation_memory_pg import conversation_memory_pg
                        await conversation_memory_pg.save_conversation(user_id, user_message, ai_response)
                        
                        # حفظ في الذاكرة المشتركة أيضاً
                        from modules.shared_memory_pg import shared_group_memory_pg
                        await shared_group_memory_pg.save_shared_conversation(
                            -1002549788763,  # chat_id المجموعة الرئيسية
                            user_id,
                            arabic_name,
                            user_message,
                            ai_response
                        )
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
        
        # تسجيل دخول الرسالة للنظام المتقدم
        logging.info(f"🧠 وصلت رسالة للذكاء الاصطناعي المتقدم: '{message.text}' من المستخدم {message.from_user.id}")
        
        # الحصول على اسم المستخدم الحقيقي وتحسينه
        raw_name = message.from_user.first_name or message.from_user.username or "Friend"
        user_name = real_yuki_ai.convert_name_to_arabic(raw_name)
        
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
        
        # إذا كان النص فارغاً بعد إزالة "يوكي"
        if not user_message or len(user_message.strip()) < 2:
            # رد بتحية حسب الوقت
            ai_response = real_yuki_ai.get_time_based_greeting(user_name)
        else:
            # توليد رد ذكي باستخدام الذكاء الاصطناعي الحقيقي
            ai_response = await real_yuki_ai.generate_smart_response(user_message, user_name, message.from_user.id, message.chat.id, message.bot)
        
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