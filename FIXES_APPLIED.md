# Text Visibility & UI Fixes

I have addressed the issues highlighted in the user's images regarding text visibility and the "broken" level display, and applied broad improvements to text contrast.

## 1. Syllabus Page Visibility
- **Issue**: The filename text "Uploaded: Introduction_to_Biology.pdf" was barely visible against the dark background.
- **Fix**: Updated `templates/syllabus.html` to change the text color from generic foreground to `var(--accent-green)`. This makes the filename pop out clearly.

## 2. Topic Completion Visibility "HII"
- **Issue**: In the syllabus visual roadmap, completed topics (like "HII") had text that was hard to read (likely dark grey strikethrough on dark grey background).
- **Fix**: Updated `static/css/style.css` for `.subtopic-item.completed span`. Changed color from `--text-muted` to `--text-secondary`, ensuring the strikethrough text is legible.

## 3. Sidebar Level Overflow "Lvl 999935"
- **Issue**: The user has an extremely high level (999935), causing the text "Lvl 999935" to overflow its container.
- **Fix**: Modified `templates/layout.html` to constrain the level text width with `max-width: 60px` and `text-overflow: ellipsis`.
    - **Result**: "Lvl 999935" will now truncate (e.g., "Lvl 99...") gracefully, preserving the layout.

## 4. Broad Text Visibility Improvements
- **Global Secondary Text**: Updated `--text-secondary` from `#a1a1aa` (Zinc-400) to `#d4d4d8` (Zinc-300).
- **Global Muted Text**: Updated `--text-muted` from `#52525b` (Zinc-600) to `#a1a1aa` (Zinc-400) in Dark Mode. This significantly improves readability for timestamps, placeholders, and inactive text across the entire application.
    - Also adjusted Light Mode muted text from `#94a3b8` to `#64748b` for better contrast.
- **Badge Visibility**: Updated `.badge-low` (used for tags like #coding) from `#94a3b8` to `#cbd5e1` (Zinc-200) to make "low priority" tags stand out more clearly against dark backgrounds.

These changes ensure that text is consistently legible throughout the application, addressing both the specific reported issues and general readability.
