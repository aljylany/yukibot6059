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

## External Dependencies
- **Telegram Bot API:** For core bot functionality.
- **Google AI (Gemini):** For advanced AI-driven content analysis and intelligent responses.
- **OpenAI API:** For general AI capabilities.
- **Anthropic API:** For additional AI model integration.
- **YouTube API:** For potential video-related functionalities.