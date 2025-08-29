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
    - **Comprehensive Content Filter:** Integrates profanity detection with explicit content filtering using Google AI (Gemini) for advanced analysis.
    - **Graduated Penalties:** Implements a tiered punishment system ranging from warnings to permanent bans based on content severity.
    - **Admin Reporting System:** Provides real-time notifications, daily summaries, and detailed reports for administrators on detected violations.
    - **Testing & Monitoring:** Includes extensive test commands (`/test_filter`, `/test_profanity`, `اختبار النظام`) and detailed logging for live monitoring of filtering processes.
- **AI & Interaction:**
    - **Smart Menus:** Features a "Smart Menu" with 8 interactive options (e.g., economic analysis, smart games, quizzes, interactive stories, AI battles).
    - **FSM (Finite State Machine):** Employs FSM states (`SmartCommandStates`) to manage complex multi-step interactions like quizzes and interactive narratives.
    - **API Management:** Reads all API keys (OpenAI, Anthropic, Telegram Bot Token, YouTube) from a single `api.txt` file for easy configuration and security.
- **Command Handling:**
    - **Direct Commands:** Supports direct Arabic and English commands for quick access to features.
    - **Permission System:** Implements a robust permission system: Owners and "Masters" have full access, Moderators have access to reports/stats, and regular members have no administrative access. "Masters" are immune to penalties.

### Feature Specifications
- **Content Types Scanned:** Text, images, videos (frame extraction + filename), stickers (emoji + filename + image analysis), and files (type + filename + image content).
- **Punishment Levels:** Warning, 5-30 min mute, 1-6 hour mute, 24-hour to permanent mute, permanent group ban.
- **Admin Commands:** Includes commands for security statistics (`احصائيات الأمان`), group/user reports (`تقرير المجموعة`), system status (`حالة النظام`), report subscription management, and user violation log management.

### System Design Choices
- **Modularity:** Core functionalities are organized into distinct modules (e.g., `comprehensive_content_filter.py`, `admin_reports_system.py`, `smart_menu_handler.py`).
- **Unified Processing:** Implemented centralized message processing to eliminate handler conflicts and ensure comprehensive content analysis.
- **Performance Optimization:** Focuses on faster and more accurate processing with intelligent API key consumption and automatic switching.
- **Circular Import Resolution:** Specific attention paid to resolving common Python issues like circular imports (e.g., in `utils/decorators.py`).

## Recent Changes (August 29, 2025)
- **Fixed Three-Warning System Properly:** Fixed critical issue where high-severity profanity (like harsh swear words) bypassed the three-warning system and went straight to mute:
  - **Unified Warning System:** Modified `_determine_punishment_action()` to ensure ALL violations start with warnings (1-3) regardless of severity level
  - **True Progressive System:** First 3 violations now ALWAYS result in warnings, then punishments begin based on violation count plus severity multiplier
  - **Severity-Based Acceleration:** After 3 warnings, severe violations add extra punishment levels (harsh profanity +2, moderate +1) for faster escalation
  - **Educational Approach:** Users now get proper opportunity to learn and correct behavior before facing actual punishment consequences
- **Enhanced Admin Command Responses:** Updated "إلغاء سوابق" (clear records) command responses to show detailed cleanup information:
  - **Detailed Cleanup Reports:** Shows exact numbers of deleted warnings, violation records, and reset punishment points
  - **Comprehensive Database Coverage:** Updated cleanup functions to return detailed results from all database tables
  - **Enhanced Admin Visibility:** Administrators can now see exactly what data was cleaned and from which systems
- **Improved Violations Records Display:** Updated violation record queries to pull data from all database tables:
  - **Multi-Table Integration:** Combines data from `user_warnings`, `violation_history`, and `user_violation_points` tables
  - **Complete User Profile:** Shows warnings count, violation points, punishment level, and ban status in unified view
  - **Better Admin Oversight:** Administrators get complete picture of user violation history across all systems
- **Complete Violation System Overhaul:** Fixed major issue where "إلغاء سوابق" (clear records) command only deleted warnings but not violation history, causing users to be immediately banned again:
  - **Comprehensive Database Cleanup:** Updated all cleanup functions (`clear_user_all_violations`, `clear_user_group_violations`, `cleanup_all_violations`, `cleanup_group_violations`) to delete from multiple database tables
  - **Multi-Table Reset:** Now clears data from `user_warnings`, `violation_history`, `user_violation_points`, and `detailed_admin_reports` tables
  - **True Fresh Start:** Users now get a genuine fresh start with complete violation history reset, returning to the 3-warning system as intended
  - **Enhanced Logging:** Added detailed logging to show exactly what data is being cleared from each database table
  - **Punishment Level Reset:** Violation points, punishment levels, and permanent ban status are now properly reset to zero/false
