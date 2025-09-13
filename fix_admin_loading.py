#!/usr/bin/env python3
"""
أداة إصلاح تحميل نظام المشرفين والمالكين
Fix admin loading system
"""

import sqlite3
import asyncio
import sys
import os

# إضافة مسار المشروع للاستيراد
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def fix_and_reload_admin_system():
    """إصلاح وإعادة تحميل نظام المشرفين"""
    print("🔧 إصلاح نظام تحميل المشرفين والمالكين...")
    print("=" * 50)
    
    try:
        # استيراد النظام الحالي
        from config.hierarchy import GROUP_OWNERS, MODERATORS, MASTERS
        from database.operations import execute_query
        
        print("📊 حالة النظام قبل الإصلاح:")
        print(f"   • مجموعات بمالكين: {len(GROUP_OWNERS)}")
        print(f"   • مجموعات بمشرفين: {len(MODERATORS)}")
        print(f"   • عدد الأسياد: {len(MASTERS)}")
        
        # مسح القواميس وإعادة تحميلها
        GROUP_OWNERS.clear()
        MODERATORS.clear()
        
        print("\n🔄 إعادة تحميل البيانات من قاعدة البيانات...")
        
        # تحميل المالكين (مالك، مالك اساسي، ادمن)
        owners_query = "SELECT user_id, chat_id FROM group_ranks WHERE rank_type IN ('مالك', 'مالك اساسي', 'ادمن')"
        owners = await execute_query(owners_query, fetch_all=True)
        
        print(f"📋 وجدت {len(owners) if owners else 0} مالك في قاعدة البيانات")
        
        if owners:
            for owner in owners:
                if isinstance(owner, tuple) and len(owner) >= 2:
                    user_id = owner[0]
                    chat_id = owner[1]
                elif hasattr(owner, 'get') and callable(getattr(owner, 'get')):
                    user_id = owner.get('user_id')
                    chat_id = owner.get('chat_id')
                else:
                    continue
                
                if user_id is None or chat_id is None:
                    continue

                if chat_id not in GROUP_OWNERS:
                    GROUP_OWNERS[chat_id] = []
                if user_id not in GROUP_OWNERS[chat_id]:
                    GROUP_OWNERS[chat_id].append(user_id)
                    print(f"   ✅ تم إضافة مالك {user_id} للمجموعة {chat_id}")

        # تحميل المشرفين (مشرف، مميز)
        moderators_query = "SELECT user_id, chat_id FROM group_ranks WHERE rank_type IN ('مشرف', 'مميز')"
        moderators = await execute_query(moderators_query, fetch_all=True)
        
        print(f"📋 وجدت {len(moderators) if moderators else 0} مشرف في قاعدة البيانات")
        
        if moderators:
            for moderator in moderators:
                if isinstance(moderator, tuple) and len(moderator) >= 2:
                    user_id = moderator[0]
                    chat_id = moderator[1]
                elif hasattr(moderator, 'get') and callable(getattr(moderator, 'get')):
                    user_id = moderator.get('user_id')
                    chat_id = moderator.get('chat_id')
                else:
                    continue
                
                if user_id is None or chat_id is None:
                    continue

                if chat_id not in MODERATORS:
                    MODERATORS[chat_id] = []
                if user_id not in MODERATORS[chat_id]:
                    MODERATORS[chat_id].append(user_id)
                    print(f"   ✅ تم إضافة مشرف {user_id} للمجموعة {chat_id}")

        print(f"\n📊 حالة النظام بعد الإصلاح:")
        print(f"   • مجموعات بمالكين: {len(GROUP_OWNERS)}")
        print(f"   • مجموعات بمشرفين: {len(MODERATORS)}")
        
        print(f"\n📋 تفاصيل المالكين:")
        for group_id, owners_list in GROUP_OWNERS.items():
            print(f"   • مجموعة {group_id}: {len(owners_list)} مالك")
            
        print(f"\n📋 تفاصيل المشرفين:")
        for group_id, mods_list in MODERATORS.items():
            print(f"   • مجموعة {group_id}: {len(mods_list)} مشرف")
        
        # اختبار دالة get_group_admins
        from config.hierarchy import get_group_admins
        print(f"\n🔧 اختبار دالة get_group_admins:")
        for group_id in list(GROUP_OWNERS.keys()) + list(MODERATORS.keys()):
            if group_id not in [-1, 0]:  # تجاهل القيم الخاطئة
                admins = get_group_admins(group_id)
                total_admins = len(admins['masters']) + len(admins['owners']) + len(admins['moderators'])
                print(f"   • مجموعة {group_id}: {total_admins} إجمالي المديرين")
                print(f"     - أسياد: {len(admins['masters'])}")
                print(f"     - مالكون: {len(admins['owners'])}")
                print(f"     - مشرفون: {len(admins['moderators'])}")
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح النظام: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("✅ انتهى إصلاح النظام")

if __name__ == "__main__":
    asyncio.run(fix_and_reload_admin_system())