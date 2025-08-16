"""
عميل API للخدمات الخارجية
External API Client Service
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, List
from config.settings import API_SETTINGS


class APIClient:
    """عميل API عام للتفاعل مع الخدمات الخارجية"""
    
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_session(self):
        """الحصول على جلسة HTTP"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """إجراء طلب HTTP عام"""
        try:
            session = await self.get_session()
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.warning(f"API request failed: {response.status} - {url}")
                    return None
        except Exception as e:
            logging.error(f"خطأ في طلب API: {e}")
            return None


class StockAPI:
    """API للحصول على أسعار الأسهم"""
    
    def __init__(self):
        self.api_key = API_SETTINGS.get('stocks_api_key', '')
        self.base_url = "https://api.twelvedata.com/v1"
        self.client = APIClient()
    
    async def get_stock_price(self, symbol: str) -> Optional[float]:
        """الحصول على سعر سهم محدد"""
        try:
            if not self.api_key:
                logging.warning("مفتاح API الأسهم غير متوفر")
                return None
            
            url = f"{self.base_url}/price"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            data = await self.client.make_request('GET', url, params=params)
            
            if data and 'price' in data:
                return float(data['price'])
            
            return None
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على سعر السهم {symbol}: {e}")
            return None
    
    async def get_multiple_stock_prices(self, symbols: List[str]) -> Dict[str, float]:
        """الحصول على أسعار متعددة"""
        try:
            if not self.api_key:
                return {}
            
            # تحديد الرموز بفاصلة
            symbols_str = ','.join(symbols)
            url = f"{self.base_url}/price"
            params = {
                'symbol': symbols_str,
                'apikey': self.api_key
            }
            
            data = await self.client.make_request('GET', url, params=params)
            
            if data:
                prices = {}
                # التعامل مع استجابة متعددة الرموز
                if isinstance(data, dict):
                    for symbol, price_data in data.items():
                        if isinstance(price_data, dict) and 'price' in price_data:
                            prices[symbol] = float(price_data['price'])
                        elif isinstance(price_data, (int, float, str)):
                            prices[symbol] = float(price_data)
                
                return prices
            
            return {}
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على أسعار الأسهم المتعددة: {e}")
            return {}
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """الحصول على معلومات تفصيلية عن سهم"""
        try:
            if not self.api_key:
                return None
            
            url = f"{self.base_url}/quote"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            data = await self.client.make_request('GET', url, params=params)
            return data
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على معلومات السهم {symbol}: {e}")
            return None


class CryptoAPI:
    """API للحصول على أسعار العملات المشفرة"""
    
    def __init__(self):
        self.api_key = API_SETTINGS.get('crypto_api_key', '')
        self.base_url = "https://api.coinmarketcap.com/v1"
        self.client = APIClient()
    
    async def get_crypto_price(self, symbol: str) -> Optional[float]:
        """الحصول على سعر عملة مشفرة"""
        try:
            url = f"{self.base_url}/cryptocurrency/quotes/latest"
            headers = {}
            if self.api_key:
                headers['X-CMC_PRO_API_KEY'] = self.api_key
            
            params = {'symbol': symbol.upper()}
            
            data = await self.client.make_request('GET', url, params=params, headers=headers)
            
            if data and 'data' in data and symbol.upper() in data['data']:
                crypto_data = data['data'][symbol.upper()]
                if 'quote' in crypto_data and 'USD' in crypto_data['quote']:
                    return float(crypto_data['quote']['USD']['price'])
            
            return None
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على سعر العملة المشفرة {symbol}: {e}")
            return None
    
    async def get_top_cryptos(self, limit: int = 10) -> List[Dict]:
        """الحصول على أفضل العملات المشفرة"""
        try:
            url = f"{self.base_url}/cryptocurrency/listings/latest"
            headers = {}
            if self.api_key:
                headers['X-CMC_PRO_API_KEY'] = self.api_key
            
            params = {'limit': limit}
            
            data = await self.client.make_request('GET', url, params=params, headers=headers)
            
            if data and 'data' in data:
                return data['data']
            
            return []
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على أفضل العملات المشفرة: {e}")
            return []


class NewsAPI:
    """API للحصول على الأخبار المالية"""
    
    def __init__(self):
        self.api_key = API_SETTINGS.get('news_api_key', '')
        self.base_url = "https://newsapi.org/v2"
        self.client = APIClient()
    
    async def get_financial_news(self, limit: int = 5) -> List[Dict]:
        """الحصول على الأخبار المالية"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/everything"
            params = {
                'q': 'stocks OR finance OR economy OR investment',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'apiKey': self.api_key
            }
            
            data = await self.client.make_request('GET', url, params=params)
            
            if data and 'articles' in data:
                return data['articles']
            
            return []
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على الأخبار المالية: {e}")
            return []


