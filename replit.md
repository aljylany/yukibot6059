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
- **Content Moderation:**
    - **Unified Message Processor:** New centralized system (`handlers/unified_message_processor.py`) that ensures ALL messages (text, images, videos, stickers, files, voice, etc.) pass through the detection system without conflicts or bypasses.
    - **Comprehensive Content Filter:** Uses Google AI (Gemini) for advanced content analysis, focusing on inappropriate sexual content, violent content, and hate speech detection.
    - **Admin Reporting System:** Provides real-time notifications, daily summaries, and detailed reports for administrators on detected violations.
- **AI & Interaction:**
    - **Smart Menus:** Features a "Smart Menu" with 8 interactive options (e.g., economic analysis, smart games, quizzes, interactive stories, AI battles).
    - **FSM (Finite State Machine):** Employs FSM states (`SmartCommandStates`) to manage complex multi-step interactions like quizzes and interactive narratives.
    - **API Management:** Reads all API keys (OpenAI, Anthropic, Telegram Bot Token, YouTube) from a single `api.txt` file for easy configuration and security.
- **Command Handling:**
    - **Direct Commands:** Supports direct Arabic and English commands for quick access to features.
    - **Permission System:** Implements a robust permission system: Owners and "Masters" have full access, Moderators have access to reports/stats, and regular members have no administrative access. "Masters" are immune to penalties.

### Feature Specifications
- **Content Types Scanned:** Text, images, videos (frame extraction + filename), stickers (emoji + filename + image analysis), and files (type + filename + image content).
- **Punishment Levels:** Warning, temporary mute, permanent mute, permanent group ban.
- **Admin Commands:** Includes commands for security statistics (`احصائيات الأمان`), group/user reports (`تقرير المجموعة`), system status (`حالة النظام`), and report subscription management.

### System Design Choices
- **Modularity:** Core functionalities are organized into distinct modules (e.g., `comprehensive_content_filter.py`, `admin_reports_system.py`, `smart_menu_handler.py`).
- **Unified Processing:** Implemented centralized message processing to eliminate handler conflicts and ensure comprehensive content analysis.
- **Performance Optimization:** Focuses on faster and more accurate processing with intelligent API key consumption and automatic switching.
- **Circular Import Resolution:** Specific attention paid to resolving common Python issues like circular imports (e.g., in `utils/decorators.py`).

## Recent Changes (August 29, 2025)
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