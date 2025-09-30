# Lucifer Facebook Tool Suite

A comprehensive Facebook automation and management platform with advanced features and security.

## Features

### 🎨 Welcome Experience
- Animated welcome page with floating particles
- Professional dark theme with red accent colors
- Auto-redirect to login after 10 seconds

### 🔐 Security & Access Control
- User registration with unique access keys
- Admin approval system for new users
- Session management for secure access
- SQLite database for user management

### 🛠️ Core Tools

#### 1. Token Checker
- Validate Facebook access tokens
- Display user information for valid tokens
- Error handling for invalid tokens

#### 2. Post Viewer
- View all Facebook posts from any profile
- Display post details including likes and comments
- Support for custom user IDs

#### 3. Post Commenter
- Automatically comment on Facebook posts
- Simple interface for quick commenting
- Real-time feedback on comment status

#### 4. Group UID Fetcher
- Extract UIDs from Messenger groups
- Display group names and IDs in a table
- Based on Facebook Graph API

#### 5. Multi Convo
- Send messages to multiple conversations
- Support for multiple tokens and messages
- Task management with stop functionality
- File upload for tokens and messages

#### 6. Uptime Monitor
- Real-time system uptime tracking
- Target: 100 days non-stop operation
- System status monitoring
- Auto-refresh functionality

### 🎨 Visual Elements
- Logo gallery with hover effects
- Animated UI components
- Professional card-based layout
- Responsive design for all devices

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```

## Deployment

This application is ready for deployment on platforms like:
- Render.com
- Heroku
- Railway
- Any Python hosting service

## Usage

1. Visit the welcome page
2. Register for a new account
3. Wait for admin approval
4. Login with your access key
5. Access all tools from the dashboard

## Admin Approval

New users require admin approval before accessing tools. The approval system is handled by a separate admin panel application.

## Security Features

- Session-based authentication
- Database-stored user credentials
- Access key generation
- Admin approval workflow

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **APIs**: Facebook Graph API
- **Deployment**: Ready for cloud platforms

## Author

Created by Lucifer - Ultimate Facebook Automation Suite
