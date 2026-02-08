"""
Script to add comprehensive comments to the StudyVerse codebase.
This script adds detailed comments explaining the purpose, flow, and concepts used in each file.
"""

# List of files and the comments to add to each section
# This will serve as a reference for manual commenting

BACKEND_COMMENTS = {
    "app.py": {
        "database_models": """
# ============================================================================
# DATABASE MODELS (ORM - Object Relational Mapping)
# ============================================================================
# These classes represent database tables using SQLAlchemy ORM
# Each class maps to a table, and each attribute maps to a column
# Benefits: Type safety, relationship management, query abstraction
""",
        "user_model": """
class User(UserMixin, db.Model):
    \"\"\"
    User Model - Core entity representing a StudyVerse user
    
    Inherits from:
    - UserMixin: Provides Flask-Login integration (is_authenticated, is_active, etc.)
    - db.Model: SQLAlchemy base class for ORM functionality
    
    Fields:
    - Authentication: email, password_hash, google_id
    - Profile: first_name, last_name, profile_image, cover_image, about_me
    - Gamification: total_xp, level, current_streak, longest_streak
    - Privacy: is_public_profile, last_seen
    
    Properties (Computed fields):
    - rank_info: Returns rank details based on current level
    - active_frame_color: Returns color of equipped profile frame
    
    Methods:
    - get_avatar(): Generates avatar URL (uploaded image or initials)
    - to_dict(): Serializes user data for JSON responses
    \"\"\"
""",
        "gamification_service": """
class GamificationService:
    \"\"\"
    Service Layer for Gamification Logic (OOP Design Pattern)
    
    Responsibilities:
    1. XP Management: Add/deduct experience points
    2. Level Calculation: Convert XP to levels (500 XP per level)
    3. Rank Assignment: Map levels to ranks (Bronze to Grandmaster)
    4. Badge Awards: Check and award achievement badges
    5. Streak Tracking: Daily activity streak management
    
    Design Pattern: Service Layer Pattern
    - Separates business logic from routes and models
    - Provides reusable methods for gamification features
    - Centralizes complex calculations and rules
    
    Key Algorithms:
    - Level formula: level = floor(total_xp / 500) + 1
    - Rank lookup: O(1) dictionary lookup by level range
    - Daily cap: Prevents XP farming (max 500 XP/day from focus)
    
    Power-up Integration:
    - XP Multipliers: Boost XP gains (2x, 3x)
    - Time Multipliers: Double focus session rewards
    - XP Protection: Prevent XP loss in battles
    \"\"\"
"""
    },
    
    "email_service.py": {
        "header": """
\"\"\"
Email Service Module
====================

Purpose: Handle all email-related functionality for StudyVerse

Features:
1. Welcome emails for new users
2. Task reminder emails (due date notifications)
3. Email configuration using Flask-Mail

Technology: Flask-Mail with Gmail SMTP
Configuration: Uses environment variables for security
\"\"\"
"""
    },
    
    "migrate_pg_syllabus.py": {
        "header": """
\"\"\"
PostgreSQL Syllabus Migration Script
=====================================

Purpose: Migrate syllabus data from SQLite to PostgreSQL

Use Case: When deploying to production (Render.com)
- Development uses SQLite
- Production uses PostgreSQL
- This script transfers existing syllabus documents

Process:
1. Connect to both databases
2. Read syllabus records from SQLite
3. Insert into PostgreSQL
4. Handle duplicates and errors
\"\"\"
"""
    }
}

