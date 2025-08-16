import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db, format_number
from modules.banking import BankingSystem
from modules.properties import PropertyManager
from modules.farm import FarmSystem
from modules.castle import CastleSystem
from modules.stocks import StockMarket
import json

banking = BankingSystem()
properties = PropertyManager()
farm = FarmSystem()
castle = CastleSystem()
stocks = StockMarket()

class ShopSystem:
    def __init__(self):
        # أنواع السلع والأسعار
        self.goods = {
            "القلعة": {
                "سور": {"price": 5000, "emoji": "🧱", "description": "يزيد دفاع قلعتك"},
                "برج حراسة": {"price": 8000, "emoji": "🏯", "description": "يراقب الأعداء ويزيد الدفاع"},
                "بوابة حديد": {"price": 12000, "emoji": "🚪", "description": "بوابة قوية تصعب اختراق القلعة"},
                "خندق": {"price": 3000, "emoji": "🕳️", "description": "يصعب تقدم الأعداء"},
                "حصن": {"price": 20000, "emoji": "🏰", "description": "مبنى دفاعي قوي"}
            },
            "المزرعة": {
                "قمح": {"price": 500, "emoji": "🌾", "description": "ينضج في 24 ساعة، سعر البيع: 1000"},
                "ذرة": {"price": 300, "emoji": "🌽", "description": "ينضج في 12 ساعة، سعر البيع: 600"},
                "طماطم": {"price": 200, "emoji": "🍅", "description": "ينضج في 8 ساعات، سعر البيع: 400"},
                "بطاطس": {"price": 400, "emoji": "🥔", "description": "ينضج في 18 ساعة، سعر البيع: 800"},
                "فراولة": {"price": 700, "emoji": "🍓", "description": "ينضج في 36 ساعة، سعر البيع: 1500"}
            },
            "العصابة": {
                "مسدس": {"price": 5000, "emoji": "🔫", "description": "يزيد قوة سرقتك بنسبة 5%"},
                "رشاش": {"price": 15000, "emoji": "💥", "description": "يزيد قوة سرقتك بنسبة 15%"},
                "دبابة": {"price": 50000, "emoji": "🚜", "description": "يزيد قوة سرقتك بنسبة 30%"},
                "طائرة حربية": {"price": 100000, "emoji": "✈️", "description": "يزيد قوة سرقتك بنسبة 50%"},
                "قنبلة": {"price": 20000, "emoji": "💣", "description": "تسبب ضررًا كبيرًا للعدو عند الهجوم"}
            },
            "الممتلكات": {
                "بيت": {"price": 10000, "emoji": "🏠", "description": "ممتلك أساسي لكل شخص"},
                "سيارة": {"price": 5000, "emoji": "🚗", "description": "تزيد من هيبتك"},
                "طائرة": {"price": 50000, "emoji": "✈️", "description": "للأثرياء فقط"},
                "يخت": {"price": 30000, "emoji": "🛥️", "description": "للتميز بحياة الرفاهية"},
                "مزرعة": {"price": 20000, "emoji": "🌾", "description": "استثمار جيد للدخل"},
                "شركة": {"price": 100000, "emoji": "🏢", "description": "تملك شركة تدر عليك دخلاً"}
            }
        }
        
        # قائمة الأقسام
        self.categories = [
            {"name": "القلعة", "emoji": "🏰"},
            {"name": "المزرعة", "emoji": "🌾"},
            {"name": "العصابة", "emoji": "🔫"},
            {"name": "الممتلكات", "emoji": "🏠"},
            {"name": "الأسهم", "emoji": "📈"}
        ]

    def get_main_menu(self):
        keyboard = InlineKeyboardMarkup(row_width=2)
        for category in self.categories:
            keyboard.add(InlineKeyboardButton(
                f"{category['emoji']} {category['name']}", 
                callback_data=f"shop_{category['name']}"
            ))
        return keyboard

    def get_category_menu(self, category_name):
        keyboard = InlineKeyboardMarkup()
        if category_name in self.goods:
            for item, details in self.goods[category_name].items():
                keyboard.add(InlineKeyboardButton(
                    f"{details['emoji']} {item} - {format_number(details['price'])} ريال", 
                    callback_data=f"buy_{category_name}_{item}"
                ))
        elif category_name == "الأسهم":
            keyboard.add(InlineKeyboardButton(
                "📦 حزمة صغيرة (10 أسهم) - 5,000 ريال", 
                callback_data="buy_stocks_10"
            ))
            keyboard.add(InlineKeyboardButton(
                "📦 حزمة متوسطة (25 أسهم) - 12,000 ريال", 
                callback_data="buy_stocks_25"
            ))
            keyboard.add(InlineKeyboardButton(
                "📦 حزمة كبيرة (50 أسهم) - 22,500 ريال", 
                callback_data="buy_stocks_50"
            ))
            keyboard.add(InlineKeyboardButton(
                "📦 حزمة ضخمة (100 أسهم) - 40,000 ريال", 
                callback_data="buy_stocks_100"
            ))
        
        keyboard.add(InlineKeyboardButton("🔙 رجوع إلى المتجر", callback_data="shop_main"))
        return keyboard

    def get_item_info(self, category, item):
        if category == "الأسهم":
            quantity = int(item)
            price = self.get_stocks_price(quantity)
            return {
                "name": f"حزمة {quantity} سهم",
                "price": price,
                "description": f"شراء {quantity} سهم بسعر {format_number(price)} ريال"
            }
        
        if category in self.goods and item in self.goods[category]:
            return self.goods[category][item]
        
        return None

    def get_stocks_price(self, quantity):
        # سعر الحزمة أقل من شراء كل سهم على حدة
        prices = {
            10: 5000,
            25: 12000,
            50: 22500,
            100: 40000
        }
        return prices.get(quantity, quantity * 500)  # 500 ريال للسهم

    def buy_item(self, user_id, category, item):
        # الحصول على معلومات السلعة
        item_info = self.get_item_info(category, item)
        if not item_info:
            return False, "❌ السلعة غير متوفرة!"
        
        price = item_info["price"]
        
        # التحقق من رصيد المستخدم
        balance = banking.get_balance(user_id)
        if balance < price:
            return False, f"❌ رصيدك غير كافي! تحتاج {format_number(price)} ريال"
        
        # خصم المبلغ
        banking.add_money(user_id, -price)
        
        # إضافة السلعة للمستخدم
        if category == "القلعة":
            castle.build(user_id, item)
        elif category == "المزرعة":
            farm.plant_crop(user_id, item)
        elif category == "العصابة":
            # نظام العصابة سيتم تنفيذه لاحقاً
            pass
        elif category == "الممتلكات":
            properties.buy_property(user_id, item)
        elif category == "الأسهم":
            quantity = int(item)
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE stocks SET amount = amount + ? WHERE user_id = ?", (quantity, user_id))
            conn.commit()
            conn.close()
        
        return True, f"✅ تم شراء {item} بنجاح! -{format_number(price)} ريال"