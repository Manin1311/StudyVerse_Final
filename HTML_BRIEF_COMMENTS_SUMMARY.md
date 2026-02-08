# HTML Template Comments - Brief Summary

## Objective
Add short, concise 1-2 line comments to HTML templates explaining main sections and functionality.

## Files Commented

### ✅ todos.html
**Comments Added:**
- Template inheritance explanation
- Header section purpose
- Task grouping logic (category-based hierarchy)
- Subtask rendering
- Uncategorized tasks (Inbox)
- Modal for task creation
- JavaScript functions (submit, search)

**Example Comments:**
```html
{# Extends base layout with sidebar and navigation #}
{% extends "layout.html" %}

{# Personal tasks grouped by category #}
<div id="personal-tasks-container">

{# Subtasks under each category #}
<div class="task-group">

{# Modal for creating new task groups with subtasks #}
<div id="addTaskModal" class="modal">

// Submit task group with all subtasks to backend
function submitTask() {

// Real-time search filter for tasks
document.addEventListener('DOMContentLoaded', () => {
```

### ✅ dashboard.html (Previously)
**Comments Added:**
- Template structure and inheritance
- Backend data flow
- Jinja2 variable explanations
- Active tasks widget
- Data sources from backend

## Comment Style Guide

### For Jinja2/HTML:
```html
{# Brief 1-2 line explanation #}
```

### For JavaScript:
```javascript
// Brief 1-2 line explanation
```

### What to Comment:
1. **Template inheritance** - Which layout is extended
2. **Major sections** - Purpose of each main div/section
3. **Backend connections** - Which variables come from backend
4. **JavaScript functions** - What each function does
5. **Modals/Forms** - Purpose and submission target

### What NOT to Comment:
- Every single line
- Obvious HTML structure
- Standard CSS classes
- Self-explanatory code

## Benefits
- **Quick understanding** for faculty review
- **Easy navigation** through template structure
- **Clear backend-frontend connections**
- **Maintainability** without overwhelming detail

## Status
✅ Short, concise comments added to key HTML files
✅ Focus on main sections and functionality
✅ No overwhelming documentation blocks
✅ Easy to read and understand

---

**Generated**: February 8, 2026  
**Project**: StudyVerse v2.0  
**Approach**: Brief, helpful comments (1-2 lines max)
