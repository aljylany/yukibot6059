#!/usr/bin/env python3
"""
أداة تشخيصية لفحص نظام المشرفين والمالكين
Diagnostic tool for checking admin and owner system
"""

import sqlite3
import asyncio
import sys
import os

# إضافة مسار المشروع للاستيراد
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_admin_system():
    """فحص شامل لنظام المشرفين والمالكين"""
    print("🔍 فحص نظام المشرفين والمالكين...")
    print("=" * 50)
    
    # فحص قاعدة البيانات
    try:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute("SELECT COUNT(*) FROM group_ranks")
        total_ranks = cursor.fetchone()[0]
        print(f"📊 إجمالي الرتب في قاعدة البيانات: {total_ranks}")
        
        # الرتب حسب النوع
        cursor.execute("SELECT rank_type, COUNT(*) FROM group_ranks GROUP BY rank_type")
        ranks_by_type = cursor.fetchall()
        print("\n🏆 الرتب حسب النوع:")
        for rank_type, count in ranks_by_type:
            print(f"   • {rank_type}: {count}")
        
        # المجموعات الموجودة
        cursor.execute("SELECT DISTINCT chat_id, COUNT(*) as admin_count FROM group_ranks GROUP BY chat_id")
        groups = cursor.fetchall()
        print(f"\n🏘️ المجموعات الموجودة ({len(groups)}):")
        for chat_id, admin_count in groups:
            print(f"   • مجموعة {chat_id}: {admin_count} مشرف/مالك")
            
            # تفاصيل كل مجموعة
            cursor.execute("SELECT rank_type, COUNT(*) FROM group_ranks WHERE chat_id = ? GROUP BY rank_type", (chat_id,))
            group_ranks = cursor.fetchall()
            for rank_type, count in group_ranks:
                print(f"     - {rank_type}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
    
    # فحص القواميس المحملة في الذاكرة
    try:
        from config.hierarchy import GROUP_OWNERS, MODERATORS, MASTERS, get_group_admins
        
        print(f"\n🧠 القواميس المحملة في الذاكرة:")
        print(f"   • الأسياد: {len(MASTERS)}")
        print(f"   • مجموعات بمالكين: {len(GROUP_OWNERS)}")
        print(f"   • مجموعات بمشرفين: {len(MODERATORS)}")
        
        print(f"\n📋 تفاصيل المالكين:")
        for group_id, owners in GROUP_OWNERS.items():
            print(f"   • مجموعة {group_id}: {len(owners)} مالك")
            
        print(f"\n📋 تفاصيل المشرفين:")
        for group_id, mods in MODERATORS.items():
            print(f"   • مجموعة {group_id}: {len(mods)} مشرف")
        
        # اختبار دالة get_group_admins
        print(f"\n🔧 اختبار دالة get_group_admins:")
        for group_id in GROUP_OWNERS.keys():
            admins = get_group_admins(group_id)
            print(f"   • مجموعة {group_id}:")
            print(f"     - أسياد: {len(admins['masters'])}")
            print(f"     - مالكون: {len(admins['owners'])}")
            print(f"     - مشرفون: {len(admins['moderators'])}")
            
    except Exception as e:
        print(f"❌ خطأ في فحص القواميس: {e}")
    
    print("\n" + "=" * 50)
    print("✅ انتهى الفحص التشخيصي")

if __name__ == "__main__":
    asyncio.run(check_admin_system())