# Overview

This project is a sophisticated Telegram bot, developed using `aiogram`, designed to host an economic simulation game entirely in Arabic. Its core purpose is to provide a rich, interactive virtual economy where users can engage in diverse activities such as banking, real estate, stock trading, farming, and even player-vs-player theft. The bot aims to deliver a comprehensive, immersive gaming experience within Telegram groups, fostering a dynamic in-game economy.

The project is built on a modular architecture, ensuring scalability and maintainability, with data persistence managed efficiently using SQLite. Its ambition is to create a captivating and highly engaging virtual world that can support a large Arabic-speaking community.

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
- **Bot Framework**: `aiogram` (Python async Telegram bot framework)
- **Database**: SQLite with `aiosqlite` for async operations
- **Programming Language**: Python with async/await patterns

## Core Architectural Decisions
- **Modular Design**: Features are separated into distinct modules (e.g., Banking, Real Estate, Theft) for clear separation of concerns and easier development.
- **Command-Based Interface**: All user interactions are driven by text commands, replacing traditional inline keyboards for a streamlined group-chat experience.
- **Group-Exclusive Operation**: The bot is designed to function primarily within Telegram groups, with private messages serving only to guide users to group setup.
- **State Management**: `aiogram`'s Finite State Machine (FSM) is extensively used to manage complex multi-step user interactions across various game mechanics.
- **Database Layer**: Asynchronous database operations using `aiosqlite` ensure efficient CRUD functionality and robust data persistence for all game states and user data.
- **Admin & Access Control**: A multi-level admin privilege system with decorator-based access control manages user roles and permissions, including comprehensive moderation tools.
- **Arabic Language Support**: The entire bot, including commands, responses, and game elements, is designed for native Arabic language interaction.
- **UI/UX Decisions**: The interface is text-command driven, focusing on clear, concise Arabic messages. Visual elements, where present, are generated as text-based charts (ASCII art) within the chat.

## Key Feature Specifications
- **Economic Simulation**:
    - **Banking System**: Account creation, deposits, withdrawals, transfers, daily salaries, and bank-specific features.
    - **Real Estate**: Buying, selling, and income generation from virtual properties.
    - **Stock Market**: Trading virtual stocks with fluctuating prices.
    - **Theft Mechanics**: Player-vs-player robbery with security levels.
    - **Investment System**: Long-term investment options.
    - **Farming**: Crop planting and harvesting.
- **User Management**: Registration, user profiles, ranking system, and ban system.
- **Group Management**: Comprehensive moderation tools (ban, kick, mute), lock/unlock features for group settings, and entertainment commands.
- **Analytics Dashboard**: Provides administrators with real-time insights into group performance, financial data, user activity, and moderation metrics through text-based visual analytics and a health score system.

# External Dependencies

- **aiogram**: The primary framework for Telegram Bot API interaction.
- **aiosqlite**: Asynchronous adapter for SQLite database operations.
- **aiohttp**: Used for making asynchronous HTTP requests, primarily for potential integration with external APIs.
- **SQLite**: The chosen database for storing all user data, game states, transactions, and administrative records. Tables include `users`, `properties`, `stocks`, `bans`, `levels`, `investments`, `teams`, `team_members`, `custom_replies`, `custom_commands`, `banned_words`, `activity_logs`, `daily_stats`, and `performance_metrics`.
- **Python logging**: Utilized for error tracking, debugging, and operational monitoring.
- **asyncio**: Python's built-in library for writing concurrent code, essential for the bot's asynchronous operations.
- **External APIs (Configured but Optional)**: The architecture supports integration with external services such as Stock APIs for real market data, Payment Providers for premium features, and Crypto APIs for cryptocurrency price feeds, though these are not core mandatory integrations for basic bot functionality.