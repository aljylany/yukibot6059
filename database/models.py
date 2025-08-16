"""
نماذج قاعدة البيانات
Database Models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class User:
    """نموذج المستخدم"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    balance: int = 1000
    bank_balance: int = 0
    last_daily: Optional[str] = None
    security_level: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'balance': self.balance,
            'bank_balance': self.bank_balance,
            'last_daily': self.last_daily,
            'security_level': self.security_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """إنشاء من قاموس"""
        return cls(
            user_id=data['user_id'],
            username=data.get('username'),
            first_name=data.get('first_name'),
            balance=data.get('balance', 1000),
            bank_balance=data.get('bank_balance', 0),
            last_daily=data.get('last_daily'),
            security_level=data.get('security_level', 1),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            last_active=datetime.fromisoformat(data['last_active']) if data.get('last_active') else None
        )


@dataclass
class Property:
    """نموذج العقار"""
    id: Optional[int] = None
    user_id: int = 0
    property_type: str = ""
    location: str = ""
    price: int = 0
    income_per_hour: int = 0
    purchased_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'property_type': self.property_type,
            'location': self.location,
            'price': self.price,
            'income_per_hour': self.income_per_hour,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None
        }


@dataclass
class Investment:
    """نموذج الاستثمار"""
    id: Optional[int] = None
    user_id: int = 0
    investment_type: str = ""
    amount: int = 0
    expected_return: float = 0.0
    maturity_date: Optional[datetime] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'investment_type': self.investment_type,
            'amount': self.amount,
            'expected_return': self.expected_return,
            'maturity_date': self.maturity_date.isoformat() if self.maturity_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Stock:
    """نموذج السهم"""
    id: Optional[int] = None
    user_id: int = 0
    symbol: str = ""
    quantity: int = 0
    purchase_price: float = 0.0
    purchased_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'purchase_price': self.purchase_price,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None
        }


@dataclass
class Farm:
    """نموذج المزرعة"""
    id: Optional[int] = None
    user_id: int = 0
    crop_type: str = ""
    quantity: int = 0
    planted_at: Optional[datetime] = None
    harvest_time: Optional[datetime] = None
    status: str = "growing"
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'crop_type': self.crop_type,
            'quantity': self.quantity,
            'planted_at': self.planted_at.isoformat() if self.planted_at else None,
            'harvest_time': self.harvest_time.isoformat() if self.harvest_time else None,
            'status': self.status
        }


@dataclass
class Castle:
    """نموذج القلعة"""
    user_id: int = 0
    level: int = 1
    defense_points: int = 100
    attack_points: int = 50
    gold_production: int = 10
    last_upgrade: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'user_id': self.user_id,
            'level': self.level,
            'defense_points': self.defense_points,
            'attack_points': self.attack_points,
            'gold_production': self.gold_production,
            'last_upgrade': self.last_upgrade.isoformat() if self.last_upgrade else None
        }


@dataclass
class Transaction:
    """نموذج المعاملة"""
    id: Optional[int] = None
    from_user_id: Optional[int] = None
    to_user_id: Optional[int] = None
    transaction_type: str = ""
    amount: int = 0
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Stats:
    """نموذج الإحصائيات"""
    id: Optional[int] = None
    user_id: int = 0
    action_type: str = ""
    action_data: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'action_data': self.action_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class BannedUser:
    """نموذج المستخدم المحظور"""
    user_id: int = 0
    banned_by: int = 0
    banned_at: Optional[datetime] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'user_id': self.user_id,
            'banned_by': self.banned_by,
            'banned_at': self.banned_at.isoformat() if self.banned_at else None,
            'reason': self.reason
        }


@dataclass
class CastleBuilding:
    """نموذج مباني القلعة"""
    id: Optional[int] = None
    user_id: int = 0
    building_type: str = ""
    level: int = 1
    upgraded_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'building_type': self.building_type,
            'level': self.level,
            'upgraded_at': self.upgraded_at.isoformat() if self.upgraded_at else None
        }


@dataclass
class GameSession:
    """نموذج جلسة اللعب"""
    id: Optional[int] = None
    user_id: int = 0
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    actions_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'session_end': self.session_end.isoformat() if self.session_end else None,
            'actions_count': self.actions_count
        }


# دوال مساعدة للنماذج

def create_user_from_telegram(telegram_user) -> User:
    """إنشاء مستخدم من كائن Telegram User"""
    return User(
        user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_active=datetime.now()
    )


