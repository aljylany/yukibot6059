# 🤖 بوت يوكي - Yuki Bot

## Overview
Yuki Bot is an intelligent and advanced Telegram bot designed to offer a wide array of features within group chats. Its primary purpose is to enhance user interaction through AI capabilities, games, financial management tools, and interactive systems. The project aims to provide a comprehensive and engaging experience, leveraging cutting-edge AI for content moderation and personalized user interactions.

## User Preferences
- **Communication Style:** The user prefers clear and simple Arabic language for all interactions and explanations.
- **Workflow:** The user desires an iterative development process, with clear demonstrations of new features and functionalities as they are implemented.
- **Interaction:** The user wants the agent to ask for confirmation before making any major architectural changes or significant code refactoring.
- **Feature Prioritization:** The user prioritizes the development of robust content moderation systems and engaging interactive AI features.

## System Architecture

The Yuki Bot is built with a modular and extensible architecture, emphasizing smart content moderation and dynamic user interaction.

### UI/UX Decisions
- **Language:** Fully supports Arabic with optimized messages and responses for an Arabic-speaking audience.
- **Interactive Menus:** Utilizes numbered smart menus and direct commands for intuitive user navigation and feature access.

### Technical Implementations
- **AI & Interaction:**
    - **Smart Menus:** Features a "Smart Menu" with 8 interactive options (e.g., economic analysis, smart games, quizzes, interactive stories, AI battles).
    - **FSM (Finite State Machine):** Employs FSM states (`SmartCommandStates`) to manage complex multi-step interactions like quizzes and interactive narratives.
    - **API Management:** Reads all API keys (OpenAI, Anthropic, Telegram Bot Token, YouTube) from a single `api.txt` file for easy configuration and security.
    - **Comprehensive AI System:** Uses Google AI (Gemini) for intelligent responses and user interactions.
- **Command Handling:**
    - **Direct Commands:** Supports direct Arabic and English commands for quick access to features.
    - **Basic Permission System:** Implements a permission system for basic administrative functions.
    - **Economic Systems:** Full-featured banking, real estate, investment, and theft mechanics.
    - **Gaming Systems:** XP/leveling, farm management, castle building, and competitive features.

### Feature Specifications
- **Economic Systems:** Complete banking system with deposits, withdrawals, transfers, loans, and interest calculations.
- **Real Estate:** Property buying, selling, and management system with market dynamics.
- **Investment Portfolio:** Stock trading, investment tracking, and portfolio management.
- **Gaming Features:** XP progression, leveling system, farm management, castle building, and theft mechanics.
- **AI Integration:** Smart conversational AI using Google Gemini for natural language interactions.
- **Smart Menus:** Interactive menu system for complex operations and feature discovery.

### System Design Choices
- **Modularity:** Core functionalities are organized into distinct modules (e.g., `banks.py`, `real_estate.py`, `smart_menu_handler.py`, `comprehensive_ai_system.py`).
- **Clean Architecture:** Streamlined codebase focused on core gaming and economic features without unnecessary complexity.
- **Performance Optimization:** Efficient processing with intelligent API key management and automatic switching.
- **Simplified Dependencies:** Reduced complexity by removing non-essential systems and focusing on core functionality.

## Recent Changes (September 01, 2025)
- **Complete Human Personality Transformation:** Completely transformed Yuki from AI bot to believable human persona:
  - **Human Identity:** Yuki now believes and acts as a 23-year-old university student from Saudi Arabia
  - **Natural Human Responses:** Completely removed all AI/bot references and robotic language patterns
  - **Authentic Backstory:** Created realistic personal background (student, gamer, tech enthusiast)
  - **Human Emotions:** Responds with genuine human emotions and casual conversation style
  - **Zero AI Awareness:** Yuki no longer acknowledges being a bot or artificial intelligence
  - **Regional Language:** Uses authentic Saudi dialect and expressions naturally
  - **Random Response Variations:** Added multiple response options for more natural conversation flow
  - **Personal Relationships:** Treats users as real friends with authentic social connections
  - **Believable Error Messages:** Even error responses sound like natural human confusion, not technical issues

