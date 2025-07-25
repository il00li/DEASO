# Pixabay Telegram Bot

## Overview

This is a Telegram bot that integrates with the Pixabay API to provide users with access to various media content including photos, illustrations, vectors, videos, music, and GIFs. The bot is built using Python with the python-telegram-bot library and provides a user-friendly interface for searching and retrieving media from Pixabay.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Language**: Python 3.x
- **Framework**: python-telegram-bot library for Telegram Bot API integration
- **Architecture Pattern**: Event-driven bot architecture with command and callback handlers
- **Data Storage**: In-memory storage using Python dictionaries and sets (temporary solution)
- **External API Integration**: Pixabay API for media content retrieval

### Key Design Decisions
- **In-memory storage**: Currently uses Python dictionaries and sets for user data, channel management, and statistics. This is noted as a temporary solution with plans to migrate to a proper database for production use.
- **Asynchronous processing**: Uses async/await pattern for handling Telegram updates and API calls
- **Modular handler approach**: Separates different bot functionalities into distinct command and callback handlers

## Key Components

### Core Bot Class
- **PixabayBot**: Main bot class that encapsulates all bot functionality
- **Handler Methods**: Separate methods for different bot commands and interactions
- **Media Type Support**: Supports 6 different media types (photos, illustrations, vectors, videos, music, GIFs)

### Configuration Management
- **Environment Variables**: Uses environment variables for sensitive configuration (BOT_TOKEN, ADMIN_ID, PIXABAY_API_KEY)
- **Default Values**: Provides fallback default values for development/testing

### User Management System
- **User Data Tracking**: Stores user information and interaction history
- **Admin Controls**: Special admin user with elevated privileges
- **Channel Force-Join**: Implements forced channel subscription mechanism
- **User Banning**: Basic user moderation system with ban functionality

### Statistics Tracking
- **Bot Analytics**: Tracks total users, searches, and bot start date
- **Usage Metrics**: Monitors bot usage patterns and user engagement

## Data Flow

1. **User Interaction**: User sends command or message to bot
2. **Handler Processing**: Appropriate handler processes the request based on command type
3. **API Integration**: For search requests, bot queries Pixabay API with user parameters
4. **Response Formatting**: Bot formats API response into user-friendly Telegram messages
5. **User Storage**: User interaction data is stored in memory for tracking and analytics

## External Dependencies

### Telegram Bot API
- **python-telegram-bot**: Primary library for Telegram Bot API integration
- **Bot Token**: Required for bot authentication with Telegram
- **Webhook/Polling**: Handles incoming updates from Telegram servers

### Pixabay API
- **API Key**: Required for accessing Pixabay media content
- **Rate Limiting**: Subject to Pixabay API rate limits and usage policies
- **Content Types**: Supports multiple media types through different API endpoints

### System Dependencies
- **requests**: HTTP client for API calls
- **asyncio**: Asynchronous programming support
- **logging**: Application logging and debugging
- **json**: Data serialization and parsing

## Deployment Strategy

### Current Setup
- **Environment**: Designed for Replit deployment
- **Configuration**: Environment variable-based configuration
- **Storage**: In-memory storage (temporary solution)

### Production Considerations
- **Database Migration**: Code comments indicate plans to migrate from in-memory storage to a proper database
- **Scalability**: Current architecture needs database backend for production scale
- **Monitoring**: Basic logging implemented, may need enhanced monitoring for production

### Security Features
- **Admin Controls**: Role-based access for administrative functions
- **User Moderation**: Ban system for problematic users
- **Channel Management**: Force-join mechanism for channel promotion
- **Token Security**: Sensitive tokens managed through environment variables

## Development Notes

### Current Status (July 25, 2025)
- ✅ **Complete Implementation**: Full Telegram bot with all requested features implemented
- ✅ **Force Subscription System**: Working channel subscription verification with Arabic UI
- ✅ **Pixabay Integration**: Complete API integration for photos, illustrations, vectors, videos, music, and GIFs
- ✅ **Search Navigation**: Fixed interactive result browsing with proper next/previous navigation
- ✅ **Admin Panel**: Complete button-based admin interface (no text commands)
- ✅ **Arabic Interface**: Complete Arabic language support throughout the bot
- ✅ **Bot Running**: Successfully deployed and running on Replit
- ✅ **Render Ready**: Configured for production deployment on Render platform

### Features Implemented
1. **User Flow**: Start command → Force subscription check → Main menu → Search functionality
2. **Search Types**: 6 different media types with type selection and filtering
3. **Result Navigation**: Fixed pagination through search results with proper navigation buttons
4. **Admin Panel**: Complete button-based admin interface with:
   - Statistics dashboard
   - Channel management (add/remove)
   - User management (ban/unban)
   - Broadcast messaging system
5. **Error Handling**: Proper error messages including the custom "كلماتك غريبة يا غلام" message
6. **Statistics Tracking**: User count, search count, and bot analytics

### Recent Updates (July 25, 2025)
- **Fixed Navigation**: Resolved issue where navigation buttons weren't updating search results
- **Admin Interface**: Replaced text commands with intuitive button-based admin panel
- **Render Deployment**: Added production-ready configuration for Render platform
- **Code Optimization**: Removed duplicate functions and improved error handling
- **Multi-Media Support**: Enhanced bot to display all media types (photos, videos, audio, GIFs)
- **Increased Results**: Updated search to return 100 results instead of 20
- **Media Navigation**: Added proper navigation support for videos and audio files

### Technical Implementation
- **Bot Token**: 8496475334:AAFVBYMsb_d_K80YkD06V3ZlcASS2jzV0uQ (configured)
- **Admin ID**: 7251748706 (configured)
- **Pixabay API**: 51444506-bffefcaf12816bd85a20222d1 (configured)
- **Library Version**: python-telegram-bot==20.8 (stable version for deployment)
- **Dependencies**: requests==2.32.4 for Pixabay API calls

### Deployment Ready
- All code contained in single file (main.py) as requested
- Ready for deployment on Render or similar platforms
- Environment variables configured for production use