#!/usr/bin/env python3
"""
اختبار شامل لنظام كشف المحتوى
يختبر جميع أنواع الفحص ويعرض النتائج بالتفصيل
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# إعداد المسار
sys.path.append('.')

# تفعيل التسجيل المفصل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('content_filter_test.log', encoding='utf-8')
    ]
)

# استيراد النظم
from modules.comprehensive_content_filter import comprehensive_filter, ViolationType, SeverityLevel, PunishmentAction
from modules.profanity_filter import check_message_advanced

class ContentFilterTester:
    """اختبار نظام كشف المحتوى"""
    
    def __init__(self):
        self.results = {
            'text_tests': [],
            'profanity_tests': [],
            'system_status': {},
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0
        }
    
    async def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        print("🚀 بدء اختبار نظام كشف المحتوى الشامل")
        print("=" * 60)
        
        # فحص حالة النظام
        await self.check_system_status()
        
        # اختبار فحص النصوص
        await self.test_text_filtering()
        
        # اختبار نظام السباب
        await self.test_profanity_detection()
        
        # اختبار نظام النقاط والعقوبات
        await self.test_punishment_system()
        
        # عرض النتائج النهائية
        self.display_final_results()
    
    async def check_system_status(self):
        """فحص حالة النظام"""
        print("\n🔍 فحص حالة النظام...")
        
        # فحص النظام الشامل
        filter_enabled = comprehensive_filter.enabled
        has_api_keys = len(comprehensive_filter.api_keys) > 0
        has_model = comprehensive_filter.model is not None
        
        self.results['system_status'] = {
            'comprehensive_filter_enabled': filter_enabled,
            'api_keys_loaded': has_api_keys,
            'ai_model_ready': has_model,
            'api_keys_count': len(comprehensive_filter.api_keys)
        }
        
        print(f"✅ النظام الشامل: {'مفعل' if filter_enabled else 'معطل'}")
        print(f"🔑 مفاتيح API: {len(comprehensive_filter.api_keys)} مفتاح")
        print(f"🧠 نموذج AI: {'جاهز' if has_model else 'غير متوفر'}")
        
        if not filter_enabled:
            print("⚠️ تحذير: النظام الشامل معطل!")
    
    async def test_text_filtering(self):
        """اختبار فحص النصوص"""
        print("\n📝 اختبار فحص النصوص...")
        
        test_texts = [
            # نصوص نظيفة
            {"text": "مرحبا كيف الحال", "expected": False, "type": "clean"},
            {"text": "أهلا وسهلا بك في المجموعة", "expected": False, "type": "clean"},
            
            # نصوص تحتوي على سباب
            {"text": "أنت شرموط", "expected": True, "type": "profanity"},
            {"text": "ش ر م و ط", "expected": True, "type": "profanity_spaced"},
            {"text": "ش*ر*م*و*ط", "expected": True, "type": "profanity_symbols"},
            {"text": "شرم0ط", "expected": True, "type": "profanity_numbers"},
            
            # محتوى جنسي
            {"text": "أريد ممارسة الجنس", "expected": True, "type": "sexual"},
            {"text": "صور عارية", "expected": True, "type": "sexual"},
            {"text": "محتوى إباحي", "expected": True, "type": "sexual"},
            
            # كلمات حدية (قد تكون مقبولة أو لا)
            {"text": "هذا غباء", "expected": False, "type": "borderline"},
            {"text": "أنت مجنون", "expected": False, "type": "borderline"},
        ]
        
        for i, test_case in enumerate(test_texts):
            print(f"\n--- اختبار {i+1}: {test_case['type']} ---")
            print(f"النص: '{test_case['text']}'")
            
            try:
                # اختبار النظام الشامل
                result = await comprehensive_filter._check_text_content(test_case['text'])
                
                has_violation = result['has_violation']
                violation_type = result.get('violation_type')
                severity = result.get('severity', 0)
                
                print(f"🔍 النتيجة: {'مخالفة' if has_violation else 'نظيف'}")
                if has_violation:
                    print(f"📋 نوع المخالفة: {violation_type}")
                    print(f"⚡ مستوى الخطورة: {severity}")
                    if 'details' in result:
                        print(f"📝 التفاصيل: {result['details']}")
                
                # تسجيل النتيجة
                test_result = {
                    'text': test_case['text'],
                    'expected': test_case['expected'],
                    'actual': has_violation,
                    'correct': has_violation == test_case['expected'],
                    'violation_type': violation_type,
                    'severity': severity,
                    'test_type': test_case['type']
                }
                
                self.results['text_tests'].append(test_result)
                self.results['total_tests'] += 1
                
                if test_result['correct']:
                    self.results['passed_tests'] += 1
                    print("✅ النتيجة صحيحة")
                else:
                    self.results['failed_tests'] += 1
                    print("❌ النتيجة خاطئة")
                
            except Exception as e:
                print(f"❌ خطأ في الاختبار: {e}")
                self.results['failed_tests'] += 1
                self.results['total_tests'] += 1
    
    async def test_profanity_detection(self):
        """اختبار نظام كشف السباب المتقدم"""
        print("\n🚫 اختبار نظام كشف السباب المتقدم...")
        
        profanity_tests = [
            # سباب واضح
            {"text": "كسك", "expected": True},
            {"text": "زبك", "expected": True},
            {"text": "شرموطة", "expected": True},
            
            # سباب مموه
            {"text": "ك س ك", "expected": True},
            {"text": "ك*س*ك", "expected": True},
            {"text": "ك5ك", "expected": True},
            
            # كلمات عادية
            {"text": "كاس ماء", "expected": False},
            {"text": "زبدة", "expected": False},
            {"text": "شرح موضوع", "expected": False},
        ]
        
        for i, test_case in enumerate(profanity_tests):
            print(f"\n--- اختبار سباب {i+1} ---")
            print(f"النص: '{test_case['text']}'")
            
            try:
                result = check_message_advanced(test_case['text'])
                
                has_profanity = result['is_abusive']
                method = result.get('method', 'unknown')
                severity = result.get('severity', 0)
                words = result.get('words', [])
                
                print(f"🔍 النتيجة: {'سباب' if has_profanity else 'نظيف'}")
                print(f"📊 الطريقة: {method}")
                if has_profanity:
                    print(f"⚡ مستوى الخطورة: {severity}")
                    print(f"📝 الكلمات المكتشفة: {words}")
                
                test_result = {
                    'text': test_case['text'],
                    'expected': test_case['expected'],
                    'actual': has_profanity,
                    'correct': has_profanity == test_case['expected'],
                    'method': method,
                    'severity': severity,
                    'detected_words': words
                }
                
                self.results['profanity_tests'].append(test_result)
                self.results['total_tests'] += 1
                
                if test_result['correct']:
                    self.results['passed_tests'] += 1
                    print("✅ النتيجة صحيحة")
                else:
                    self.results['failed_tests'] += 1
                    print("❌ النتيجة خاطئة")
                
            except Exception as e:
                print(f"❌ خطأ في اختبار السباب: {e}")
                self.results['failed_tests'] += 1
                self.results['total_tests'] += 1
    
    async def test_punishment_system(self):
        """اختبار نظام العقوبات"""
        print("\n⚖️ اختبار نظام تحديد العقوبات...")
        
        # محاكاة نقاط مختلفة
        test_points = [
            {"points": 1, "expected": PunishmentAction.WARNING},
            {"points": 3, "expected": PunishmentAction.MUTE_5MIN},
            {"points": 5, "expected": PunishmentAction.MUTE_30MIN},
            {"points": 8, "expected": PunishmentAction.MUTE_1HOUR},
            {"points": 12, "expected": PunishmentAction.MUTE_6HOUR},
            {"points": 16, "expected": PunishmentAction.MUTE_24HOUR},
            {"points": 20, "expected": PunishmentAction.MUTE_PERMANENT},
            {"points": 25, "expected": PunishmentAction.BAN_PERMANENT},
        ]
        
        for test_case in test_points:
            points = test_case['points']
            expected = test_case['expected']
            
            # محاكاة تحديد العقوبة
            try:
                action = comprehensive_filter._determine_punishment_action(
                    points, 12345, -123456  # مستخدم ومجموعة وهمية
                )
                
                correct = action == expected
                print(f"نقاط: {points} | متوقع: {expected.value} | فعلي: {action.value} | {'✅' if correct else '❌'}")
                
                if correct:
                    self.results['passed_tests'] += 1
                else:
                    self.results['failed_tests'] += 1
                    
                self.results['total_tests'] += 1
                
            except Exception as e:
                print(f"❌ خطأ في اختبار العقوبة للنقاط {points}: {e}")
                self.results['failed_tests'] += 1
                self.results['total_tests'] += 1
    
    def display_final_results(self):
        """عرض النتائج النهائية"""
        print("\n" + "=" * 60)
        print("📊 النتائج النهائية")
        print("=" * 60)
        
        total = self.results['total_tests']
        passed = self.results['passed_tests']
        failed = self.results['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 إجمالي الاختبارات: {total}")
        print(f"✅ نجحت: {passed}")
        print(f"❌ فشلت: {failed}")
        print(f"📊 معدل النجاح: {success_rate:.1f}%")
        
        # تفاصيل النظام
        print(f"\n🔧 حالة النظام:")
        status = self.results['system_status']
        print(f"  - النظام الشامل: {'مفعل' if status.get('comprehensive_filter_enabled') else 'معطل'}")
        print(f"  - مفاتيح API: {status.get('api_keys_count', 0)}")
        print(f"  - نموذج AI: {'جاهز' if status.get('ai_model_ready') else 'غير متوفر'}")
        
        # اختبارات فشلت
        if failed > 0:
            print(f"\n❌ الاختبارات التي فشلت:")
            for test in self.results['text_tests']:
                if not test['correct']:
                    print(f"  - '{test['text']}' (متوقع: {test['expected']}, فعلي: {test['actual']})")
            
            for test in self.results['profanity_tests']:
                if not test['correct']:
                    print(f"  - '{test['text']}' (متوقع: {test['expected']}, فعلي: {test['actual']})")
        
        # حفظ النتائج
        self.save_results()
        
        if success_rate >= 90:
            print(f"\n🎉 النظام يعمل بكفاءة عالية!")
        elif success_rate >= 70:
            print(f"\n⚠️ النظام يعمل بكفاءة متوسطة، يحتاج تحسينات")
        else:
            print(f"\n🚨 النظام يحتاج إصلاحات فورية!")
    
    def save_results(self):
        """حفظ النتائج في ملف"""
        import json
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        try:
            # تحويل العقوبات إلى نصوص للحفظ
            results_copy = self.results.copy()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_copy, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 تم حفظ النتائج في: {filename}")
            
        except Exception as e:
            print(f"❌ خطأ في حفظ النتائج: {e}")

async def main():
    """الدالة الرئيسية"""
    tester = ContentFilterTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())