FRONTEND_COMMENTS = {
    "static/js/main.js": """
/**
 * Main JavaScript File - Core UI Functionality
 * ============================================
 * 
 * Purpose: Handle global UI interactions and theme management
 * 
 * Features:
 * 1. Theme Toggle: Switch between light and dark modes
 * 2. Sidebar Navigation: Mobile-responsive menu
 * 3. Notification System: Toast messages for user feedback
 * 4. Avatar Management: Profile picture updates
 * 
 * Design Pattern: Event-driven programming
 * - DOM event listeners for user interactions
 * - LocalStorage for persistent theme preference
 */
""",
    
    "static/js/battle.js": """
/**
 * Battle Mode JavaScript - Competitive Quiz System
 * =================================================
 * 
 * Purpose: Real-time quiz battles between users
 * 
 * Flow:
 * 1. Matchmaking: Find opponent or create battle
 * 2. Question Display: Show AI-generated quiz questions
 * 3. Answer Submission: Track correct/incorrect answers
 * 4. Score Calculation: Real-time score updates
 * 5. Result Display: Winner determination and XP rewards
 * 
 * Technologies:
 * - Socket.IO: Real-time communication
 * - Fetch API: HTTP requests to backend
 * - DOM Manipulation: Dynamic UI updates
 * 
 * Data Structures:
 * - Arrays: Store questions and answers
 * - Objects: Battle state management
 * 
 * Algorithms:
 * - Timer: Countdown for each question
 * - Score calculation: Points based on speed and accuracy
 */
""",
    
    "static/js/pomodoro.js": """
/**
 * Pomodoro Timer - Focus Session Management
 * ==========================================
 * 
 * Purpose: Implement Pomodoro Technique for productivity
 * 
 * Pomodoro Technique:
 * - 25-minute focus sessions
 * - 5-minute short breaks
 * - 15-minute long breaks (after 4 sessions)
 * 
 * Features:
 * 1. Customizable Timer: User-defined session lengths
 * 2. XP Rewards: Earn XP for completed focus sessions
 * 3. Session History: Track productivity over time
 * 4. Audio Notifications: Sound alerts for session end
 * 5. Zen Mode: Distraction-free full-screen mode
 * 
 * Data Structures:
 * - State Object: Current timer state (running, paused, stopped)
 * - Queue: Manage session sequence (focus → break → focus)
 * 
 * Algorithms:
 * - Countdown Timer: setInterval for 1-second updates
 * - XP Calculation: Duration-based rewards (1 XP per minute)
 */
""",
    
    "static/js/chat.js": """
/**
 * AI Chat Assistant - Context-Aware Study Helper
 * ===============================================
 * 
 * Purpose: Provide AI-powered study assistance using Google Gemini
 * 
 * Features:
 * 1. Context Awareness: Uses uploaded syllabus for relevant answers
 * 2. Chat History: Maintains conversation context
 * 3. Markdown Rendering: Formats AI responses
 * 4. Code Highlighting: Syntax highlighting for code snippets
 * 
 * Flow:
 * 1. User sends message
 * 2. Frontend sends to backend via fetch
 * 3. Backend queries Gemini API with syllabus context
 * 4. AI response streamed back to frontend
 * 5. Message displayed in chat interface
 * 
 * Technologies:
 * - Fetch API: Async HTTP requests
 * - Markdown-it: Markdown parsing
 * - Highlight.js: Code syntax highlighting
 */
""",
    
    "static/js/dashboard_calendar.js": """
/**
 * Dashboard Calendar - Event and Task Management
 * ===============================================
 * 
 * Purpose: Integrated calendar view with tasks and events
 * 
 * Features:
 * 1. Calendar Display: Month view with navigation
 * 2. Event Creation: Add events with date and time
 * 3. Task Integration: Show tasks on due dates
 * 4. Reminders: Email notifications for upcoming events
 * 
 * Data Structures:
 * - 2D Array: Calendar grid (weeks × days)
 * - Hash Map: Quick lookup of events by date
 * 
 * Algorithms:
 * - Calendar Generation: Calculate days in month, first day of week
 * - Date Comparison: Sort and filter events by date
 */
"""
}

TEMPLATE_COMMENTS = {
    "templates/layout.html": """
<!--
Layout Template - Base Template for All Pages
==============================================

Purpose: Provide consistent structure across all pages

Features:
1. Navigation Bar: Logo, menu items, user profile
2. Sidebar: Quick access to features
3. Footer: Links and copyright
4. Theme System: Dark/light mode toggle
5. Notification Area: Toast messages

Jinja2 Blocks:
- title: Page-specific title
- extra_css: Additional stylesheets
- content: Main page content
- extra_js: Additional JavaScript files

Design Pattern: Template Inheritance
- Child templates extend this base
- Override blocks for customization
-->
""",
    
    "templates/dashboard.html": """
<!--
Dashboard - Main User Interface
================================

Purpose: Central hub for all StudyVerse features

Sections:
1. Stats Overview: XP, level, rank, streak
2. Quick Actions: Start focus, create task, take quiz
3. Recent Activity: Latest tasks and achievements
4. Calendar Widget: Upcoming events
5. Leaderboard Preview: Top users

Data Flow:
1. Backend fetches user stats from database
2. Jinja2 renders data into HTML
3. JavaScript adds interactivity
4. Socket.IO provides real-time updates

Gamification Elements:
- Progress bars for level advancement
- Badge display
- Streak counter with fire animation
-->
""",
    
    "templates/quiz.html": """
<!--
Quiz System - AI-Generated Assessments
=======================================

Purpose: Test knowledge with AI-generated questions

Flow:
1. User clicks \"Start Quiz\"
2. Backend generates questions using Gemini API
3. Questions displayed one at a time
4. User selects answer
5. Immediate feedback (correct/incorrect)
6. Final score and XP reward

Question Types:
- Multiple Choice: 4 options, 1 correct
- True/False: Binary choice
- Fill in the Blank: Text input

AI Integration:
- Gemini API generates questions from syllabus
- Context-aware difficulty adjustment
- Varied question formats
-->
"""
}

print("Comment Reference Guide Created!")
print("\\nThis file contains structured comments for all major files.")
print("Use this as a reference to add comments to the codebase.")
