"""
وحدة الأسهم
Stocks Module
"""

import logging
import random
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, execute_query, add_transaction
from utils.states import StocksStates
from utils.helpers import format_number, is_valid_amount
from services.api_client import get_stock_prices

# أسهم وهمية للعبة
GAME_STOCKS = {
    "AAPL": {"name": "Apple Inc.", "base_price": 150, "volatility": 0.05, "emoji": "🍎", "category": "تكنولوجيا"},
    "GOOGL": {"name": "Alphabet Inc.", "base_price": 2500, "volatility": 0.04, "emoji": "🔍", "category": "تكنولوجيا"},
    "TSLA": {"name": "Tesla Inc.", "base_price": 800, "volatility": 0.08, "emoji": "🚗", "category": "سيارات"},
    "AMZN": {"name": "Amazon.com Inc.", "base_price": 3200, "volatility": 0.06, "emoji": "📦", "category": "تجارة إلكترونية"},
    "MSFT": {"name": "Microsoft Corp.", "base_price": 300, "volatility": 0.04, "emoji": "💻", "category": "تكنولوجيا"},
    "NVDA": {"name": "NVIDIA Corp.", "base_price": 450, "volatility": 0.07, "emoji": "🎮", "category": "أشباه موصلات"},
    "META": {"name": "Meta Platforms", "base_price": 320, "volatility": 0.06, "emoji": "📱", "category": "وسائل التواصل"},
    "NFLX": {"name": "Netflix Inc.", "base_price": 400, "volatility": 0.05, "emoji": "🎬", "category": "ترفيه"}
}


