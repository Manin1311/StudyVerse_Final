import codecs

# Read the file
with codecs.open(r'd:\STUDYVERSE_FINAL\PROJECT D2\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line  3355 (index 3354)
lines[3354] = '        print(f"Heartbeat from {current_user.first_name} in {room_code}")\n'

# Write back
with codecs.open(r'd:\STUDYVERSE_FINAL\PROJECT D2\app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✓ Fixed syntax error in app.py line 3355")