- **Merciful Reset System Implementation:** Added automatic warning reset when admins manually unmute users:
  - **Admin Unmute Detection:** When a moderator uses the unmute command (`الغاء كتم`), the system automatically detects this action
  - **Complete Warning Reset:** All user violations and warnings are completely cleared from the database (`reset_user_warnings()` function)
  - **Fresh Start Principle:** Users get a completely fresh start with new three-warning cycle after being unmuted by an admin
  - **Educational Priority:** System prioritizes rehabilitation over punishment by giving users multiple opportunities to improve
  - **Admin Feedback:** Unmute messages now include confirmation that warnings have been reset for transparency
- **Three-Warning System Implementation:** Modified the profanity detection system to provide three progressive warnings before taking actual punishment actions:
  - **First Warning (1/3):** Simple warning with gentle reminder about community standards
  - **Second Warning (2/3):** Stronger warning indicating final chance before punishment
  - **Third Strike:** After 3 warnings, the user receives the actual punishment (mute for 1 hour)
- **Enhanced Warning Messages:** Updated all warning messages to display current warning count (e.g., "التحذيرات: 2/3") for better user awareness
- **Improved User Experience:** Users now have multiple chances to correct their behavior before facing consequences, making the system more educational rather than purely punitive
- **Smart Warning Tracking:** Added `get_user_warnings()` function to track and retrieve current warning counts from the database
- **Graduated Response System:** Different message tones for each warning level - from educational to final warning to punishment notification
- **Advanced Graduated Punishment System:** Implemented sophisticated punishment escalation based on violation count and severity:
  - **Warning Phase (1-3 violations):** Educational warnings only
  - **Graduated Muting (4+ violations):** Progressive mute durations: 1 min → 2 min → 3 min → 4 min → 5 min → 10 min → 30 min → 1 hour → 2 hours → 3 hours → 4 hours → 1 day → 2 days → 3 days → 1 week → 1 month
  - **Permanent Ban (17+ violations):** Automatic permanent removal from group
  - **Severity-Based Acceleration:** Higher severity violations (harsh profanity) accelerate punishment progression
  - **Dynamic Duration Calculation:** `calculate_punishment_duration()` function determines appropriate punishment based on user history and violation severity
  - **Merciful Reset Feature:** When admins manually unmute a user, the system gives them a fresh start by resetting their violation history completely

## Previous Changes (August 28, 2025)
- **Fixed Message Detection System:** Created unified message processor (`handlers/unified_message_processor.py`) to resolve issues where profanity detection wasn't working consistently
- **Eliminated Handler Conflicts:** Removed competing message handlers that were causing messages to bypass the detection system
- **Ensured Complete Coverage:** Now ALL message types (text, images, videos, stickers, files, voice messages) are processed through the same comprehensive detection system
- **Improved Logging:** Enhanced logging to track exactly which messages are being processed and detected
- **System Integration:** Properly integrated the comprehensive AI detection system with the bot's message routing
- **Enhanced Protection Hierarchy:** Implemented differentiated protection levels where Supreme Master (ID: 6524680126) has absolute protection from all content filtering, while other Masters can be tested for system verification purposes
- **Master Testing Mode:** Added `other_masters_testing_enabled` flag to allow selective testing of content detection on regular Masters while maintaining Supreme Master immunity
- **Supreme Master Commands System:** Added exclusive commands for Supreme Master to control punishment system on other Masters with simplified Arabic commands:
  - `تفعيل العقوبات` / `تفعيل عقوبات الاسياد` - Enable full punishments on other Masters (treat them as regular members)
  - `الغاء العقوبات` / `تعطيل العقوبات` - Disable punishments on Masters (return to protection mode)
  - `حالة العقوبات` / `وضع الاسياد` - Check current punishment status for Masters
- **Dynamic Punishment Control:** Masters can now be dynamically switched between protection mode and full punishment mode while Supreme Master remains permanently protected
- **Simplified Command Structure:** Updated commands to use simple Arabic phrases for better user experience
- **Commands Documentation Update:** Updated `commands_list.txt` with new Supreme Master exclusive commands section and proper organization
- **Added Help Command:** Added `اوامر النظام الجديد` command for Supreme Master to view new system commands

## External Dependencies
- **Telegram Bot API:** For core bot functionality and interaction.
- **Google AI (Gemini):** Used for advanced AI-driven content analysis, especially for explicit content detection in images and videos.
- **OpenAI API:** For general AI capabilities and intelligent responses.
- **Anthropic API:** For additional AI model integration.
- **YouTube API:** For potential video-related functionalities (e.g., fetching video information).