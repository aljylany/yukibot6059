import sqlite3
import json
import time
from database import get_db, format_number
from modules.banking import BankingSystem

banking = BankingSystem()

# أنواع المحاصيل وأسعارها وأوقات نضوجها
CROP_TYPES = {
    "قمح": {"price": 500, "grow_time": 24 * 3600, "sell_price": 1000},
    "ذرة": {"price": 300, "grow_time": 12 * 3600, "sell_price": 600},
    "طماطم": {"price": 200, "grow_time": 8 * 3600, "sell_price": 400},
    "بطاطس": {"price": 400, "grow_time": 18 * 3600, "sell_price": 800},
    "فراولة": {"price": 700, "grow_time": 36 * 3600, "sell_price": 1500}
}

class FarmSystem:
    def plant_crop(self, user_id, crop_type):
        conn = get_db()
        c = conn.cursor()
        
        # التحقق من صحة نوع المحصول
        if crop_type not in CROP_TYPES:
            return False, "❌ نوع المحصول غير متاح!"
        
        # التحقق من وجود مزرعة للمستخدم
        c.execute("SELECT crops FROM farms WHERE user_id = ?", (user_id,))
        farm = c.fetchone()
        
        # التحقق من رصيد المستخدم
        balance = banking.get_balance(user_id)
        crop_price = CROP_TYPES[crop_type]["price"]
        
        if balance < crop_price:
            return False, f"❌ رصيدك غير كافي! سعر البذور: {format_number(crop_price)} ريال"
        
        # إذا كان هناك محصول موجود
        if farm and farm[0]:
            existing_crop = json.loads(farm[0])
            if existing_crop.get('type') == crop_type:
                existing_crop['quantity'] = existing_crop.get('quantity', 1) + 1
                c.execute("UPDATE farms SET crops = ? WHERE user_id = ?", 
                          (json.dumps(existing_crop), user_id))
                conn.commit()
                conn.close()
                return True, f"🌱 تمت إضافة المزيد من {crop_type} إلى مزرعتك! (الكمية: {existing_crop['quantity']})"
            else:
                return False, f"❌ لديك محصول {existing_crop.get('type')} مزروع بالفعل!"
        
        # خصم سعر البذور
        banking.add_money(user_id, -crop_price)
        
        # إنشاء المحصول الجديد
        new_crop = {
            "type": crop_type,
            "quantity": 1,
            "planted_at": time.time(),
            "grow_time": CROP_TYPES[crop_type]["grow_time"],
            "sell_price": CROP_TYPES[crop_type]["sell_price"]
        }
        
        # حفظ في قاعدة البيانات
        if farm:
            c.execute("UPDATE farms SET crops = ? WHERE user_id = ?", 
                      (json.dumps(new_crop), user_id))
        else:
            c.execute("INSERT INTO farms (user_id, crops) VALUES (?, ?)", 
                      (user_id, json.dumps(new_crop)))
        
        conn.commit()
        conn.close()
        return True, f"✅ تم زرع {crop_type} بنجاح! ستنضج بعد {self.format_time(CROP_TYPES[crop_type]['grow_time'])}"

    def harvest_crops(self, user_id):
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT crops FROM farms WHERE user_id = ?", (user_id,))
        farm = c.fetchone()
        
        if not farm or not farm[0]:
            return False, "❌ لا يوجد محصول لحصاده!"
        
        crop = json.loads(farm[0])
        current_time = time.time()
        elapsed = current_time - crop["planted_at"]
        
        if elapsed < crop["grow_time"]:
            remaining = crop["grow_time"] - elapsed
            return False, f"⏳ المحصول لم ينضج بعد! متبقي: {self.format_time(remaining)}"
        
        # حساب الربح
        quantity = crop.get('quantity', 1)
        profit = crop["sell_price"] * quantity
        banking.add_money(user_id, profit)
        
        # حذف المحصول
        c.execute("UPDATE farms SET crops = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True, f"💰 تم حصاد المحصول! ربحت {format_number(profit)} ريال"

    def get_farm_info(self, user_id):
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT crops FROM farms WHERE user_id = ?", (user_id,))
        farm = c.fetchone()
        
        if not farm or not farm[0]:
            return "🌱 مزرعتك فارغة! استخدم 'زرع' لبدء الزراعة"
        
        crop = json.loads(farm[0])
        current_time = time.time()
        elapsed = current_time - crop["planted_at"]
        
        if elapsed < crop["grow_time"]:
            remaining = crop["grow_time"] - elapsed
            status = f"🌱 محصول {crop['type']} في طور النمو\n⏱ متبقي: {self.format_time(remaining)}"
        else:
            status = f"✅ محصول {crop['type']} جاهز للحصاد! استخدم 'حصاد'"
        
        quantity = crop.get('quantity', 1)
        return f"🌾 <b>مزرعتك</b>\n\n{status}\n\n" \
               f"• الكمية: {quantity}\n" \
               f"💸 أرباحك عند الحصاد: {format_number(crop['sell_price'] * quantity)} ريال"

    def get_market_items(self):
        return CROP_TYPES

    def get_active_farms_count(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM farms WHERE crops IS NOT NULL")
        count = c.fetchone()[0]
        conn.close()
        return count

    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)} ساعة {int(minutes)} دقيقة"