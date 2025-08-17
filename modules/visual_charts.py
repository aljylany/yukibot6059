"""
وحدة إنشاء المخططات المرئية النصية
Visual Text Charts Generation Module
"""

import math
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta


class TextChartGenerator:
    """مولد المخططات النصية"""
    
    @staticmethod
    def create_horizontal_bar_chart(data: List[Tuple[str, int]], title: str, max_width: int = 25) -> str:
        """إنشاء مخطط أعمدة أفقي"""
        if not data:
            return f"📊 **{title}**\n\n❌ لا توجد بيانات متاحة"
        
        chart = f"📊 **{title}**\n{'═' * (len(title) + 6)}\n\n"
        
        # العثور على أكبر قيمة للتطبيع
        max_value = max(item[1] for item in data)
        max_label_length = max(len(item[0]) for item in data)
        
        for label, value in data:
            # حساب طول الشريط
            if max_value > 0:
                bar_length = int((value / max_value) * max_width)
                percentage = (value / max_value) * 100
            else:
                bar_length = 0
                percentage = 0
            
            # إنشاء الشريط
            filled_bar = "█" * bar_length
            empty_bar = "░" * (max_width - bar_length)
            bar = filled_bar + empty_bar
            
            # تنسيق التسمية
            padded_label = label.ljust(max_label_length)
            
            chart += f"{padded_label} │{bar}│ {value:,} ({percentage:.1f}%)\n"
        
        return chart

    @staticmethod
    def create_line_chart(data: List[Tuple[str, int]], title: str, height: int = 8) -> str:
        """إنشاء مخطط خطي"""
        if not data or len(data) < 2:
            return f"📈 **{title}**\n\n❌ تحتاج لبيانات أكثر لعرض المخطط"
        
        chart = f"📈 **{title}**\n{'═' * (len(title) + 6)}\n\n"
        
        values = [item[1] for item in data]
        labels = [item[0] for item in data]
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return f"📈 **{title}**\n\n📊 جميع القيم متساوية: {max_val}"
        
        # تطبيع القيم إلى ارتفاع المخطط
        normalized_values = []
        for val in values:
            normalized = int(((val - min_val) / (max_val - min_val)) * (height - 1))
            normalized_values.append(normalized)
        
        # إنشاء المخطط من الأعلى للأسفل
        for row in range(height - 1, -1, -1):
            line = ""
            for i, norm_val in enumerate(normalized_values):
                if norm_val >= row:
                    if i > 0 and normalized_values[i-1] >= row:
                        line += "━"
                    else:
                        line += "▲"
                else:
                    line += " "
                
                if i < len(normalized_values) - 1:
                    line += " "
            
            # إضافة مؤشر القيمة على اليمين
            y_value = min_val + (row / (height - 1)) * (max_val - min_val)
            chart += f"{line} │ {int(y_value):,}\n"
        
        # إضافة المحور السيني
        chart += "─" * (len(normalized_values) * 2 - 1) + " └─\n"
        
        # إضافة التسميات
        label_line = ""
        for i, label in enumerate(labels):
            short_label = label[:3] if len(label) > 3 else label
            label_line += short_label
            if i < len(labels) - 1:
                label_line += " "
        
        chart += label_line + "\n"
        
        return chart

    @staticmethod
    def create_pie_chart(data: List[Tuple[str, int]], title: str) -> str:
        """إنشاء مخطط دائري نصي"""
        if not data:
            return f"🥧 **{title}**\n\n❌ لا توجد بيانات متاحة"
        
        chart = f"🥧 **{title}**\n{'═' * (len(title) + 6)}\n\n"
        
        total = sum(item[1] for item in data)
        if total == 0:
            return f"🥧 **{title}**\n\n❌ جميع القيم صفر"
        
        # رموز مختلفة للقطع
        pie_symbols = ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫", "⬛"]
        
        for i, (label, value) in enumerate(data):
            percentage = (value / total) * 100
            symbol = pie_symbols[i % len(pie_symbols)]
            
            # إنشاء شريط مرئي للنسبة
            bar_length = int((percentage / 100) * 20)
            visual_bar = "█" * bar_length + "░" * (20 - bar_length)
            
            chart += f"{symbol} {label}\n"
            chart += f"   │{visual_bar}│ {value:,} ({percentage:.1f}%)\n\n"
        
        return chart

    @staticmethod
    def create_trend_indicator(current: int, previous: int) -> str:
        """إنشاء مؤشر الاتجاه"""
        if previous == 0:
            return "🆕 جديد"
        
        change = current - previous
        percentage_change = (change / previous) * 100
        
        if change > 0:
            return f"📈 +{change:,} (+{percentage_change:.1f}%)"
        elif change < 0:
            return f"📉 {change:,} ({percentage_change:.1f}%)"
        else:
            return "📊 بدون تغيير"

    @staticmethod
    def create_gauge_meter(value: int, max_value: int, title: str, thresholds: Dict[str, int] = None) -> str:
        """إنشاء مقياس دائري"""
        if max_value == 0:
            return f"🔄 **{title}**: غير محدد"
        
        percentage = min((value / max_value) * 100, 100)
        
        # تحديد اللون بناءً على العتبات
        if thresholds:
            if percentage >= thresholds.get('excellent', 90):
                status = "🟢 ممتاز"
            elif percentage >= thresholds.get('good', 70):
                status = "🟡 جيد"
            elif percentage >= thresholds.get('average', 50):
                status = "🟠 متوسط"
            else:
                status = "🔴 ضعيف"
        else:
            status = "📊 عادي"
        
        # إنشاء المقياس الدائري
        filled_segments = int((percentage / 100) * 10)
        gauge = "●" * filled_segments + "○" * (10 - filled_segments)
        
        return f"🔄 **{title}**\n   [{gauge}] {percentage:.1f}% {status}\n   {value:,} / {max_value:,}"

    @staticmethod
    def create_comparison_chart(data1: List[int], data2: List[int], labels: List[str], 
                              title1: str, title2: str, chart_title: str) -> str:
        """إنشاء مخطط مقارنة"""
        if len(data1) != len(data2) or len(data1) != len(labels):
            return "❌ خطأ في بيانات المقارنة"
        
        chart = f"📊 **{chart_title}**\n{'═' * (len(chart_title) + 6)}\n\n"
        chart += f"🔵 {title1} vs 🔴 {title2}\n\n"
        
        max_val = max(max(data1, default=0), max(data2, default=0))
        if max_val == 0:
            return chart + "❌ لا توجد بيانات للمقارنة"
        
        for i, label in enumerate(labels):
            val1 = data1[i] if i < len(data1) else 0
            val2 = data2[i] if i < len(data2) else 0
            
            # حساب أطوال الأشرطة
            bar1_length = int((val1 / max_val) * 15)
            bar2_length = int((val2 / max_val) * 15)
            
            bar1 = "█" * bar1_length + "░" * (15 - bar1_length)
            bar2 = "█" * bar2_length + "░" * (15 - bar2_length)
            
            chart += f"{label}:\n"
            chart += f"  🔵 │{bar1}│ {val1:,}\n"
            chart += f"  🔴 │{bar2}│ {val2:,}\n\n"
        
        return chart

    @staticmethod
    def create_sparkline(values: List[int], title: str = "") -> str:
        """إنشاء خط صغير للاتجاه"""
        if not values or len(values) < 2:
            return "📊 بيانات غير كافية"
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return f"{'📊 ' + title + ': ' if title else ''}{'▬' * len(values)} ({max_val})"
        
        # رموز الخط الصغير
        spark_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        # تطبيع القيم
        normalized = []
        for val in values:
            norm = int(((val - min_val) / (max_val - min_val)) * (len(spark_chars) - 1))
            normalized.append(spark_chars[norm])
        
        sparkline = ''.join(normalized)
        
        # حساب الاتجاه
        if values[-1] > values[0]:
            trend = "📈"
        elif values[-1] < values[0]:
            trend = "📉"
        else:
            trend = "📊"
        
        result = f"{'📊 ' + title + ': ' if title else ''}{sparkline} {trend}"
        return result


