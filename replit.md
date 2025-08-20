# Overview

This project is an advanced Arabic-language Telegram economic simulation bot named "يوكي" (Yuki) with enhanced interactive features. The bot includes a comprehensive virtual economy with banking, real estate, stock trading, farming, and player-vs-player systems. Recent enhancements focus on bot personality protection, custom command systems for authorized users, music search functionality, and automated responses to specific triggers. The architecture remains modular with new security and entertainment systems integrated.

# User Preferences

Preferred communication style: Simple, everyday language.

Bot Configuration:
- Remove all keyboard buttons (inline keyboards)
- Bot works only in groups (not private messages except /start)
- /start command works ONLY in private chats, completely disabled in groups
- /start in private asks user to add bot to group as admin
- All functionality integrated into text messages/commands instead of buttons
- Fixed registration issues with user_required decorator
- Added special response system for specific users with personalized greetings
- Fixed bank account creation with dedicated handlers bypassing user_required decorator
- Changed salary collection cooldown from 3 minutes to 5 minutes
- Added missing last_salary_time column to database schema
- Added direct deposit/withdraw commands supporting "ايداع 100" and "سحب 200" format
- Implemented reply-based theft system where players reply to victim messages and write "سرقة" or "سرف"
- Fixed theft button display issue - removed non-functional inline keyboard buttons from security menu
- Theft functionality works through text commands only: reply to messages with "سرقة"/"سرف" for stealing
- Fixed widespread database parameter bug (fetch= to fetch_one=/fetch_all=) across all modules
- Separated security upgrade command: "ترقية الامان" now distinct from security menu "امان"
- Added comprehensive theft statistics and leaderboard functionality with text commands
- Enhanced security upgrade system with detailed cost/benefit display
- Updated castle deletion commands: "حذف قلعتي" (removed "حذف القلعة"), confirmation now accepts "تأكيد" or "نعم", cancellation with "لا"
- Enhanced banking system with immediate command recognition for better user experience
- Enhanced treasure hunt system with multi-resource discovery: single (45%), double (25%), triple (15%), quadruple (8%), nothing (7%)
- Fixed castle resource purchase commands: added support for "حجار" alternative to "حجارة" spelling
- Added missing properties database table to fix real estate module database errors
- Fixed critical balance bug in castle module causing negative balances (update_user_balance function misuse)
- Fixed rank promotion synchronization bug: unified hierarchy system and database storage with automatic synchronization
- Enhanced marriage system with comprehensive dowry mechanics, judge approval workflow, and commission system (Judge ID: 7155814194, commission range: 100-1000$)
- Added database startup synchronization to load existing ranks from database into memory dictionaries
- Added comprehensive user information commands: "رتبتي" (my rank), "فلوسي" (my balance), "فلوسه" (check others' balance with reply), "رتبته" (check others' rank with reply), "مستواي"/"مستواه" (level checking)
- Fixed bank selection handler conflicts that were interfering with user info commands
- Created dedicated user_info.py module for handling all user information display functionality
- Fixed critical bug in stocks module: missing stocks table in database causing "❌ حدث خطأ أثناء عرض الكلمات المفتاحية" error when using "محفظتي" command
- Created stocks table in SQLite database with proper schema for stock trading functionality
- Fixed null pointer exceptions and type errors in stocks.py module for proper portfolio display
- Enhanced get_user_stocks function to properly handle both single stock and portfolio queries
- Added proper error handling and null checks throughout stocks module to prevent crashes
- Fixed duplicate check_for_custom_replies function calls causing "خطأ في فحص الردود المخصصة: 0" errors
- Added Master-only delete custom reply functionality: "حذف رد [keyword]" command for Masters to delete any custom keyword/reply
- Enhanced keywords display with proper Arabic labels instead of English database column names
- Improved custom replies system reliability with direct aiosqlite connection and detailed logging
- **Added Simple Investment System**: Quick investment commands "استثمار [amount]" or "استثمار فلوسي" providing instant 0-30% random returns every 5 minutes with 50 XP reward per investment
- **Unified Level System**: Resolved conflicts between legacy and new level systems, ensuring consistent level 1000 display for Masters across all commands and modules
- **Enhanced Investment Center UI**: Updated investment center branding from "الاستثمار المحسن" to "الاستثمار المتقدم" with comprehensive explanations of simple vs advanced investment systems
- **Added Master Account Deletion Command**: "حذف حسابه" command allows Masters to completely delete any user's account with 10-second countdown and cancellation option. Includes protection against deleting other Masters
- **Added Master Level Fix Command**: "اصلح مستواه" command allows Masters to fix level inconsistencies by deleting and resetting user level data
- **Added Comprehensive Levels Guide**: "المستويات" command displays complete guide explaining level system, worlds, XP earning methods, progression tips, and useful commands for players

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
- **Admin & Access Control**: A multi-level admin privilege system with decorator-based access control and comprehensive moderation tools.
- **Hierarchical Administrative System**: Implemented a 4-level administrative hierarchy (Masters, Group Owners, Moderators, Members) with dynamic permission system.
- **Arabic Language Support**: Designed for native Arabic language interaction.
- **UI/UX Decisions**: The interface is text-command driven, focusing on clear, concise Arabic messages. Visual elements are text-based charts (ASCII art).
- **Insulting Permission System**: A hierarchical system that provides different insulting responses based on user level and the unauthorized command attempted.

