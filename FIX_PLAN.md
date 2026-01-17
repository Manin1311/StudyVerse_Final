# StudyVerse Bug Fix Plan

## Issues to Fix

### 1. ByteBattle - Users Getting Kicked Out
**Problem**: After 1 minute, users get kicked out, other players not getting requests
**Root Cause**: 
- Session timeout/connection issues
- Join request not broadcasting properly
- No heartbeat/keep-alive mechanism

**Fix**:
- Add proper room persistence
- Fix join request notification broadcasting
- Add connection heartbeat

### 2. WhiteBoard - Drawings Not Syncing
**Problem**: What user draws, friend can't see
**Root Cause**: Socket emit using `include_self=False` which might not broadcast correctly
**Fix**:
- Change whiteboard socket handlers to use `broadcast=True`
- Ensure proper room joining
- Add debug logging

### 3. Email - Not Sending for New Users
**Problem**: Email was working at start but now not going from account for new login people
**Root Cause**: Email service exists but not being called on user registration
**Fix**:
- Add send_welcome_email call to user creation flow
- Verify Gmail App Password (16-digit) is correct
- Add error logging

### 4. Chat - Needs Refresh to Send
**Problem**: Messages need page refresh to appear
**Root Cause**: Real-time socket events not properly configured
**Fix**:
- Fix socket event handlers for instant delivery
- Add proper room management

### 5. Notification System
**Problem**: No notification bell for requests
**Root Cause**: Feature doesn't exist yet
**Fix**: 
- Add notification Icon to layout 
- Create notification system with Socket.IO
- Add database table for notifications
- Real-time push notifications

## Implementation Order
1. WhiteBoard (simplest fix)
2. Email Service (important for users)
3. Chat real-time (important for UX)
4. ByteBattle persistence
5. Notification System (new feature)

