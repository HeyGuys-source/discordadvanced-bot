# Overview

This is an advanced Discord moderation bot built with Python and discord.py. The bot provides comprehensive server management features including automated moderation, custom commands, reaction roles, welcome/farewell messages, starboard functionality, and a web dashboard for configuration. It's designed to help Discord server administrators efficiently manage their communities with powerful automation and logging capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Core**: Built on discord.py with a cog-based modular architecture
- **Command System**: Hybrid approach supporting both traditional prefix commands and modern slash commands (app_commands)
- **Event Handling**: Comprehensive event listeners for message monitoring, member events, and reaction tracking
- **Permission System**: Custom decorators for checking user and bot permissions before command execution

## Database Layer
- **Database**: SQLite with aiosqlite for async operations
- **Schema**: Relational design with tables for guild settings, moderation logs, custom commands, reaction roles, and event tracking
- **Data Management**: Centralized Database class handling all database operations with proper connection management

## Modular Cog System
- **Moderation**: Traditional moderation commands (kick, ban, mute, warn) with proper permission checks
- **AutoMod**: Automated content filtering for spam, links, mentions, and blocked words with configurable thresholds
- **Custom Commands**: Dynamic command system with variable substitution and auto-responses
- **Reaction Roles**: Role assignment through emoji reactions on messages
- **Welcome System**: Configurable welcome/farewell messages with auto-role assignment
- **Starboard**: Popular message highlighting system based on star reactions
- **Logging**: Comprehensive event logging for moderation actions and server events

## Web Dashboard
- **Framework**: Flask-based web interface for bot configuration
- **Authentication**: Discord OAuth2 integration for secure user authentication
- **Interface**: Bootstrap-powered responsive UI with guild-specific configuration pages
- **Real-time Updates**: JavaScript-driven dashboard for dynamic settings management

## Configuration Management
- **Settings**: Environment-based configuration with sensible defaults
- **Guild-specific**: Per-server customization of all bot features
- **Color Scheme**: Consistent Discord-themed UI elements and embed colors
- **Rate Limiting**: Built-in protection against command spam

## Permission & Security
- **Role Hierarchy**: Respect for Discord's role hierarchy in all moderation actions
- **Permission Validation**: Dual checks for both user and bot permissions
- **Audit Logging**: Comprehensive logging of all moderation actions for accountability
- **Error Handling**: Graceful error handling with user-friendly error messages

# External Dependencies

## Core Libraries
- **discord.py**: Primary Discord API wrapper for bot functionality
- **aiosqlite**: Async SQLite database operations
- **Flask**: Web framework for the dashboard interface
- **Flask-CORS**: Cross-origin resource sharing support

## Web Dashboard
- **Discord OAuth2 API**: User authentication and guild access verification
- **Bootstrap 5**: Frontend CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements

## Development Tools
- **Python Logging**: Built-in logging system for debugging and monitoring
- **Regex**: Pattern matching for automod content filtering and variable processing

## Potential Integrations
- **PostgreSQL**: Database can be upgraded from SQLite for production use
- **Redis**: Can be added for caching and session management
- **Webhook Services**: Extensible logging system supports external webhook integration