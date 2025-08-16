import sqlite3
from database import get_db, format_number

class PropertyManager:
    # أسعار الممتلكات
    PROPERTY_PRICES = {
        "بيت": 10000,
        "سيارة": 5000,
        "طائرة": 50000,
        "يخت": 30000,
        "مزرعة": 20000,
        "شركة": 100000
    }

    def buy_property(self, user_id, property_name):
        conn = get_db()
        c = conn.cursor()
        
        # التحقق من وجود الممتلك
        if property_name not in self.PROPERTY_PRICES:
            return False, "❌ هذا الممتلك غير متوفر للبيع!"
        
        price = self.PROPERTY_PRICES[property_name]
        
        # جلب رصيد المستخدم
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        user_balance = result[0] if result else 0
        
        if user_balance < price:
            return False, f"❌ رصيدك غير كافي! سعر {property_name}: {format_number(price)} ريال"
        
        # جلب ممتلكات المستخدم الحالية
        c.execute("SELECT quantity FROM properties WHERE user_id = ? AND property_name = ?", (user_id, property_name))
        existing_property = c.fetchone()
        
        if existing_property:
            new_quantity = existing_property[0] + 1
            c.execute("UPDATE properties SET quantity = ? WHERE user_id = ? AND property_name = ?", 
                      (new_quantity, user_id, property_name))
        else:
            c.execute("INSERT INTO properties (user_id, property_name, quantity) VALUES (?, ?, 1)", 
                      (user_id, property_name))
        
        # خصم السعر من رصيد المستخدم
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
        conn.commit()
        conn.close()
        return True, f"✅ تم شراء {property_name} بنجاح! -{format_number(price)} ريال"

    def sell_property(self, user_id, property_name, quantity):
        conn = get_db()
        c = conn.cursor()
        
        # التحقق من وجود الممتلك
        if property_name not in self.PROPERTY_PRICES:
            return False, "❌ هذا الممتلك غير موجود!"
        
        # جلب ممتلكات المستخدم الحالية
        c.execute("SELECT quantity FROM properties WHERE user_id = ? AND property_name = ?", (user_id, property_name))
        existing_property = c.fetchone()
        
        if not existing_property or existing_property[0] < quantity:
            return False, f"❌ ليس لديك ما يكفي من {property_name} للبيع!"
        
        # حساب سعر البيع (نصف السعر الأصلي)
        sell_price = int(self.PROPERTY_PRICES[property_name] * 0.5 * quantity)
        
        # تحديث الكمية
        new_quantity = existing_property[0] - quantity
        if new_quantity > 0:
            c.execute("UPDATE properties SET quantity = ? WHERE user_id = ? AND property_name = ?", 
                      (new_quantity, user_id, property_name))
        else:
            c.execute("DELETE FROM properties WHERE user_id = ? AND property_name = ?", (user_id, property_name))
        
        # إضافة المبلغ إلى رصيد المستخدم
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (sell_price, user_id))
        conn.commit()
        conn.close()
        return True, f"✅ تم بيع {quantity} من {property_name} بـ {format_number(sell_price)} ريال"

    def gift_property(self, user_id, target_id, property_name, quantity):
        conn = get_db()
        c = conn.cursor()
        
        # جلب ممتلكات المرسل
        c.execute("SELECT quantity FROM properties WHERE user_id = ? AND property_name = ?", (user_id, property_name))
        sender_property = c.fetchone()
        
        if not sender_property or sender_property[0] < quantity:
            return False, f"❌ ليس لديك ما يكفي من {property_name} للإهداء!"
        
        # تحديث ممتلكات المرسل
        new_sender_quantity = sender_property[0] - quantity
        if new_sender_quantity > 0:
            c.execute("UPDATE properties SET quantity = ? WHERE user_id = ? AND property_name = ?", 
                      (new_sender_quantity, user_id, property_name))
        else:
            c.execute("DELETE FROM properties WHERE user_id = ? AND property_name = ?", (user_id, property_name))
        
        # تحديث ممتلكات المستقبل
        c.execute("SELECT quantity FROM properties WHERE user_id = ? AND property_name = ?", (target_id, property_name))
        receiver_property = c.fetchone()
        
        if receiver_property:
            new_receiver_quantity = receiver_property[0] + quantity
            c.execute("UPDATE properties SET quantity = ? WHERE user_id = ? AND property_name = ?", 
                      (new_receiver_quantity, target_id, property_name))
        else:
            c.execute("INSERT INTO properties (user_id, property_name, quantity) VALUES (?, ?, ?)", 
                      (target_id, property_name, quantity))
        
        conn.commit()
        conn.close()
        return True, f"✅ تم إهداء {quantity} من {property_name} للمستخدم بنجاح!"

    def get_user_properties(self, user_id):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT property_name, quantity FROM properties WHERE user_id = ?", (user_id,))
        properties_list = c.fetchall()
        conn.close()
        return properties_list