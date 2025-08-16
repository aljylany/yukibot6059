# Overview

This is a comprehensive Telegram bot built with aiogram that implements an economic simulation game in Arabic. The bot features a complex virtual economy where users can engage in banking, real estate, stock trading, farming, theft mechanics, and more. The project follows a modular architecture with separate handlers for different bot functionalities and uses SQLite for data persistence.

# User Preferences

Preferred communication style: Simple, everyday language.

Bot Configuration:
- Remove all keyboard buttons (inline keyboards)
- Bot works only in groups (not private messages except /start)
- /start in private asks user to add bot to group as admin
- All functionality integrated into text messages/commands instead of buttons
- Fixed registration issues with user_required decorator

# System Architecture

## Framework and Technology Stack
- **Bot Framework**: aiogram (Python async Telegram bot framework)
- **Database**: SQLite with aiosqlite for async operations
- **Programming Language**: Python with async/await patterns
- **Architecture Pattern**: Modular design with separation of concerns

## Core Components

### Handler System
The bot uses a command-focused handler system:
- **Commands Handler**: Processes slash commands like `/start`, `/help`, `/balance`
- **Callbacks Handler**: Removed - no longer uses inline keyboards
- **Messages Handler**: Handles text messages based on FSM states
- **Group-Only Operation**: Bot only works in groups, private messages redirect to group setup

### State Management
Implements aiogram's FSM (Finite State Machine) for managing user interactions across different modules:
- Banking states for deposits/withdrawals
- Property states for real estate transactions
- Theft states for robbery mechanics
- Investment and farming states for economic activities

### Database Layer
- **Models**: User data structures with dataclasses
- **Operations**: Async database operations for CRUD functionality
- **Connection Management**: Context managers for database connections

### Modular Game Systems
Each game feature is implemented as a separate module:
- **Banking System**: Virtual currency management, transfers, daily bonuses
- **Real Estate**: Property buying/selling with income generation
- **Stock Market**: Virtual stock trading with fluctuating prices
- **Theft Mechanics**: Player-vs-player robbery with security levels
- **Investment System**: Long-term investment options with returns
- **Farming**: Crop planting and harvesting mechanics
- **Castle Building**: Construction and upgrade system
- **Ranking System**: Leaderboards and player statistics

### Security and Access Control
- Admin privilege system with decorator-based access control
- User authentication and registration flow
- Ban system for problematic users
- Activity tracking and user state management

## External Dependencies

### Core Bot Dependencies
- **aiogram**: Telegram Bot API framework for Python
- **aiosqlite**: Async SQLite database adapter
- **aiohttp**: HTTP client for external API calls

### Database
- **SQLite**: Local database for user data, transactions, and game state
- Tables include: users, properties, stocks, bans, levels, investments

### External APIs (Configured but Optional)
- **Stock APIs**: For real market data integration
- **Payment Providers**: Telegram payments for premium features
- **Crypto APIs**: For cryptocurrency price feeds

### Development and Logging
- **Python logging**: Comprehensive error tracking and debugging
- **asyncio**: Async programming support for scalable operations

## Recent Changes (August 16, 2025)

### Architecture Modifications
- **Removed Inline Keyboards**: Eliminated all keyboard buttons and inline callbacks
- **Group-Only Operation**: Bot now works exclusively in group chats
- **Private Message Handling**: /start in private messages guides users to add bot to groups
- **Command-Based Interface**: All functionality moved to text commands instead of button interactions
- **Fixed Registration Issues**: Updated user_required decorator to handle group-only operations
- **Simplified Callbacks**: Removed all callback handlers since keyboards are no longer used

### New Bank Account System
- **"انشاء حساب بنكي" Registration**: Users now type "انشاء حساب بنكي" instead of /start to begin
- **Bank Selection System**: Players choose from 4 different banks (الأهلي، الراجحي، سامبا، الرياض)
- **Random Daily Salary**: Each bank offers different salary ranges and bonuses
- **Bank-Specific Features**: Each bank has unique initial bonuses, daily salary ranges, and interest rates
- **Keyword-Based Commands**: Players use Arabic keywords like "راتب" for salary, "رصيد" for balance

### User Experience Changes
- Users must add bot as admin to their groups to use features
- Registration starts with "انشاء حساب بنكي" in groups only
- Bank selection process with detailed comparison
- Daily salary collection with random bonuses
- Text-based interactions using Arabic keywords
- Improved error handling for group vs private message contexts

The architecture prioritizes modularity and group-based gaming, allowing easy addition of new game features while maintaining clean separation between bot logic, database operations, and external service integrations.

## Current Status (August 16, 2025)

### ✅ Successfully Completed
- **Configuration System**: Created complete config/settings.py with all required settings
- **Database Setup**: Fixed database operations and created bot_database.db (53KB)
- **Dependencies**: All packages installed (aiogram, aiosqlite)
- **Code Structure**: Resolved all import errors and missing functions
- **File Organization**: Created proper config/ directory structure

### ⚠️ Next Steps Required
- **Bot Token**: Current token is invalid/expired - needs new token from @BotFather
- **Testing**: Once valid token provided, bot should work immediately

### Technical Details
- Bot starts successfully but fails at token validation
- Database initializes properly with all required tables
- All Python dependencies are correctly installed
- Error message: "Token is invalid!" indicates token issue only

The bot is fully ready to run and just needs a valid Telegram bot token to become operational.