async def show_stocks_menu(message: Message):
    """عرض قائمة الأسهم الرئيسية"""
    try:
        if not message.from_user:
            await message.reply("❌ خطأ في معرف المستخدم")
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على محفظة المستخدم
        portfolio = await get_user_stocks(message.from_user.id)
        portfolio_value = await calculate_portfolio_value(portfolio)
        
        # حساب عدد الأسهم المختلفة
        stocks_count = len(portfolio) if isinstance(portfolio, list) else 0
        
        stocks_text = f"""
📈 **سوق الأسهم**

💰 رصيدك النقدي: {format_number(user['balance'])}$
💼 قيمة المحفظة: {format_number(portfolio_value)}$
📊 إجمالي الثروة: {format_number(user['balance'] + portfolio_value)}$

🎯 عدد الأسهم المملوكة: {stocks_count}

💡 نصيحة: تنويع المحفظة يقلل المخاطر!

📋 **الأوامر المتاحة:**
📈 اكتب: "شراء اسهم" لشراء أسهم
📉 اكتب: "بيع اسهم" لبيع أسهم
💼 اكتب: "محفظتي" لعرض محفظة الأسهم
📊 اكتب: "اسعار الاسهم" لعرض أسعار السوق
        """
        
        await message.reply(stocks_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة الأسهم: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الأسهم")


async def list_available_stocks(message: Message):
    """عرض قائمة الأسهم المتاحة"""
    try:
        current_prices = await get_current_stock_prices()
        
        stocks_text = """
📈 **الأسهم المتاحة للتداول:**

"""
        for symbol, stock_info in GAME_STOCKS.items():
            current_price = current_prices.get(symbol, stock_info['base_price'])
            change = random.uniform(-5, 5)
            change_emoji = "📈" if change >= 0 else "📉"
            
            stocks_text += f"{stock_info['emoji']} **{symbol}** - {stock_info['name']}\n"
            stocks_text += f"   💰 السعر: ${current_price:.2f}\n"
            stocks_text += f"   {change_emoji} التغيير: {change:+.2f}%\n"
            stocks_text += f"   📊 الفئة: {stock_info['category']}\n\n"
        
        stocks_text += "💡 لشراء سهم: اكتب 'شراء سهم [الرمز]'\n💡 مثال: شراء سهم AAPL"
        
        await message.reply(stocks_text)
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة الأسهم: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الأسهم")

async def buy_stock_command(message: Message):
    """معالجة أمر شراء الأسهم"""
    try:
        if not message.text:
            return
            
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply("❌ يرجى كتابة رمز السهم\n\nمثال: شراء سهم AAPL")
            return
            
        symbol = parts[2].upper()
        
        if symbol not in GAME_STOCKS:
            await message.reply("❌ رمز السهم غير متاح\n\nاستخدم 'قائمة الاسهم' لعرض الأسهم المتاحة")
            return
            
        stock_info = GAME_STOCKS[symbol]
        current_prices = await get_current_stock_prices()
        current_price = current_prices.get(symbol, stock_info['base_price'])
        
        await message.reply(f"📈 تم اختيار {stock_info['emoji']} {symbol}\n\n💰 السعر الحالي: ${current_price:.2f}\n\n⏳ يرجى إدخال الكمية...")
    except Exception as e:
        logging.error(f"خطأ في شراء السهم: {e}")
        await message.reply("❌ حدث خطأ في عملية الشراء")

async def sell_stock_command(message: Message):
    """معالجة أمر بيع الأسهم"""
    try:
        user_stocks = await get_user_stocks(message.from_user.id)
        
        if not user_stocks:
            await message.reply("❌ لا تملك أي أسهم للبيع\n\nاستخدم 'اسهم' لشراء أسهم أولاً")
            return
            
        await message.reply("📉 جاري عرض أسهمك للبيع...")
        await show_sell_stocks(message)
    except Exception as e:
        logging.error(f"خطأ في بيع السهم: {e}")
        await message.reply("❌ حدث خطأ في عملية البيع")

async def show_buy_stocks(message: Message):
    """عرض قائمة الأسهم للشراء"""
    try:
        if not message.from_user:
            await message.reply("❌ خطأ في معرف المستخدم")
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        current_prices = await get_current_stock_prices()
        stocks_text = f"📈 **شراء الأسهم**\n\n💰 رصيدك: {format_number(user['balance'])}$\n\n"
        
        for symbol, info in GAME_STOCKS.items():
            price = current_prices.get(symbol, info['base_price'])
            stocks_text += f"{info['emoji']} **{symbol}** - {info['name']}\n"
            stocks_text += f"   💰 السعر: ${price:.2f}\n"
            stocks_text += f"   📊 الفئة: {info['category']}\n"
            stocks_text += f"   🔹 اكتب: \"شراء سهم {symbol} [العدد]\"\n\n"
        
        stocks_text += "\n📋 **أمثلة:**\n"
        stocks_text += "• شراء سهم AAPL 10\n"
        stocks_text += "• شراء سهم TSLA 5\n"
        stocks_text += "• شراء سهم MSFT 20"
        
        await message.reply(stocks_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض شراء الأسهم: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الشراء")

async def show_sell_stocks(message: Message):
    """عرض قائمة الأسهم للبيع"""
    try:
        if not message.from_user:
            await message.reply("❌ خطأ في معرف المستخدم")
            return
            
        user_stocks = await get_user_stocks(message.from_user.id)
        
        if not user_stocks or not isinstance(user_stocks, list):
            await message.reply("📊 محفظتك فارغة\n\nلا يمكنك بيع أسهم لا تملكها")
            return
        
        current_prices = await get_current_stock_prices()
        stocks_text = "📉 **بيع الأسهم**\n\n"
        
        for stock in user_stocks:
            if not isinstance(stock, dict):
                continue
                
            symbol = stock.get('symbol', '')
            quantity = stock.get('quantity', 0)
            purchase_price = stock.get('purchase_price', 0)
            
            stock_info = GAME_STOCKS.get(symbol, {})
            current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
            profit = (current_price - purchase_price) * quantity
            
            profit_emoji = "📈" if profit >= 0 else "📉"
            
            stocks_text += f"{stock_info.get('emoji', '📊')} **{symbol}** x{quantity}\n"
            stocks_text += f"   💰 السعر الحالي: ${current_price:.2f}\n"
            stocks_text += f"   {profit_emoji} الربح/الخسارة: ${profit:+.2f}\n"
            stocks_text += f"   🔹 اكتب: \"بيع سهم {symbol} [العدد]\"\n\n"
        
        stocks_text += "\n📋 **أمثلة:**\n"
        stocks_text += "• بيع سهم AAPL 5\n"
        stocks_text += "• بيع سهم TSLA 2"
        
        await message.reply(stocks_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض بيع الأسهم: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة البيع")

async def show_stock_prices(message: Message):
    """عرض أسعار الأسهم الحالية"""
    try:
        current_prices = await get_current_stock_prices()
        prices_text = "📊 **أسعار الأسهم الحالية:**\n\n"
        
        for symbol, info in GAME_STOCKS.items():
            current_price = current_prices.get(symbol, info['base_price'])
            base_price = info['base_price']
            
            # حساب التغيير
            change = ((current_price - base_price) / base_price) * 100
            change_emoji = "📈" if change >= 0 else "📉"
            
            prices_text += f"{info['emoji']} **{symbol}** - {info['name']}\n"
            prices_text += f"   💰 السعر: ${current_price:.2f}\n"
            prices_text += f"   📊 الفئة: {info['category']}\n"
            prices_text += f"   {change_emoji} التغيير: {change:+.1f}%\n\n"
        
        prices_text += "\n📋 **للشراء/البيع:**\n"
        prices_text += "• اكتب: \"شراء اسهم\" لعرض قائمة الشراء\n"
        prices_text += "• اكتب: \"بيع اسهم\" لعرض أسهمك للبيع"
        
        await message.reply(prices_text)
    except Exception as e:
        logging.error(f"خطأ في عرض أسعار الأسهم: {e}")
        await message.reply("❌ حدث خطأ في عرض أسعار الأسهم")

async def show_portfolio(message: Message):
    """عرض محفظة الأسهم"""
    try:
        if not message.from_user:
            await message.reply("❌ خطأ في معرف المستخدم")
            return
            
        user_stocks = await get_user_stocks(message.from_user.id)
        
        if not user_stocks or not isinstance(user_stocks, list):
            await message.reply("📊 محفظتك فارغة\n\nابدأ الاستثمار باستخدام 'اسهم'")
            return
            
        current_prices = await get_current_stock_prices()
        portfolio_text = "💼 **محفظة الأسهم:**\n\n"
        total_value = 0
        total_profit = 0
        
        for stock in user_stocks:
            if not isinstance(stock, dict):
                continue
                
            symbol = stock.get('symbol', '')
            quantity = stock.get('quantity', 0)
            purchase_price = stock.get('purchase_price', 0)
            
            stock_info = GAME_STOCKS.get(symbol, {})
            current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
            stock_value = current_price * quantity
            profit = (current_price - purchase_price) * quantity
            
            profit_emoji = "📈" if profit >= 0 else "📉"
            
            portfolio_text += f"{stock_info.get('emoji', '📊')} **{symbol}** x{quantity}\n"
            portfolio_text += f"   💰 السعر الحالي: ${current_price:.2f}\n"
            portfolio_text += f"   💵 القيمة: ${stock_value:.2f}\n"
            portfolio_text += f"   {profit_emoji} الربح/الخسارة: ${profit:+.2f}\n\n"
            
            total_value += stock_value
            total_profit += profit
        
        portfolio_text += f"💎 **إجمالي قيمة المحفظة:** ${total_value:.2f}\n"
        portfolio_text += f"📊 **إجمالي الربح/الخسارة:** ${total_profit:+.2f}"
        
        await message.reply(portfolio_text)
    except Exception as e:
        logging.error(f"خطأ في عرض المحفظة: {e}")
        await message.reply("❌ حدث خطأ في عرض المحفظة")

async def show_stock_prices(message: Message):
    """عرض أسعار الأسهم الحالية"""
    try:
        current_prices = await get_current_stock_prices()
        
        prices_text = "📊 **أسعار السوق الحالية:**\n\n"
        
        for symbol, stock_info in GAME_STOCKS.items():
            current_price = current_prices.get(symbol, stock_info['base_price'])
            change = random.uniform(-5, 5)
            change_emoji = "📈" if change >= 0 else "📉"
            
            prices_text += f"{stock_info['emoji']} **{symbol}** - ${current_price:.2f} "
            prices_text += f"{change_emoji} {change:+.2f}%\n"
        
        prices_text += "\n💡 الأسعار تتحدث كل دقيقة!"
        
        await message.reply(prices_text)
    except Exception as e:
        logging.error(f"خطأ في عرض أسعار الأسهم: {e}")
        await message.reply("❌ حدث خطأ في عرض أسعار الأسهم")


async def show_buy_stocks(message: Message):
    """عرض الأسهم المتاحة للشراء"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        current_prices = await get_current_stock_prices()
        
        keyboard_buttons = []
        for symbol, stock_info in GAME_STOCKS.items():
            current_price = current_prices.get(symbol, stock_info['base_price'])
            affordable = user['balance'] >= current_price
            
            button_text = f"{stock_info['emoji']} {symbol} - ${current_price:.2f}"
            if not affordable:
                button_text = f"❌ {button_text}"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"stocks_buy_{symbol}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        stocks_text = "📈 **الأسهم المتاحة للشراء:**\n\n"
        for symbol, stock_info in GAME_STOCKS.items():
            current_price = current_prices.get(symbol, stock_info['base_price'])
            change = random.uniform(-5, 5)  # تغيير وهمي للعرض
            change_emoji = "📈" if change >= 0 else "📉"
            affordable = "✅" if user['balance'] >= current_price else "❌"
            
            stocks_text += f"{affordable} {stock_info['emoji']} **{symbol}** - {stock_info['name']}\n"
            stocks_text += f"   💰 السعر: ${current_price:.2f}\n"
            stocks_text += f"   {change_emoji} التغيير: {change:+.2f}%\n\n"
        
        stocks_text += f"💰 رصيدك الحالي: {format_number(user['balance'])}$"
        
        await message.reply(stocks_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الأسهم للشراء: {e}")
        await message.reply("❌ حدث خطأ في عرض الأسهم للشراء")


async def show_sell_stocks(message: Message):
    """عرض أسهم المستخدم للبيع"""
    try:
        user_stocks = await get_user_stocks(message.from_user.id)
        
        if not user_stocks:
            await message.reply("❌ لا تملك أي أسهم للبيع\n\nاستخدم /stocks لشراء أسهم")
            return
        
        current_prices = await get_current_stock_prices()
        keyboard_buttons = []
        
        for stock in user_stocks:
            symbol = stock['symbol']
            stock_info = GAME_STOCKS.get(symbol, {})
            current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
            total_value = current_price * stock['quantity']
            
            button_text = f"{stock_info.get('emoji', '📊')} {symbol} x{stock['quantity']} - ${total_value:.2f}"
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"stocks_sell_{symbol}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        stocks_text = "📉 **أسهمك للبيع:**\n\n"
        total_portfolio_value = 0
        
        for stock in user_stocks:
            symbol = stock['symbol']
            stock_info = GAME_STOCKS.get(symbol, {})
            current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
            total_value = current_price * stock['quantity']
            profit_loss = (current_price - stock['purchase_price']) * stock['quantity']
            profit_emoji = "📈" if profit_loss >= 0 else "📉"
            
            stocks_text += f"{stock_info.get('emoji', '📊')} **{symbol}** x{stock['quantity']}\n"
            stocks_text += f"   💰 السعر الحالي: ${current_price:.2f}\n"
            stocks_text += f"   💵 القيمة الإجمالية: ${total_value:.2f}\n"
            stocks_text += f"   {profit_emoji} الربح/الخسارة: ${profit_loss:+.2f}\n\n"
            
            total_portfolio_value += total_value
        
        stocks_text += f"💼 إجمالي قيمة المحفظة: ${total_portfolio_value:.2f}"
        
        await message.reply(stocks_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الأسهم للبيع: {e}")
        await message.reply("❌ حدث خطأ في عرض الأسهم للبيع")


async def start_buy_process(message: Message, symbol: str, state: FSMContext):
    """بدء عملية شراء سهم"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        if symbol not in GAME_STOCKS:
            await message.reply("❌ رمز سهم غير صحيح")
            return
        
        stock_info = GAME_STOCKS[symbol]
        current_prices = await get_current_stock_prices()
        current_price = current_prices.get(symbol, stock_info['base_price'])
        
        if user['balance'] < current_price:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"📊 {symbol} - {stock_info['name']}\n"
                f"💰 السعر الحالي: ${current_price:.2f}\n"
                f"💵 رصيدك: {format_number(user['balance'])}$"
            )
            return
        
        max_affordable = int(user['balance'] // current_price)
        
        await state.update_data(symbol=symbol, price=current_price)
        await state.set_state(StocksStates.waiting_buy_quantity)
        
        await message.reply(
            f"📈 **شراء أسهم {symbol}**\n\n"
            f"{stock_info['emoji']} {stock_info['name']}\n"
            f"💰 السعر الحالي: ${current_price:.2f}\n"
            f"💵 رصيدك: {format_number(user['balance'])}$\n"
            f"📊 أقصى كمية: {max_affordable} سهم\n\n"
            f"كم سهم تريد شراء؟\n"
            f"❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء عملية الشراء: {e}")
        await message.reply("❌ حدث خطأ في عملية الشراء")


async def start_sell_process(message: Message, symbol: str, state: FSMContext):
    """بدء عملية بيع سهم"""
    try:
        user_stocks = await get_user_stocks(message.from_user.id, symbol)
        
        if not user_stocks:
            await message.reply("❌ لا تملك أسهم من هذا النوع")
            return
        
        stock = user_stocks[0]
        stock_info = GAME_STOCKS.get(symbol, {})
        current_prices = await get_current_stock_prices()
        current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
        
        await state.update_data(symbol=symbol, price=current_price, owned_quantity=stock['quantity'])
        await state.set_state(StocksStates.waiting_sell_quantity)
        
        profit_loss = (current_price - stock['purchase_price']) * stock['quantity']
        profit_emoji = "📈" if profit_loss >= 0 else "📉"
        
        await message.reply(
            f"📉 **بيع أسهم {symbol}**\n\n"
            f"{stock_info.get('emoji', '📊')} {stock_info.get('name', symbol)}\n"
            f"💰 السعر الحالي: ${current_price:.2f}\n"
            f"📊 الكمية المملوكة: {stock['quantity']} سهم\n"
            f"💵 سعر الشراء: ${stock['purchase_price']:.2f}\n"
            f"{profit_emoji} الربح/الخسارة المتوقع: ${profit_loss:+.2f}\n\n"
            f"كم سهم تريد بيع؟\n"
            f"💡 اكتب 'الكل' لبيع جميع الأسهم\n"
            f"❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء عملية البيع: {e}")
        await message.reply("❌ حدث خطأ في عملية البيع")


async def process_buy_quantity(message: Message, state: FSMContext):
    """معالجة كمية الشراء"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            await state.clear()
            return
        
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية الشراء")
            return
        
        if not is_valid_amount(text):
            await message.reply("❌ كمية غير صحيحة. يرجى إدخال رقم صحيح")
            return
        
        quantity = int(text)
        
        if quantity <= 0:
            await message.reply("❌ الكمية يجب أن تكون أكبر من صفر")
            return
        
        # الحصول على بيانات السهم
        data = await state.get_data()
        symbol = data['symbol']
        price = data['price']
        total_cost = price * quantity
        
        if total_cost > user['balance']:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"💰 التكلفة الإجمالية: ${total_cost:.2f}\n"
                f"💵 رصيدك الحالي: {format_number(user['balance'])}$"
            )
            return
        
        # تنفيذ عملية الشراء
        new_balance = user['balance'] - total_cost
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة الأسهم إلى محفظة المستخدم
        await add_user_stocks(message.from_user.id, symbol, quantity, price)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=0,  # النظام
            transaction_type="stock_purchase",
            amount=int(total_cost),
            description=f"شراء {quantity} سهم من {symbol}"
        )
        
        stock_info = GAME_STOCKS[symbol]
        
        await message.reply(
            f"✅ **تم الشراء بنجاح!**\n\n"
            f"{stock_info['emoji']} السهم: {symbol}\n"
            f"📊 الكمية: {quantity} سهم\n"
            f"💰 سعر السهم: ${price:.2f}\n"
            f"💵 التكلفة الإجمالية: ${total_cost:.2f}\n"
            f"💰 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"🎉 تم إضافة الأسهم إلى محفظتك!"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة كمية الشراء: {e}")
        await message.reply("❌ حدث خطأ في عملية الشراء")
        await state.clear()


async def process_sell_quantity(message: Message, state: FSMContext):
    """معالجة كمية البيع"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            await state.clear()
            return
        
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية البيع")
            return
        
        # الحصول على بيانات العملية
        data = await state.get_data()
        symbol = data['symbol']
        price = data['price']
        owned_quantity = data['owned_quantity']
        
        # تحديد الكمية
        if text.lower() in ['الكل', 'كل', 'all']:
            quantity = owned_quantity
        else:
            if not is_valid_amount(text):
                await message.reply("❌ كمية غير صحيحة. يرجى إدخال رقم صحيح أو 'الكل'")
                return
            quantity = int(text)
        
        if quantity <= 0:
            await message.reply("❌ الكمية يجب أن تكون أكبر من صفر")
            return
        
        if quantity > owned_quantity:
            await message.reply(f"❌ لا تملك هذه الكمية!\nتملك: {owned_quantity} سهم")
            return
        
        # تنفيذ عملية البيع
        total_revenue = price * quantity
        new_balance = user['balance'] + total_revenue
        await update_user_balance(message.from_user.id, new_balance)
        
        # تحديث أو حذف الأسهم من المحفظة
        await remove_user_stocks(message.from_user.id, symbol, quantity)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=0,  # النظام
            to_user_id=message.from_user.id,
            transaction_type="stock_sale",
            amount=int(total_revenue),
            description=f"بيع {quantity} سهم من {symbol}"
        )
        
        stock_info = GAME_STOCKS[symbol]
        
        await message.reply(
            f"✅ **تم البيع بنجاح!**\n\n"
            f"{stock_info['emoji']} السهم: {symbol}\n"
            f"📊 الكمية: {quantity} سهم\n"
            f"💰 سعر البيع: ${price:.2f}\n"
            f"💵 المبلغ المستلم: ${total_revenue:.2f}\n"
            f"💰 رصيدك الجديد: {format_number(new_balance)}$"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة كمية البيع: {e}")
        await message.reply("❌ حدث خطأ في عملية البيع")
        await state.clear()


async def show_user_portfolio(message: Message):
    """عرض محفظة المستخدم"""
    try:
        user_stocks = await get_user_stocks(message.from_user.id)
        
        if not user_stocks:
            await message.reply("📊 **محفظتك فارغة**\n\nاستخدم /stocks لشراء أسهم")
            return
        
        current_prices = await get_current_stock_prices()
        portfolio_text = "💼 **محفظة الأسهم**\n\n"
        
        total_investment = 0
        total_current_value = 0
        
        for stock in user_stocks:
            symbol = stock['symbol']
            stock_info = GAME_STOCKS.get(symbol, {})
            current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
            
            investment = stock['purchase_price'] * stock['quantity']
            current_value = current_price * stock['quantity']
            profit_loss = current_value - investment
            profit_percentage = (profit_loss / investment) * 100 if investment > 0 else 0
            
            profit_emoji = "📈" if profit_loss >= 0 else "📉"
            
            portfolio_text += f"{stock_info.get('emoji', '📊')} **{symbol}** x{stock['quantity']}\n"
            portfolio_text += f"   💰 سعر الشراء: ${stock['purchase_price']:.2f}\n"
            portfolio_text += f"   💵 السعر الحالي: ${current_price:.2f}\n"
            portfolio_text += f"   📊 الاستثمار: ${investment:.2f}\n"
            portfolio_text += f"   💎 القيمة الحالية: ${current_value:.2f}\n"
            portfolio_text += f"   {profit_emoji} الربح/الخسارة: ${profit_loss:+.2f} ({profit_percentage:+.1f}%)\n\n"
            
            total_investment += investment
            total_current_value += current_value
        
        total_profit_loss = total_current_value - total_investment
        total_profit_percentage = (total_profit_loss / total_investment) * 100 if total_investment > 0 else 0
        total_emoji = "📈" if total_profit_loss >= 0 else "📉"
        
        portfolio_text += f"📊 **ملخص المحفظة:**\n"
        portfolio_text += f"💰 إجمالي الاستثمار: ${total_investment:.2f}\n"
        portfolio_text += f"💎 القيمة الحالية: ${total_current_value:.2f}\n"
        portfolio_text += f"{total_emoji} إجمالي الربح/الخسارة: ${total_profit_loss:+.2f} ({total_profit_percentage:+.1f}%)"
        
        await message.reply(portfolio_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المحفظة: {e}")
        await message.reply("❌ حدث خطأ في عرض المحفظة")


async def get_current_stock_prices():
    """الحصول على أسعار الأسهم الحالية"""
    try:
        # محاولة الحصول على الأسعار الحقيقية من API
        real_prices = await get_stock_prices(list(GAME_STOCKS.keys()))
        
        if real_prices:
            return real_prices
        
        # في حالة فشل API، استخدام أسعار وهمية متقلبة
        current_prices = {}
        for symbol, stock_info in GAME_STOCKS.items():
            base_price = stock_info['base_price']
            volatility = stock_info['volatility']
            # تغيير عشوائي يعتمد على التقلبات
            change_factor = 1 + random.uniform(-volatility, volatility)
            current_prices[symbol] = base_price * change_factor
        
        return current_prices
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على أسعار الأسهم: {e}")
        # إرجاع الأسعار الأساسية في حالة الخطأ
        return {symbol: info['base_price'] for symbol, info in GAME_STOCKS.items()}


async def get_user_stocks(user_id: int, symbol: str = None):
    """الحصول على أسهم المستخدم"""
    try:
        if symbol:
            query = "SELECT * FROM stocks WHERE user_id = ? AND symbol = ?"
            params = (user_id, symbol)
            stocks = await execute_query(query, params, fetch_one=True)
            return stocks if stocks else None
        else:
            query = "SELECT * FROM stocks WHERE user_id = ? ORDER BY id DESC"
            params = (user_id,)
            stocks = await execute_query(query, params, fetch_all=True)
            return stocks if stocks else []
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على أسهم المستخدم: {e}")
        return []


async def add_user_stocks(user_id: int, symbol: str, quantity: int, price: float):
    """إضافة أسهم لمحفظة المستخدم"""
    try:
        # التحقق من وجود أسهم مماثلة
        existing = await execute_query(
            "SELECT * FROM stocks WHERE user_id = ? AND symbol = ?",
            (user_id, symbol),
            fetch_one=True
        )
        
        if existing:
            # تحديث الكمية والسعر المتوسط
            old_quantity = existing['quantity']
            old_price = existing['purchase_price']
            
            new_quantity = old_quantity + quantity
            new_avg_price = ((old_quantity * old_price) + (quantity * price)) / new_quantity
            
            await execute_query(
                "UPDATE stocks SET quantity = ?, purchase_price = ? WHERE user_id = ? AND symbol = ?",
                (new_quantity, new_avg_price, user_id, symbol)
            )
        else:
            # إضافة سهم جديد
            await execute_query(
                "INSERT INTO stocks (user_id, symbol, quantity, purchase_price) VALUES (?, ?, ?, ?)",
                (user_id, symbol, quantity, price)
            )
            
    except Exception as e:
        logging.error(f"خطأ في إضافة الأسهم: {e}")
        raise


async def remove_user_stocks(user_id: int, symbol: str, quantity: int):
    """إزالة أسهم من محفظة المستخدم"""
    try:
        existing = await execute_query(
            "SELECT * FROM stocks WHERE user_id = ? AND symbol = ?",
            (user_id, symbol),
            fetch_one=True
        )
        
        if not existing:
            raise ValueError("لا توجد أسهم للحذف")
        
        new_quantity = existing['quantity'] - quantity
        
        if new_quantity <= 0:
            # حذف السهم بالكامل
            await execute_query(
                "DELETE FROM stocks WHERE user_id = ? AND symbol = ?",
                (user_id, symbol)
            )
        else:
            # تحديث الكمية
            await execute_query(
                "UPDATE stocks SET quantity = ? WHERE user_id = ? AND symbol = ?",
                (new_quantity, user_id, symbol)
            )
            
    except Exception as e:
        logging.error(f"خطأ في إزالة الأسهم: {e}")
        raise


async def calculate_portfolio_value(portfolio):
    """حساب قيمة المحفظة الإجمالية"""
    try:
        if not portfolio:
            return 0
        
        current_prices = await get_current_stock_prices()
        total_value = 0
        
        for stock in portfolio:
            symbol = stock['symbol']
            stock_info = GAME_STOCKS.get(symbol, {})
            current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
            total_value += current_price * stock['quantity']
        
        return total_value
        
    except Exception as e:
        logging.error(f"خطأ في حساب قيمة المحفظة: {e}")
        return 0


# معالج حالة المخزون
async def process_stock_symbol(message: Message, state: FSMContext):
    """معالجة رمز السهم"""
    await message.reply("تم استلام رمز السهم")
    await state.clear()


async def handle_state_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل الأسهم حسب الحالة"""
    try:
        if current_state == "StocksStates:waiting_buy_quantity":
            await handle_buy_quantity(message, state)
        elif current_state == "StocksStates:waiting_sell_quantity":
            await handle_sell_quantity(message, state)
        else:
            await message.reply("❌ حالة غير معروفة")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل الأسهم: {e}")
        await message.reply("❌ حدث خطأ في معالجة الأمر")
        await state.clear()


async def handle_buy_quantity(message: Message, state: FSMContext):
    """معالجة كمية الشراء"""
    try:
        if not message.text or not message.text.isdigit():
            await message.reply("❌ يرجى إدخال رقم صحيح للكمية")
            return
        
        quantity = int(message.text)
        if quantity <= 0:
            await message.reply("❌ يجب أن تكون الكمية أكبر من صفر")
            return
        
        data = await state.get_data()
        symbol = data.get('symbol')
        price = data.get('price')
        
        if not symbol or not price:
            await message.reply("❌ حدث خطأ في البيانات، يرجى المحاولة مرة أخرى")
            await state.clear()
            return
        
        total_cost = price * quantity
        user = await get_user(message.from_user.id)
        
        if user['balance'] < total_cost:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"💰 التكلفة: {format_number(total_cost)}$\n"
                f"💵 رصيدك: {format_number(user['balance'])}$"
            )
            await state.clear()
            return
        
        # تنفيذ عملية الشراء
        await add_user_stocks(message.from_user.id, symbol, quantity, price)
        new_balance = user['balance'] - total_cost
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة معاملة
        await add_transaction(
            message.from_user.id,
            f"شراء {quantity} من أسهم {symbol}",
            -total_cost,
            "stock_buy"
        )
        
        stock_info = GAME_STOCKS.get(symbol, {})
        await message.reply(
            f"✅ **تم شراء الأسهم بنجاح!**\n\n"
            f"{stock_info.get('emoji', '📊')} **{symbol}** x{quantity}\n"
            f"💰 السعر: ${price:.2f}\n"
            f"💵 التكلفة الإجمالية: {format_number(total_cost)}$\n"
            f"🏦 رصيدك الجديد: {format_number(new_balance)}$"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة شراء الأسهم: {e}")
        await message.reply("❌ حدث خطأ أثناء شراء الأسهم")
        await state.clear()


async def handle_sell_quantity(message: Message, state: FSMContext):
    """معالجة كمية البيع"""
    try:
        if not message.text or not message.text.isdigit():
            await message.reply("❌ يرجى إدخال رقم صحيح للكمية")
            return
        
        quantity = int(message.text)
        if quantity <= 0:
            await message.reply("❌ يجب أن تكون الكمية أكبر من صفر")
            return
        
        data = await state.get_data()
        symbol = data.get('symbol')
        
        if not symbol:
            await message.reply("❌ حدث خطأ في البيانات، يرجى المحاولة مرة أخرى")
            await state.clear()
            return
        
        # التحقق من ملكية الأسهم
        user_stock = await get_user_stocks(message.from_user.id, symbol)
        if not user_stock or user_stock['quantity'] < quantity:
            available = user_stock['quantity'] if user_stock else 0
            await message.reply(
                f"❌ كمية غير كافية!\n\n"
                f"📊 المتاح: {available} سهم\n"
                f"📉 المطلوب: {quantity} سهم"
            )
            await state.clear()
            return
        
        # حساب سعر البيع الحالي
        current_prices = await get_current_stock_prices()
        stock_info = GAME_STOCKS.get(symbol, {})
        current_price = current_prices.get(symbol, stock_info.get('base_price', 100))
        
        total_sale = current_price * quantity
        
        # تنفيذ عملية البيع
        await remove_user_stocks(message.from_user.id, symbol, quantity)
        user = await get_user(message.from_user.id)
        new_balance = user['balance'] + total_sale
        await update_user_balance(message.from_user.id, new_balance)
        
        # حساب الربح/الخسارة
        profit_loss = (current_price - user_stock['purchase_price']) * quantity
        profit_emoji = "📈" if profit_loss >= 0 else "📉"
        
        # إضافة معاملة
        await add_transaction(
            message.from_user.id,
            f"بيع {quantity} من أسهم {symbol}",
            total_sale,
            "stock_sell"
        )
        
        await message.reply(
            f"✅ **تم بيع الأسهم بنجاح!**\n\n"
            f"{stock_info.get('emoji', '📊')} **{symbol}** x{quantity}\n"
            f"💰 سعر البيع: ${current_price:.2f}\n"
            f"💵 إجمالي البيع: {format_number(total_sale)}$\n"
            f"{profit_emoji} الربح/الخسارة: {profit_loss:+.2f}$\n"
            f"🏦 رصيدك الجديد: {format_number(new_balance)}$"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة بيع الأسهم: {e}")
        await message.reply("❌ حدث خطأ أثناء بيع الأسهم")
        await state.clear()
