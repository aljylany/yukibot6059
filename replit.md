# Overview

This project is an advanced Arabic-language Telegram economic simulation bot named "يوكي" (Yuki) with enhanced interactive features. The bot includes a comprehensive virtual economy with banking, real estate, stock trading, farming, and player-vs-player systems. Recent enhancements focus on bot personality protection, custom command systems for authorized users, music search functionality across multiple platforms, and automated responses to specific triggers. The architecture remains modular with new security and entertainment systems integrated.

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
    - **Banking System**: Account creation (manual), deposits, withdrawals, transfers, daily salaries, and bank-specific features across multiple virtual banks.
    - **Real Estate**: Buying, selling, and income generation from virtual properties.
    - **Stock Market**: Trading virtual stocks.
    - **Theft Mechanics**: Player-vs-player robbery with security levels.
    - **Investment System**: Long-term investment options.
    - **Farming**: Crop planting and harvesting.
    - **Castle System**: Comprehensive system for managing and upgrading virtual castles, including resource management, a dedicated shop, smart pricing, castle visibility controls (hide/show), attack/war system with unique castle IDs, and battle history tracking.
- **User Management**: Registration, user profiles, ranking system, ban system, and a detailed player profile system showing statistics and achievements.
- **Group Management**: Comprehensive moderation tools (ban, kick, mute), lock/unlock features, and entertainment commands.
- **Analytics Dashboard**: Provides administrators with real-time insights into group performance, financial data, user activity, and moderation metrics through text-based visual analytics and a health score system.
- **Special Response System**: Personalized greeting system for specific users and a comprehensive response system for all users, with automatic keyword detection and smart response selection.
- **Master Commands**: Ultimate control commands for Masters, including bot restart, shutdown, self-destruct, and financial control (adding money to any user).
- **Bot Protection System**: Anti-insult mechanism that responds mockingly to attempts to insult or demean the bot, protecting Yuki's personality and dignity.
- **Custom Commands System**: Authorized admins and moderators can create custom bot commands with keywords and responses using "اضافة امر" command.
- **Music Search Feature**: Users can search for and play songs from YouTube, Instagram, and TikTok through the bot with commands like "ابحث عن اغنية".
- **Special Trigger Responses**: Automated responses to specific phrases like "جاب العيد" which triggers a special YouTube music link.
- **Anti-Zarf Protection**: Special protection against "زرف"/"سرف" commands targeted at the bot itself with humorous responses.

# External Dependencies

- **aiogram**: Primary framework for Telegram Bot API interaction.
- **aiosqlite**: Asynchronous adapter for SQLite database operations.
- **aiohttp**: Used for making asynchronous HTTP requests.
- **SQLite**: The chosen database for storing all user data, game states, transactions, and administrative records across various tables (e.g., `users`, `properties`, `stocks`, `bans`, `levels`, `investments`, `teams`, `team_members`, `custom_replies`, `custom_commands`, `banned_words`, `activity_logs`, `daily_stats`, `performance_metrics`).
- **Python logging**: Utilized for error tracking, debugging, and operational monitoring.
- **asyncio**: Python's built-in library for writing concurrent code, essential for the bot's asynchronous operations.
- **External APIs (Configured but Optional)**: Architecture supports integration with external services like Stock APIs, Payment Providers, and Crypto APIs.

# Recent Changes (2025-08-17)

## Latest Updates:
- ✅ **Notification Channel System**: Implemented comprehensive notification system for sub-channel "@erAruca685xmMDNk"
  - Detailed notifications when bot is added to new groups (group info, admin list, member count)
  - Bot promotion/demotion notifications
  - Bot removal notifications
  - Startup and maintenance notifications
  - Error alerts for administrators
  - Daily statistics reporting capability
- ✅ **Group Events Handler**: New `handlers/group_events.py` module for handling my_chat_member events
- ✅ **Notification Manager**: Advanced `modules/notification_manager.py` for structured notification handling
- ✅ **Admin Test Command**: `/test_channel` command for administrators to test notification channel connectivity
- ✅ **Enhanced Configuration**: Added NOTIFICATION_CHANNEL settings in `config/settings.py`
- ✅ **Automatic Startup Notifications**: Bot sends startup notification to channel when launched

## Previous Features:
- ✅ **Bot Insult Protection System**: Yuki now responds with sarcastic and defensive messages when users attempt to insult or demean the bot
- ✅ **Custom Commands System**: Authorized users (moderators+) can add custom commands with "اضافة امر [keyword] [response]" format
- ✅ **Music Search Integration**: Users can search for music across YouTube, SoundCloud, and Spotify platforms with commands like "ابحث عن اغنية [song name]"
- ✅ **"جاب العيد" Special Response**: Automatically responds with a specific YouTube music link when this phrase is mentioned
- ✅ **Anti-Zarf Protection**: Bot refuses to be "zarfed" and responds humorously when targeted with زرف/سرف commands
- ✅ **Enhanced Database Schema**: Updated custom_commands table with proper keyword/responses columns
- ✅ **State Management**: Integrated CustomCommandsStates for multi-step command creation
- ✅ **Permission-Based Access**: Custom command creation restricted to moderators and above
- ✅ **Database Integration**: All new features fully integrated with SQLite database and async operations

## Technical Updates:
- Added new modules: `custom_commands.py`, `music_search.py`, `message_handlers.py`, `group_events.py`, `notification_manager.py`
- Enhanced `special_responses.py` with comprehensive bot protection responses  
- Updated database schema for custom commands support
- Integrated new features into main message handling pipeline
- Added proper error handling and logging for all new features
- Fixed group settings toggle commands by adding missing "التحميل" setting to TOGGLE_SETTINGS
- Enhanced media download toggle with proper admin permission checks
- Corrected permission function calls to use has_permission from config.hierarchy
- Fixed "جاب العيد" response to send audio file instead of showing YouTube link
- Added comprehensive debugging for download settings persistence issues
- Adjusted permission level for download toggle to MEMBER level for better accessibility
- Integrated group events monitoring with my_chat_member handler
- Enhanced main.py with automatic startup notifications