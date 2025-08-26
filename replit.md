# Overview

This project is an advanced Arabic-language Telegram economic simulation bot named "يوكي" (Yuki), designed to offer a comprehensive virtual economy experience. Its core purpose is to provide an engaging and interactive platform for users to participate in banking, real estate, stock trading, farming, and player-vs-player systems within a virtual environment. The project aims to integrate robust security, advanced AI interactions, and entertainment features, establishing a dynamic and responsive bot that protects its personality while offering deep economic simulation and social interaction. The business vision is to create a leading virtual economic game within the Telegram ecosystem, attracting a wide user base through its unique features and immersive Arabic-centric design.

# User Preferences

Preferred communication style: Simple, everyday language.

Bot Configuration:
- Remove all keyboard buttons (inline keyboards)
- Bot works only in groups (not private messages except /start)
- /start command works ONLY in private chats, completely disabled in groups
- /start in private asks user to add bot to group as admin
- All functionality integrated into text messages/commands instead of buttons
- Reply-based theft system where players reply to victim messages and write "سرقة" or "سرف"
- Theft functionality works through text commands only: reply to messages with "سرقة"/"سرف" for stealing
- Castle deletion confirmation now accepts "تأكيد" or "نعم", cancellation with "لا"
- New Farm Commands: "حصاد محاصيلي" for harvesting all ready crops and "حصاد [النوع] [العدد]" for harvesting specific quantities of specific crops
- Master-only delete custom reply functionality: "حذف رد [keyword]" command for Masters to delete any custom keyword/reply
- Master Account Deletion Command: "حذف حسابه" command allows Masters to completely delete any user's account with 10-second countdown and cancellation option. Includes protection against deleting other Masters
- Master Level Fix Command: "اصلح مستواه" command allows Masters to fix level inconsistencies by deleting and resetting user level data
- Natural Arabic Protection Commands: Group owners can control protection with intuitive commands: "تفعيل الحماية", "تعطيل الحماية", "حالة الحماية" (restricted to group owners and masters)

# System Architecture

## Framework and Technology Stack
- **Bot Framework**: `aiogram` (Python async Telegram bot framework)
- **Database**: SQLite with `aiosqlite` for async operations
- **Programming Language**: Python with async/await patterns

## Core Architectural Decisions
- **Modular Design**: Features are separated into distinct modules for clear separation of concerns.
- **Command-Based Interface**: All user interactions are driven by text commands.
- **Group-Exclusive Operation**: The bot functions primarily within Telegram groups; private messages guide users to group setup.
- **State Management**: `aiogram`'s Finite State Machine (FSM) manages complex multi-step user interactions.
- **Database Layer**: Asynchronous database operations using `aiosqlite` ensure efficient CRUD functionality.
- **Admin & Access Control**: A multi-level admin privilege system with decorator-based access control and comprehensive moderation tools, featuring a 4-level administrative hierarchy (Masters, Group Owners, Moderators, Members).
- **Arabic Language Support**: Designed for native Arabic language interaction.
- **UI/UX Decisions**: The interface is text-command driven, focusing on clear, concise Arabic messages. Visual elements are text-based charts (ASCII art).
- **AI Integration**: Enhanced Google Gemini AI system to access player database for comprehensive statistics and provide detailed user progress information via natural language queries.
- **Bot Personality Protection**: Anti-insult mechanisms and response systems protect the bot's identity and dignity.

## Key Feature Specifications
- **Economic Simulation**:
    - **Banking System**: Account creation, deposits, withdrawals, transfers, daily salaries, and bank-specific features.
    - **Real Estate**: Buying, selling, and income generation from virtual properties.
    - **Stock Market**: Trading virtual stocks with portfolio management.
    - **Theft Mechanics**: Player-vs-player robbery with security levels and detailed statistics.
    - **Investment System**: Dual investment architecture with simple (instant random returns) and advanced (long-term company investments) options.
    - **Farming**: Crop planting and command-based harvesting with detailed profit analysis.
    - **Castle System**: Management and upgrade of virtual castles, including resource management, shop, pricing, visibility controls, attack/war system, and battle history.
- **User Management**: Registration, profiles, ranking system, ban system, and detailed player statistics.
- **Group Management**: Moderation tools (ban, kick, mute), lock/unlock features, and entertainment commands.
- **Analytics Dashboard**: Text-based visual analytics and health score for administrators, showing group performance, financial data, and user activity.
- **Special Response System**: Personalized greetings and automatic responses to keywords.
- **Master Commands**: Ultimate control commands for Masters, including bot restart, shutdown, self-destruct, and financial control.
- **Custom Commands System**: Authorized users can create custom bot commands with keywords and responses.
- **Music Search Feature**: Search and play songs from YouTube, Instagram, and TikTok.
- **Advanced AI-Powered Protection System**: Sophisticated profanity detection using machine learning (TfidfVectorizer + LogisticRegression) with database-driven word classification, severity levels, automated message deletion, progressive warnings, and punishment escalation. Includes smart detection methods for encrypted/obfuscated text.
- **Fixed Game Commands Word Boundary Detection**: Implemented comprehensive word boundary detection for all game commands to prevent accidental activation when mentioned within sentences. Applied regex-based standalone word detection to all games including quiz, royal battle, word game, symbols, battle arena, luck wheel, number guess, and XO game. Commands now require exact matching instead of substring matching. Date: August 26, 2025
- **Notification System**: Comprehensive notification system for sub-channels detailing bot activity and status updates.

# External Dependencies

- **aiogram**: Primary framework for Telegram Bot API interaction.
- **aiosqlite**: Asynchronous adapter for SQLite database operations.
- **aiohttp**: Used for making asynchronous HTTP requests.
- **SQLite**: The chosen database for storing all user data, game states, transactions, and administrative records.
- **Python logging**: Utilized for error tracking, debugging, and operational monitoring.
- **asyncio**: Python's built-in library for writing concurrent code.
- **Google Gemini AI**: Integrated for natural language processing and database querying.
- **scikit-learn**: Used for machine learning models (TfidfVectorizer, LogisticRegression) in the profanity detection system.
- **External APIs (supported)**: Architecture supports integration with external services like Stock APIs, Payment Providers, and Crypto APIs.