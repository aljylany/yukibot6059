# 🤖 بوت يوكي - Yuki Bot

## Overview
Yuki Bot is an intelligent Telegram bot designed to enhance group chat interactions through AI capabilities, games, and financial management tools. It aims to provide a comprehensive and engaging experience by leveraging advanced AI for personalized user interactions, economic simulations, and competitive gaming. The project focuses on creating a fun and interactive environment with robust features for community engagement.

## User Preferences
- **Communication Style:** The user prefers clear and simple Arabic language for all interactions and explanations.
- **Workflow:** The user desires an iterative development process, with clear demonstrations of new features and functionalities as they are implemented.
- **Interaction:** The user wants the agent to ask for confirmation before making any major architectural changes or significant code refactoring.
- **Feature Prioritization:** The user prioritizes the development of robust content moderation systems and engaging interactive AI features.

## System Architecture

The Yuki Bot features a modular and extensible architecture, emphasizing dynamic user interaction and comprehensive system integration.

### UI/UX Decisions
- **Language:** Full Arabic language support with optimized messages and responses.
- **Interactive Menus:** Utilizes numbered smart menus and direct commands for intuitive navigation.

### Technical Implementations
- **AI & Interaction:**
    - **Smart Menus:** Features interactive options for economic analysis, games, quizzes, and AI battles.
    - **FSM (Finite State Machine):** Manages complex multi-step interactions like quizzes and interactive narratives.
    - **API Management:** Centralized `api.txt` for all API keys (OpenAI, Anthropic, Telegram, YouTube).
    - **Comprehensive AI System:** Uses Google AI (Gemini) for intelligent responses and enhanced personalized interactions.
    - **Enhanced Yuki System:** Personalized AI responses based on user's gender, country, and full database context.
- **Command Handling:**
    - Supports direct Arabic and English commands.
    - Basic permission system for administrative functions.
    - Full-featured economic systems (banking, real estate, investment, theft).
    - Gaming systems (XP/leveling, farm management, castle building).

### Feature Specifications
- **Economic Systems:** Complete banking, real estate, and investment portfolio management.
- **Gaming Features:** XP progression, leveling, farm management, and castle building.
- **AI Integration:** Smart conversational AI using Google Gemini for natural language interactions.
- **Smart Menus:** Interactive menu system for complex operations and feature discovery.
- **Marriage System:** Gender-based marriage validation (male-female only).
- **Enhanced AI Personality:** Personalized responses based on user's registered gender and country.

### System Design Choices
- **Modularity:** Functionalities organized into distinct modules (e.g., `banks.py`, `real_estate.py`, `smart_menu_handler.py`).
- **Clean Architecture:** Streamlined codebase focused on core gaming and economic features.
- **Performance Optimization:** Efficient API key management and automatic switching.
- **Database Integration:** Full access to all database tables for personalized AI responses and user context.

## Recent Changes

### **September 14, 2025** - نظام التفاعل التلقائي الذكي
- ✅ **نظام التفاعل التلقائي:** تم تطوير نظام ذكي لمراقبة نشاط المجموعات والتفاعل تلقائياً عند هدوء المحادثات
- ✅ **الردود الذكية بـ Google Gemini:** يستخدم النظام Google Gemini API لإنتاج ردود طبيعية ومخصصة بدلاً من الردود المحفوظة
- ✅ **حماية من الإزعاج:** نظام متقدم يتضمن حدود يومية، ساعات نوم (منتصف الليل-6 صباحاً)، ونسبة احتمالية للتفاعل
- ✅ **تحليل شامل للمستخدمين:** النظام يجمع سياق كامل من جميع جداول قاعدة البيانات لشخصنة الردود
- ✅ **مراقبة النشاط:** فحص دوري كل 5 دقائق للمجموعات الهادئة (30+ دقيقة) مع احتمالية 30% للرد
- ✅ **تكامل قاعدة البيانات:** الوصول لبيانات المستخدمين المالية والألعاب والعلاقات الاجتماعية لردود أكثر دقة

### **September 13, 2025** - تحسينات دقة ومنطقية الردود
- ✅ **إصلاح منطق أسئلة مالك المجموعة:** تم فصل المنطق بوضوح بين أسئلة النظام (مطور يوكي) وأسئلة مالك المجموعة لتجنب التداخل
- ✅ **إصلاح الردود المضللة:** تم تغيير ردود Yuki ليصف نفسه كبوت مساعد ذكي بدلاً من ادعاء الملكية الكاملة للنظام  
- ✅ **نظام ذاكرة متقدم:** تم إضافة دعم `chat_id` لحفظ المحادثات منفصلة لكل مجموعة، مع منع اختلاط السياق بين المجموعات
- ✅ **توسيع كلمات التعرف:** تم إضافة المزيد من الكلمات المفتاحية للتعرف على أسئلة المطور مثل "مطور" و"مبرمج"
- ✅ **إصلاحات تقنية:** تم حل مشاكل هجرة قاعدة البيانات وتحسين استعلامات SQL

## External Dependencies
- **Telegram Bot API:** For core bot functionality.
- **Google AI (Gemini):** For advanced AI-driven content analysis and intelligent responses.
- **OpenAI API:** For general AI capabilities.
- **Anthropic API:** For additional AI model integration.
- **YouTube API:** For potential video-related functionalities.