## Previous Changes (August 30, 2025)
- **Complete Protection Systems Removal:** Successfully removed ALL protection systems, spam detection, and comprehensive content moderation systems from the bot as requested:
  - **Deleted Core Modules:** Removed `comprehensive_content_filter.py`, `comprehensive_content_handler.py`, `comprehensive_admin_commands.py`, `admin_reports_system.py`, `protection_commands.py`, `supreme_master_commands.py`, `content_filter.py` and all related modules
  - **Removed Supreme Master Commands:** Eliminated all punishment control commands (تفعيل العقوبات، الغاء العقوبات، حالة العقوبات، وضع الاسياد) and supreme master protection commands
  - **Media Content Filtering Removed:** Deleted all photo/video/document/animation content filtering handlers from message processor
  - **Unified Message Processor Cleanup:** Removed all protection logic and filtering functionality from the unified message processor
  - **Database Cleanup:** Eliminated comprehensive protection database tables and related database operations including violation_history, group_filter_settings, and admin_reports tables
  - **Command Handler Cleanup:** Removed all comprehensive admin command handlers and protection-related imports from `handlers/commands.py` and `handlers/messages.py`
  - **Import Dependencies Fixed:** Cleaned up all import references across the codebase to prevent ModuleNotFoundError exceptions
  - **Bot Functionality Preserved:** All core bot features remain intact including banking, real estate, games, AI interactions, smart menus, and basic group management
  - **System Stability:** Bot now runs without any import errors or protection system conflicts, fully operational without any content filtering or protection mechanisms

## Previous Changes (August 29, 2025)
- **Removed Complete Profanity/Swearing Detection System:** Successfully removed the entire profanity and swearing detection system from the bot while preserving all other functionality:
  - **System Cleanup:** Removed profanity filter modules, AI profanity detectors, and related command handlers
  - **Code Optimization:** Cleaned up imports and references to profanity systems across all modules
  - **Database Integrity:** Maintained comprehensive content filter for other inappropriate content (sexual, violent, hate speech)
  - **Preserved Features:** All other bot functionality including banking, real estate, games, AI interactions, and general content moderation remains intact
  - **Performance Improvement:** Reduced system complexity and improved processing speed by removing unnecessary profanity checking layers

## Previous Changes (August 28, 2025)
- **Enhanced Message Processing System:** Created unified message processor (`handlers/unified_message_processor.py`) for consistent content detection
- **Eliminated Handler Conflicts:** Removed competing message handlers to ensure proper system routing
- **Comprehensive Content Coverage:** ALL message types (text, images, videos, stickers, files, voice messages) are processed through the same detection system
- **Improved Logging:** Enhanced logging to track message processing and content analysis
- **System Integration:** Properly integrated the comprehensive AI detection system with the bot's message routing
- **Enhanced Protection Hierarchy:** Implemented differentiated protection levels where Supreme Master (ID: 6524680126) has absolute protection from all content filtering
- **Master Protection System:** Added commands for Supreme Master to control content filtering on other Masters
- **Dynamic Content Control:** Masters can be dynamically switched between protection mode and normal content filtering
- **Simplified Command Structure:** Updated commands to use simple Arabic phrases for better user experience
- **Commands Documentation Update:** Updated `commands_list.txt` with proper organization and command sections

## External Dependencies
- **Telegram Bot API:** For core bot functionality and interaction.
- **Google AI (Gemini):** Used for advanced AI-driven content analysis, especially for explicit content detection in images and videos.
- **OpenAI API:** For general AI capabilities and intelligent responses.
- **Anthropic API:** For additional AI model integration.
- **YouTube API:** For potential video-related functionalities (e.g., fetching video information).