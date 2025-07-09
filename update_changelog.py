#!/usr/bin/env python3
"""
Update the changelog in replit.md with the portable app fixes
"""

changelog_entry = """- July 9, 2025. Portable app critical fixes - Fixed all deployment issues: switched from gunicorn to waitress server, updated requirements.txt with correct package versions, fixed Python embedded configuration, corrected static files paths to app/static/, resolved circular import issues between models and app, added comprehensive error handling and dependency checking, created proper package structure with __init__.py files, and enhanced setup.bat with better error handling and target installation paths"""

# Read current replit.md
with open('replit.md', 'r') as f:
    content = f.read()

# Find the changelog section and add the new entry
lines = content.splitlines()
new_lines = []
changelog_added = False

for line in lines:
    new_lines.append(line)
    # Add after the last changelog entry (before User Preferences)
    if line.startswith('- June 27, 2025. Portable Windows desktop app') and not changelog_added:
        new_lines.append(changelog_entry)
        changelog_added = True

# Write back
with open('replit.md', 'w') as f:
    f.write('\n'.join(new_lines))

print("✓ Updated replit.md changelog")