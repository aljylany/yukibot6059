"""
🧠 نظام تحليل المستخدمين المتقدم - جداول قاعدة البيانات
"""

import aiosqlite
import logging
from datetime import datetime
from config.database import DATABASE_URL

async def create_user_analysis_tables():
    """إنشاء جميع جداول نظام تحليل المستخدمين"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            
            # 📊 جدول التحليل الأساسي للمستخدمين
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_analysis (
                    user_id INTEGER PRIMARY KEY,
                    
                    -- تحليل الشخصية (نقاط من 0.0 إلى 1.0)
                    extravert_score REAL DEFAULT 0.5,      -- اجتماعي
                    risk_taker_score REAL DEFAULT 0.5,     -- مغامر
                    leader_score REAL DEFAULT 0.5,         -- قيادي
                    patient_score REAL DEFAULT 0.5,        -- صبور
                    competitive_score REAL DEFAULT 0.5,    -- تنافسي
                    
                    -- الاهتمامات (نقاط من 0.0 إلى 1.0)
                    games_interest REAL DEFAULT 0.0,       -- الألعاب
                    money_interest REAL DEFAULT 0.0,       -- المال والاستثمار
                    social_interest REAL DEFAULT 0.0,      -- التفاعل الاجتماعي
                    entertainment_interest REAL DEFAULT 0.0, -- التسلية
                    
                    -- أنماط النشاط (JSON)
                    activity_pattern TEXT,                  -- {"morning": 0.2, "afternoon": 0.3, "evening": 0.5}
                    
                    -- الحالة المزاجية (JSON)
                    mood_history TEXT,                      -- آخر 20 حالة مزاجية
                    current_mood TEXT DEFAULT 'محايد',     -- الحالة المزاجية الحالية
                    
                    -- إحصائيات التفاعل
                    total_messages INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    investments_made INTEGER DEFAULT 0,
                    social_interactions INTEGER DEFAULT 0,
                    commands_used INTEGER DEFAULT 0,
                    
                    -- خصائص إضافية
                    favorite_game_type TEXT,                -- نوع اللعبة المفضل
                    investment_style TEXT DEFAULT 'محافظ', -- أسلوب الاستثمار
                    communication_style TEXT DEFAULT 'طبيعي', -- أسلوب التواصل
                    
                    -- طوابع زمنية
                    first_analysis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # 🧠 جدول الذكريات المتقدم
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_memories (
                    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    
                    -- تصنيف الذكرى
                    memory_type TEXT NOT NULL,              -- 'game_win', 'game_loss', 'investment', 'social', 'achievement', 'conversation'
                    memory_category TEXT,                   -- فئة فرعية
                    
                    -- محتوى الذكرى (JSON)
                    memory_data TEXT NOT NULL,              -- التفاصيل الكاملة
                    memory_summary TEXT,                    -- ملخص نصي
                    
                    -- أهمية الذكرى
                    importance_score REAL DEFAULT 0.5,     -- 0.0 = غير مهم، 1.0 = مهم جداً
                    emotional_impact REAL DEFAULT 0.0,     -- التأثير العاطفي
                    
                    -- معلومات السياق
                    context_users TEXT,                     -- المستخدمين المرتبطين (JSON)
                    context_location TEXT,                  -- المجموعة أو المكان
                    
                    -- طوابع زمنية
                    memory_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_recalled TIMESTAMP NULL,           -- آخر مرة تم تذكر هذه الذكرى
                    recall_count INTEGER DEFAULT 0,         -- عدد مرات التذكر
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # 👥 جدول العلاقات الاجتماعية
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_relationships (
                    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER NOT NULL,
                    user2_id INTEGER NOT NULL,
                    
                    -- قوة العلاقة
                    relationship_strength REAL DEFAULT 0.0, -- 0.0 = غرباء، 1.0 = أصدقاء مقربين
                    friendship_level TEXT DEFAULT 'stranger', -- 'stranger', 'acquaintance', 'friend', 'close_friend', 'rival'
                    
                    -- إحصائيات التفاعل
                    total_interactions INTEGER DEFAULT 0,
                    games_together INTEGER DEFAULT 0,
                    messages_exchanged INTEGER DEFAULT 0,
                    competitive_interactions INTEGER DEFAULT 0,
                    cooperative_interactions INTEGER DEFAULT 0,
                    
                    -- نوع التفاعل (JSON)
                    interaction_type TEXT,                  -- {"competitive": 0.7, "cooperative": 0.3}
                    
                    -- طوابع زمنية
                    first_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user1_id) REFERENCES users(user_id),
                    FOREIGN KEY (user2_id) REFERENCES users(user_id),
                    UNIQUE(user1_id, user2_id)
                )
            ''')
            
            # ⚙️ جدول إعدادات التحليل للمجموعات
            await db.execute('''
                CREATE TABLE IF NOT EXISTS group_analysis_settings (
                    chat_id INTEGER PRIMARY KEY,
                    analysis_enabled BOOLEAN DEFAULT TRUE,
                    
                    -- من قام بالتغيير الأخير
                    last_modified_by INTEGER,
                    last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- إعدادات متقدمة
                    allow_mood_analysis BOOLEAN DEFAULT TRUE,
                    allow_relationship_analysis BOOLEAN DEFAULT TRUE,
                    allow_memory_system BOOLEAN DEFAULT TRUE,
                    allow_predictive_responses BOOLEAN DEFAULT TRUE,
                    
                    -- معلومات إضافية
                    disable_reason TEXT,                     -- سبب الإيقاف
                    notification_sent BOOLEAN DEFAULT FALSE, -- تم إرسال إعلام للأعضاء
                    
                    -- إعدادات خصوصية
                    data_retention_days INTEGER DEFAULT 365, -- مدة حفظ البيانات بالأيام
                    auto_delete_inactive BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # 📈 جدول إحصائيات استخدام النظام
            await db.execute('''
                CREATE TABLE IF NOT EXISTS analysis_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER,
                    
                    -- نوع النشاط
                    activity_type TEXT NOT NULL,            -- 'message', 'game', 'command', 'investment'
                    activity_details TEXT,                  -- تفاصيل إضافية (JSON)
                    
                    -- معلومات التحليل
                    mood_detected TEXT,                     -- المزاج المكتشف
                    keywords_extracted TEXT,                -- الكلمات المفتاحية (JSON)
                    sentiment_score REAL,                   -- نتيجة تحليل المشاعر
                    
                    -- معلومات وقتية
                    hour_of_day INTEGER,                    -- ساعة اليوم (0-23)
                    day_of_week INTEGER,                    -- يوم الأسبوع (0-6)
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # 🎯 جدول توقعات السلوك والتوصيات
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_predictions (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    
                    -- نوع التوقع
                    prediction_type TEXT NOT NULL,          -- 'next_game', 'investment_move', 'mood_change', 'interaction'
                    predicted_action TEXT,                  -- العمل المتوقع
                    confidence_score REAL DEFAULT 0.5,     -- مستوى الثقة (0.0-1.0)
                    
                    -- أساس التوقع
                    based_on_patterns TEXT,                 -- الأنماط المعتمد عليها (JSON)
                    historical_accuracy REAL,              -- دقة التوقعات السابقة
                    
                    -- النتيجة الفعلية
                    actual_outcome TEXT,                    -- ما حدث فعلاً
                    prediction_accuracy REAL,              -- دقة هذا التوقع
                    
                    -- طوابع زمنية
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,                   -- متى ينتهي التوقع
                    verified_at TIMESTAMP                   -- متى تم التحقق من النتيجة
                )
            ''')
            
            # إنشاء الفهارس لتحسين الأداء
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_analysis_updated ON user_analysis(last_updated)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_memories_user_type ON user_memories(user_id, memory_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_memories_importance ON user_memories(importance_score DESC)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_memories_date ON user_memories(memory_date DESC)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_relationships_strength ON user_relationships(relationship_strength DESC)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_relationships_users ON user_relationships(user1_id, user2_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_group_analysis_enabled ON group_analysis_settings(analysis_enabled)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_statistics_user_time ON analysis_statistics(user_id, timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_statistics_activity ON analysis_statistics(activity_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_predictions_user_type ON user_predictions(user_id, prediction_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_predictions_expires ON user_predictions(expires_at)")
            
            await db.commit()
            print("✅ تم إنشاء جداول نظام تحليل المستخدمين بنجاح!")
            
            # فحص الجداول المنشأة
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%analysis%' OR name LIKE '%memories%' OR name LIKE '%relationships%' OR name LIKE '%predictions%'") as cursor:
                tables = await cursor.fetchall()
                print("📊 جداول نظام التحليل:")
                for table in tables:
                    print(f"  ✓ {table[0]}")
                    
    except Exception as e:
        print(f"❌ خطأ في إنشاء جداول نظام التحليل: {e}")
        logging.error(f"خطأ في إنشاء جداول نظام التحليل: {e}")
        raise


async def drop_analysis_tables():
    """حذف جميع جداول التحليل (للتطوير فقط)"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute("DROP TABLE IF EXISTS user_predictions")
            await db.execute("DROP TABLE IF EXISTS analysis_statistics")
            await db.execute("DROP TABLE IF EXISTS group_analysis_settings")
            await db.execute("DROP TABLE IF EXISTS user_relationships")
            await db.execute("DROP TABLE IF EXISTS user_memories")
            await db.execute("DROP TABLE IF EXISTS user_analysis")
            await db.commit()
            print("🗑️ تم حذف جداول نظام التحليل")
    except Exception as e:
        print(f"❌ خطأ في حذف جداول التحليل: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(create_user_analysis_tables())