class ExchangeRateAPI:
    """API للحصول على أسعار صرف العملات"""
    
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.client = APIClient()
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """الحصول على سعر صرف بين عملتين"""
        try:
            url = f"{self.base_url}/{from_currency.upper()}"
            
            data = await self.client.make_request('GET', url)
            
            if data and 'rates' in data and to_currency.upper() in data['rates']:
                return float(data['rates'][to_currency.upper()])
            
            return None
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على سعر الصرف {from_currency}/{to_currency}: {e}")
            return None


# إنشاء كائنات الخدمات
stock_api = StockAPI()
crypto_api = CryptoAPI()
news_api = NewsAPI()
exchange_api = ExchangeRateAPI()


# دوال مساعدة للوصول السريع
async def get_stock_prices(symbols: List[str]) -> Dict[str, float]:
    """الحصول على أسعار الأسهم"""
    try:
        prices = await stock_api.get_multiple_stock_prices(symbols)
        return prices
    except Exception as e:
        logging.error(f"خطأ في الحصول على أسعار الأسهم: {e}")
        return {}


async def get_crypto_prices(symbols: List[str]) -> Dict[str, float]:
    """الحصول على أسعار العملات المشفرة"""
    try:
        prices = {}
        for symbol in symbols:
            price = await crypto_api.get_crypto_price(symbol)
            if price:
                prices[symbol] = price
        return prices
    except Exception as e:
        logging.error(f"خطأ في الحصول على أسعار العملات المشفرة: {e}")
        return {}


async def get_latest_financial_news(count: int = 5) -> List[Dict]:
    """الحصول على آخر الأخبار المالية"""
    try:
        news = await news_api.get_financial_news(count)
        return news
    except Exception as e:
        logging.error(f"خطأ في الحصول على الأخبار المالية: {e}")
        return []


async def convert_currency(amount: float, from_currency: str, to_currency: str) -> Optional[float]:
    """تحويل العملات"""
    try:
        rate = await exchange_api.get_exchange_rate(from_currency, to_currency)
        if rate:
            return amount * rate
        return None
    except Exception as e:
        logging.error(f"خطأ في تحويل العملة: {e}")
        return None


async def test_api_connections():
    """اختبار الاتصال بجميع APIs"""
    try:
        results = {}
        
        # اختبار API الأسهم
        try:
            stock_price = await stock_api.get_stock_price('AAPL')
            results['stocks'] = stock_price is not None
        except:
            results['stocks'] = False
        
        # اختبار API العملات المشفرة
        try:
            crypto_price = await crypto_api.get_crypto_price('BTC')
            results['crypto'] = crypto_price is not None
        except:
            results['crypto'] = False
        
        # اختبار API الأخبار
        try:
            news = await news_api.get_financial_news(1)
            results['news'] = len(news) > 0
        except:
            results['news'] = False
        
        # اختبار API أسعار الصرف
        try:
            rate = await exchange_api.get_exchange_rate('USD', 'EUR')
            results['exchange'] = rate is not None
        except:
            results['exchange'] = False
        
        return results
        
    except Exception as e:
        logging.error(f"خطأ في اختبار الاتصالات: {e}")
        return {}


# إعدادات الكاش للبيانات
CACHE = {
    'stock_prices': {},
    'crypto_prices': {},
    'news': [],
    'last_update': {}
}

CACHE_DURATION = 300  # 5 دقائق


async def get_cached_stock_prices(symbols: List[str]) -> Dict[str, float]:
    """الحصول على أسعار الأسهم مع الكاش"""
    import time
    
    current_time = time.time()
    cache_key = 'stocks'
    
    # التحقق من صحة الكاش
    if (cache_key in CACHE['last_update'] and 
        current_time - CACHE['last_update'][cache_key] < CACHE_DURATION):
        return {symbol: CACHE['stock_prices'].get(symbol) 
                for symbol in symbols 
                if symbol in CACHE['stock_prices']}
    
    # تحديث الكاش
    prices = await get_stock_prices(symbols)
    CACHE['stock_prices'].update(prices)
    CACHE['last_update'][cache_key] = current_time
    
    return prices


async def cleanup_api_connections():
    """تنظيف الاتصالات"""
    try:
        apis = [stock_api.client, crypto_api.client, news_api.client, exchange_api.client]
        
        for api_client in apis:
            if api_client.session and not api_client.session.closed:
                await api_client.session.close()
        
        logging.info("تم تنظيف اتصالات API")
        
    except Exception as e:
        logging.error(f"خطأ في تنظيف الاتصالات: {e}")