## Key Feature Specifications
- **Economic Simulation**:
    - **Banking System**: Account creation, deposits, withdrawals, transfers, daily salaries, and bank-specific features across multiple virtual banks.
    - **Real Estate**: Buying, selling, and income generation from virtual properties.
    - **Stock Market**: Trading virtual stocks.
    - **Theft Mechanics**: Player-vs-player robbery with security levels.
    - **Investment System**: Dual investment architecture with simple (immediate 0-30% returns every 5 minutes) and advanced (long-term company investments) options.
    - **Farming**: Crop planting and harvesting.
    - **Castle System**: Comprehensive system for managing and upgrading virtual castles, including resource management, a dedicated shop, smart pricing, castle visibility controls (hide/show), attack/war system with unique castle IDs, and battle history tracking.
- **User Management**: Registration, user profiles, ranking system, ban system, and a detailed player profile system showing statistics and achievements.
- **Group Management**: Comprehensive moderation tools (ban, kick, mute), lock/unlock features, and entertainment commands.
- **Analytics Dashboard**: Provides administrators with real-time insights into group performance, financial data, user activity, and moderation metrics through text-based visual analytics and a health score system.
- **Special Response System**: Personalized greeting system for specific users and a comprehensive response system for all users, with automatic keyword detection and smart response selection.
- **Master Commands**: Ultimate control commands for Masters, including bot restart, shutdown, self-destruct, and financial control (adding money to any user).
- **Bot Protection System**: Anti-insult mechanism that responds mockingly to attempts to insult or demean the bot, protecting Yuki's personality and dignity.
- **Custom Commands System**: Authorized admins and moderators can create custom bot commands with keywords and responses.
- **Music Search Feature**: Users can search for and play songs from YouTube, Instagram, and TikTok through the bot.
- **Special Trigger Responses**: Automated responses to specific phrases.
- **Anti-Zarf Protection**: Special protection against "زرف"/"سرف" commands targeted at the bot itself with humorous responses.
- **Notification Channel System**: Comprehensive notification system for sub-channel with detailed bot activity and status updates.

# External Dependencies

- **aiogram**: Primary framework for Telegram Bot API interaction.
- **aiosqlite**: Asynchronous adapter for SQLite database operations.
- **aiohttp**: Used for making asynchronous HTTP requests.
- **SQLite**: The chosen database for storing all user data, game states, transactions, and administrative records across various tables (e.g., `users`, `properties`, `stocks`, `bans`, `levels`, `investments`, `teams`, `team_members`, `custom_replies`, `custom_commands`, `banned_words`, `activity_logs`, `daily_stats`, `performance_metrics`).
- **Python logging**: Utilized for error tracking, debugging, and operational monitoring.
- **asyncio**: Python's built-in library for writing concurrent code, essential for the bot's asynchronous operations.
- **External APIs**: Architecture supports integration with external services like Stock APIs, Payment Providers, and Crypto APIs.