def validate_user_data(user_data: Dict[str, Any]) -> bool:
    """التحقق من صحة بيانات المستخدم"""
    required_fields = ['user_id']
    return all(field in user_data for field in required_fields)


def sanitize_user_input(text: str) -> str:
    """تنظيف إدخال المستخدم"""
    if not text:
        return ""
    
    # إزالة الأحرف الخطيرة
    dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # تحديد الطول الأقصى
    return text[:1000] if len(text) > 1000 else text


def format_currency_amount(amount: int) -> str:
    """تنسيق مبلغ العملة"""
    return f"{amount:,}$"


def calculate_level_from_experience(experience: int) -> int:
    """حساب المستوى من الخبرة"""
    if experience < 100:
        return 1
    elif experience < 500:
        return 2
    elif experience < 1500:
        return 3
    elif experience < 5000:
        return 4
    elif experience < 15000:
        return 5
    else:
        return min(100, 5 + (experience - 15000) // 10000)


def get_level_requirements(level: int) -> int:
    """الحصول على متطلبات الخبرة للمستوى"""
    level_requirements = {
        1: 0, 2: 100, 3: 500, 4: 1500, 5: 5000
    }
    
    if level <= 5:
        return level_requirements.get(level, 0)
    else:
        return 15000 + (level - 5) * 10000


# ثوابت النماذج

class TransactionTypes:
    """أنواع المعاملات"""
    DAILY_BONUS = "daily_bonus"
    TRANSFER = "transfer"
    BANK_DEPOSIT = "bank_deposit"
    BANK_WITHDRAW = "bank_withdraw"
    PROPERTY_PURCHASE = "property_purchase"
    PROPERTY_SALE = "property_sale"
    STOCK_PURCHASE = "stock_purchase"
    STOCK_SALE = "stock_sale"
    INVESTMENT = "investment"
    INVESTMENT_RETURN = "investment_return"
    THEFT_SUCCESS = "theft_success"
    THEFT_FAILED = "theft_failed"
    CROP_PURCHASE = "crop_purchase"
    CROP_HARVEST = "crop_harvest"
    CASTLE_UPGRADE = "castle_upgrade"
    CASTLE_RAID_SUCCESS = "castle_raid_success"
    CASTLE_GOLD_PRODUCTION = "castle_gold_production"
    PAYMENT_PURCHASE = "payment_purchase"


class PropertyTypes:
    """أنواع العقارات"""
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    BUILDING = "building"
    MALL = "mall"
    SKYSCRAPER = "skyscraper"


class InvestmentTypes:
    """أنواع الاستثمارات"""
    SAVINGS = "savings"
    BONDS = "bonds"
    MUTUAL_FUNDS = "mutual_funds"
    REAL_ESTATE = "real_estate"
    HIGH_YIELD = "high_yield"


class CropTypes:
    """أنواع المحاصيل"""
    WHEAT = "wheat"
    CORN = "corn"
    TOMATO = "tomato"
    POTATO = "potato"
    CARROT = "carrot"
    STRAWBERRY = "strawberry"


class BuildingTypes:
    """أنواع مباني القلعة"""
    MAIN_HALL = "main_hall"
    BARRACKS = "barracks"
    TREASURY = "treasury"
    WALLS = "walls"
    TOWER = "tower"
    MARKET = "market"


class ActionTypes:
    """أنواع الإجراءات للإحصائيات"""
    LOGIN = "login"
    COMMAND_USED = "command_used"
    GAME_ACTION = "game_action"
    PURCHASE = "purchase"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    LEVEL_UP = "level_up"


# دوال التحقق

def is_valid_transaction_type(transaction_type: str) -> bool:
    """التحقق من صحة نوع المعاملة"""
    return hasattr(TransactionTypes, transaction_type.upper())


def is_valid_property_type(property_type: str) -> bool:
    """التحقق من صحة نوع العقار"""
    return hasattr(PropertyTypes, property_type.upper())


def is_valid_investment_type(investment_type: str) -> bool:
    """التحقق من صحة نوع الاستثمار"""
    return hasattr(InvestmentTypes, investment_type.upper())


def is_valid_crop_type(crop_type: str) -> bool:
    """التحقق من صحة نوع المحصول"""
    return hasattr(CropTypes, crop_type.upper())


def is_valid_building_type(building_type: str) -> bool:
    """التحقق من صحة نوع المبنى"""
    return hasattr(BuildingTypes, building_type.upper())
