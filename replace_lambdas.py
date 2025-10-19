#!/usr/bin/env python3
"""
Replace lambda function definitions with module-level function references.
"""

import re

def replace_lambdas(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern 1: func_a = lambda: None
    content = re.sub(r'\s+func_a = lambda: None\n', '', content)
    
    # Pattern 2: func_b = lambda: None  
    content = re.sub(r'\s+func_b = lambda: None\n', '', content)
    
    # Pattern 3: func_a = lambda v: v
    content = re.sub(r'\s+func_a = lambda v: v\n', '', content)
    
    # Pattern 4: func_b = lambda v: v
    content = re.sub(r'\s+func_b = lambda v: v\n', '', content)
    
    # Pattern 5: Remove extra blank lines left behind
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Replaced lambdas in {filepath}")

if __name__ == '__main__':
    replace_lambdas('tests/test_edges.py')
