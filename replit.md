# Overview

This project is an economic simulation game implemented as a Telegram bot using `aiogram`, designed specifically for the Arabic-speaking community. It offers a comprehensive virtual economy where users can engage in banking, real estate, stock trading, farming, and player-vs-player theft. The bot aims to provide an immersive gaming experience within Telegram groups, fostering a dynamic in-game economy. The architecture is modular for scalability and maintainability, with data persistence managed by SQLite. The overarching ambition is to create a captivating virtual world supporting a large Arabic-speaking user base.

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
- Enhanced banking system with immediate command recognition for better user experience

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

# External Dependencies

- **aiogram**: Primary framework for Telegram Bot API interaction.
- **aiosqlite**: Asynchronous adapter for SQLite database operations.
- **aiohttp**: Used for making asynchronous HTTP requests.
- **SQLite**: The chosen database for storing all user data, game states, transactions, and administrative records across various tables (e.g., `users`, `properties`, `stocks`, `bans`, `levels`, `investments`, `teams`, `team_members`, `custom_replies`, `custom_commands`, `banned_words`, `activity_logs`, `daily_stats`, `performance_metrics`).
- **Python logging**: Utilized for error tracking, debugging, and operational monitoring.
- **asyncio**: Python's built-in library for writing concurrent code, essential for the bot's asynchronous operations.
- **External APIs (Configured but Optional)**: Architecture supports integration with external services like Stock APIs, Payment Providers, and Crypto APIs.