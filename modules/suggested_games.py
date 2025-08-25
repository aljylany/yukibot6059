"""
ملف الألعاب المقترحة للتطوير المستقبلي
Suggested Games for Future Development
"""

SUGGESTED_GAMES = {
    "empire_wars": {
        "name": "🏆 معركة الإمبراطوريات",
        "description": "كل لاعب يبني إمبراطوريته ويحارب الآخرين في معارك يومية",
        "features": [
            "بناء الجيش والاقتصاد",
            "معارك جماعية يومية",
            "نظام تحالفات وخيانات",
            "موارد محدودة ومنافسة شرسة"
        ],
        "complexity": "عالية",
        "development_time": "4-6 أسابيع",
        "priority": "متوسطة"
    },
    
    "battle_arena": {
        "name": "⚔️ ساحة الموت الأخيرة", 
        "description": "معركة البقاء المثيرة مثل PUBG للبوت",
        "features": [
            "10-15 لاعب في ساحة واحدة",
            "تقلص الساحة كل دقيقة",
            "نظام أسلحة وتطوير سريع", 
            "جوائز كبيرة للفائز"
        ],
        "complexity": "متوسطة",
        "development_time": "2-3 أسابيع", 
        "priority": "عالية - جاري التطوير"
    },
    
    "mafia_city": {
        "name": "🕴️ مافيا المدينة",
        "description": "لعبة نفسية بأدوار سرية ومؤامرات",
        "features": [
            "أدوار سرية: مافيا، شرطة، مواطنين",
            "تصويت يومي لإعدام مشتبه",
            "محادثات سرية ومؤامرات",
            "تعتمد على الذكاء والإقناع"
        ],
        "complexity": "عالية", 
        "development_time": "3-4 أسابيع",
        "priority": "متوسطة"
    },
    
    "crazy_race": {
        "name": "🏃‍♂️ السباق المحموم",
        "description": "سباق تفاعلي بعوائق وفخاخ",
        "features": [
            "سباق عبر مراحل مختلفة",
            "عوائق وفخاخ من اللاعبين",
            "نظام تسريع وإبطاء", 
            "مراهنات جانبية"
        ],
        "complexity": "متوسطة",
        "development_time": "2-3 أسابيع",
        "priority": "متوسطة"
    },
    
    "castle_siege": {
        "name": "🏰 حصار القلاع",
        "description": "معارك فرق مقابل فرق استراتيجية",
        "features": [
            "فرق 3 مقابل 3",
            "بناء دفاعات وتخطيط هجمات",
            "موارد محدودة ووقت ضاغط",
            "انتقام وثارات بين الفرق"
        ],
        "complexity": "عالية",
        "development_time": "4-5 أسابيع", 
        "priority": "منخفضة"
    },
    
    "treasure_hunt": {
        "name": "🗺️ صيد الكنوز",
        "description": "لعبة استكشاف وحل الألغاز",
        "features": [
            "خريطة كبيرة للاستكشاف",
            "ألغاز وتحديات ذكية",
            "كنوز مخفية وجوائز",
            "تعاون أو منافسة بين اللاعبين"
        ],
        "complexity": "متوسطة",
        "development_time": "3-4 أسابيع",
        "priority": "متوسطة"
    },
    
    "quiz_master": {
        "name": "🧠 ملك المعرفة",
        "description": "مسابقة معرفية تفاعلية متقدمة",
        "features": [
            "أسئلة في مجالات مختلفة",
            "مستويات صعوبة متدرجة",
            "تحديات سريعة",
            "بطولات أسبوعية"
        ],
        "complexity": "منخفضة",
        "development_time": "1-2 أسبوع",
        "priority": "عالية"
    }
}

def get_suggested_games_list():
    """الحصول على قائمة منسقة بالألعاب المقترحة"""
    games_text = "💡 **الألعاب المقترحة للتطوير**\n\n"
    
    # ترتيب حسب الأولوية
    priority_order = {"عالية": 1, "متوسطة": 2, "منخفضة": 3}
    sorted_games = sorted(SUGGESTED_GAMES.items(), 
                         key=lambda x: priority_order.get(x[1]["priority"].split(" - ")[0], 4))
    
    for game_key, game_info in sorted_games:
        priority_icon = "🔥" if "عالية" in game_info["priority"] else "⭐" if "متوسطة" in game_info["priority"] else "💫"
        
        games_text += f"{priority_icon} **{game_info['name']}**\n"
        games_text += f"📝 {game_info['description']}\n"
        games_text += f"🎯 **المميزات:**\n"
        
        for feature in game_info['features']:
            games_text += f"  • {feature}\n"
            
        games_text += f"⚙️ التعقيد: {game_info['complexity']}\n"
        games_text += f"⏱️ وقت التطوير: {game_info['development_time']}\n"
        games_text += f"🎖️ الأولوية: {game_info['priority']}\n\n"
    
    return games_text

def get_next_priority_game():
    """الحصول على اللعبة التالية حسب الأولوية"""
    high_priority = [game for game in SUGGESTED_GAMES.values() 
                    if "عالية" in game["priority"] and "جاري" not in game["priority"]]
    
    if high_priority:
        return high_priority[0]
    
    medium_priority = [game for game in SUGGESTED_GAMES.values() 
                      if "متوسطة" in game["priority"]]
    
    return medium_priority[0] if medium_priority else None