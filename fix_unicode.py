import sys

# Read the file
with open('verify_database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Unicode characters with ASCII equivalents
replacements = {
    '✓': '[OK]',
    '✗': '[X]',
    '⚠': '[!]',
}

for unicode_char, ascii_char in replacements.items():
    content = content.replace(unicode_char, ascii_char)

# Write back
with open('verify_database.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Unicode characters in verify_database.py")
