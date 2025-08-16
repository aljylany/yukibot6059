import sqlite3
import json
import random
from database import get_db, format_number
from modules.banking import BankingSystem

banking = BankingSystem()

# أنواع المباني وأسعارها
BUILDING_TYPES = {
    "سور": {"price": 5000, "defense": 20},
    "برج حراسة": {"price": 8000, "defense": 30},
    "بوابة حديد": {"price": 12000, "defense": 50},
    "خندق": {"price": 3000, "defense": 15},
    "حصن": {"price": 20000, "defense": 70}
}

class CastleSystem:
    def build(self, user_id, building_type):
        conn = get_db()
        c = conn.cursor()
        
        # التحقق من صحة نوع البناء
        if building_type not in BUILDING_TYPES:
            return False, "❌ نوع البناء غير متاح!"
        
        # التحقق من رصيد المستخدم
        building_info = BUILDING_TYPES[building_type]
        balance = banking.get_balance(user_id)
        
        if balance < building_info["price"]:
            return False, f"❌ رصيدك غير كافي! سعر البناء: {format_number(building_info['price'])} ريال"
        
        # جلب معلومات القلعة الحالية
        c.execute("SELECT buildings FROM castles WHERE user_id = ?", (user_id,))
        castle = c.fetchone()
        
        buildings = []
        if castle and castle[0]:
            buildings = json.loads(castle[0])
            # التحقق إذا كان البناء موجوداً بالفعل
            for building in buildings:
                if building['type'] == building_type:
                    building['quantity'] = building.get('quantity', 1) + 1
                    # تحديث قاعدة البيانات
                    c.execute("UPDATE castles SET buildings = ? WHERE user_id = ?", 
                              (json.dumps(buildings), user_id))
                    conn.commit()
                    conn.close()
                    return True, f"🏰 تم تحديث {building_type} بنجاح! (الكمية: {building['quantity']})"
        
        # إضافة البناء الجديد
        buildings.append({
            "type": building_type,
            "quantity": 1,
            "defense": building_info["defense"]
        })
        
        # خصم سعر البناء
        banking.add_money(user_id, -building_info["price"])
        
        # حفظ في قاعدة البيانات
        if castle:
            c.execute("UPDATE castles SET buildings = ? WHERE user_id = ?", 
                      (json.dumps(buildings), user_id))
        else:
            c.execute("INSERT INTO castles (user_id, buildings) VALUES (?, ?)", 
                      (user_id, json.dumps(buildings)))
        
        conn.commit()
        conn.close()
        return True, f"🏰 تم بناء {building_type} بنجاح! +{building_info['defense']} دفاع"

    def upgrade_army(self, user_id):
        conn = get_db()
        c = conn.cursor()
        
        # جلب مستوى الجيش الحالي
        c.execute("SELECT army_level FROM castles WHERE user_id = ?", (user_id,))
        castle = c.fetchone()
        
        if not castle:
            return False, "❌ ليس لديك قلعة! قم ببناء شيء أولاً"
        
        current_level = castle[0] or 1
        upgrade_cost = current_level * 10000
        
        # التحقق من الرصيد
        balance = banking.get_balance(user_id)
        if balance < upgrade_cost:
            return False, f"❌ رصيدك غير كافي! سعر الترقية: {format_number(upgrade_cost)} ريال"
        
        # ترقية الجيش
        new_level = current_level + 1
        banking.add_money(user_id, -upgrade_cost)
        c.execute("UPDATE castles SET army_level = ? WHERE user_id = ?", (new_level, user_id))
        conn.commit()
        conn.close()
        return True, f"⚔️ تم ترقية جيشك إلى المستوى {new_level}! هجومك أقوى الآن"

    def attack(self, attacker_id, target_id):
        conn = get_db()
        c = conn.cursor()
        
        # جذب معلومات المهاجم
        c.execute("SELECT buildings, army_level FROM castles WHERE user_id = ?", (attacker_id,))
        attacker_castle = c.fetchone()
        
        # جذب معلومات المدافع
        c.execute("SELECT buildings, army_level FROM castles WHERE user_id = ?", (target_id,))
        target_castle = c.fetchone()
        
        # التحقق من وجود القلاع
        if not attacker_castle or not target_castle:
            return False, "❌ أحد اللاعبين ليس لديه قلعة!"
        
        # حساب قوة الهجوم والدفاع
        attacker_buildings = json.loads(attacker_castle[0]) if attacker_castle[0] else []
        target_buildings = json.loads(target_castle[0]) if target_castle[0] else []
        
        attack_power = sum(b['defense'] * b.get('quantity', 1) for b in attacker_buildings) * (attacker_castle[1] or 1)
        defense_power = sum(b['defense'] * b.get('quantity', 1) for b in target_buildings) * (target_castle[1] or 1)
        
        # حساب فرص النجاح (40% للمهاجم، 60% للمدافع)
        success_chance = attack_power / (attack_power + defense_power) * 0.4
        
        # نتيجة الهجوم
        if random.random() < success_chance:
            # الهجوم ناجح
            loot = min(5000, banking.get_balance(target_id) * 0.2)  # 20% من رصيد المدافع بحد أقصى 5000
            banking.add_money(attacker_id, loot)
            banking.add_money(target_id, -loot)
            
            # تدمير جزء من دفاعات المدافع (30% فرصة تدمير بناء)
            if random.random() < 0.3 and target_buildings:
                destroyed_building = random.choice(target_buildings)
                target_buildings.remove(destroyed_building)
                c.execute("UPDATE castles SET buildings = ? WHERE user_id = ?", 
                          (json.dumps(target_buildings), target_id))
                conn.commit()
                
                result = f"⚔️ هجوم ناجح! سرقت {format_number(loot)} ريال ودمرت {destroyed_building['type']}!"
            else:
                result = f"⚔️ هجوم ناجح! سرقت {format_number(loot)} ريال!"
        else:
            # الهجوم فاشل
            penalty = min(2000, banking.get_balance(attacker_id) * 0.1)  # 10% من رصيد المهاجم بحد أقصى 2000
            banking.add_money(attacker_id, -penalty)
            
            # تدمير جزء من هجوم المهاجم (20% فرصة تدمير بناء)
            if random.random() < 0.2 and attacker_buildings:
                destroyed_building = random.choice(attacker_buildings)
                attacker_buildings.remove(destroyed_building)
                c.execute("UPDATE castles SET buildings = ? WHERE user_id = ?", 
                          (json.dumps(attacker_buildings), attacker_id))
                conn.commit()
                
                result = f"🛡️ هجوم فاشل! خسرت {format_number(penalty)} ريال ودمر {destroyed_building['type']}!"
            else:
                result = f"🛡️ هجوم فاشل! خسرت {format_number(penalty)} ريال!"
        
        conn.close()
        return True, result

    def get_castle_info(self, user_id):
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT buildings, army_level FROM castles WHERE user_id = ?", (user_id,))
        castle = c.fetchone()
        
        if not castle:
            return "🏰 ليس لديك قلعة بعد! استخدم 'بناء' لتبدأ"
        
        buildings = json.loads(castle[0]) if castle[0] else []
        army_level = castle[1] or 1
        
        # حساب إجمالي الدفاع
        total_defense = sum(b['defense'] * b.get('quantity', 1) for b in buildings) * army_level
        
        castle_info = f"🏰 <b>قلعتك</b>\n\n"
        castle_info += f"• مستوى الجيش: {army_level} ⚔️\n"
        castle_info += f"• قوة الدفاع: {total_defense} 🛡️\n\n"
        
        if buildings:
            castle_info += "🔧 <b>المباني</b>:\n"
            for building in buildings:
                quantity = building.get('quantity', 1)
                castle_info += f"• {building['type']} (×{quantity}) - دفاع: {building['defense'] * quantity}\n"
        else:
            castle_info += "❌ لا توجد مباني مبنية بعد!\n"
        
        return castle_info

    def get_built_castles_count(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM castles WHERE buildings IS NOT NULL")
        count = c.fetchone()[0]
        conn.close()
        return count