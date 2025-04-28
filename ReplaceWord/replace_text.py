import re
from pathlib import Path

def replace_in_file(filepath, search, replace):
    """Single file replacement"""
    with open (filepath, 'r', encoding = 'utf-8') as f:
        content = f.read()

        new_content = re.sub(search, replace, content)

        if new_content != content:
            with open(filepath, 'w', encoding = 'utf-8') as f:
                f.write(new_content)
            print(f"Replaced: {filepath}")

# test: modify all files below this folder
replace_in_file("test.txt", "old_word", "new_word")