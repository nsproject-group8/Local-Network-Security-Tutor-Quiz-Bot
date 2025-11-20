#!/usr/bin/env python3
"""Fix all backend imports to use relative imports instead of absolute backend. imports"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Replace 'from backend.' with 'from ' in Python files"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace 'from backend.' with 'from '
    content = re.sub(r'from backend\.', 'from ', content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Fixed: {file_path}")
        return True
    return False

def main():
    backend_dir = Path(__file__).parent / 'backend'
    
    # Find all Python files in backend directory
    python_files = list(backend_dir.rglob('*.py'))
    
    fixed_count = 0
    for py_file in python_files:
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\n✅ Fixed imports in {fixed_count} files")

if __name__ == '__main__':
    main()