class DashboardStats:
    """إحصائيات لوحة التحكم المتقدمة"""
    
    @staticmethod
    def calculate_growth_rate(current: int, previous: int) -> float:
        """حساب معدل النمو"""
        if previous == 0:
            return 0 if current == 0 else 100
        return ((current - previous) / previous) * 100

    @staticmethod
    def calculate_moving_average(values: List[int], period: int = 3) -> List[float]:
        """حساب المتوسط المتحرك"""
        if len(values) < period:
            return [sum(values) / len(values)] * len(values)
        
        moving_avg = []
        for i in range(len(values)):
            if i < period - 1:
                # للعناصر الأولى، استخدم جميع القيم المتاحة
                avg = sum(values[:i+1]) / (i + 1)
            else:
                # للباقي، استخدم النافذة المحددة
                avg = sum(values[i-period+1:i+1]) / period
            moving_avg.append(avg)
        
        return moving_avg

    @staticmethod
    def detect_anomalies(values: List[int], threshold: float = 2.0) -> List[bool]:
        """كشف الشذوذ في البيانات"""
        if len(values) < 3:
            return [False] * len(values)
        
        # حساب المتوسط والانحراف المعياري
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        # تحديد النقاط الشاذة
        anomalies = []
        for value in values:
            z_score = abs(value - mean) / std_dev if std_dev > 0 else 0
            anomalies.append(z_score > threshold)
        
        return anomalies

    @staticmethod
    def calculate_correlation(x: List[int], y: List[int]) -> float:
        """حساب معامل الارتباط"""
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
        
        if denominator == 0:
            return 0
        
        return numerator / denominator

    @staticmethod
    def get_performance_grade(score: float, thresholds: Dict[str, float] = None) -> Tuple[str, str]:
        """تحديد درجة الأداء"""
        if thresholds is None:
            thresholds = {
                'A+': 95, 'A': 90, 'A-': 85,
                'B+': 80, 'B': 75, 'B-': 70,
                'C+': 65, 'C': 60, 'C-': 55,
                'D': 50
            }
        
        for grade, threshold in thresholds.items():
            if score >= threshold:
                return grade, "🟢" if grade.startswith('A') else "🟡" if grade.startswith('B') else "🟠" if grade.startswith('C') else "🔴"
        
        return 'F', "🔴"