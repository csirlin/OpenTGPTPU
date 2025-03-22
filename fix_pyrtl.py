#!/usr/bin/env python
"""
Fix script for PyRTL 0.8.6 compatibility with Python 3.8+

This script patches PyRTL's simulation.py to use collections.abc.Mapping
instead of collections.Mapping, which was moved in Python 3.8+.

Run this after installing PyRTL but before running your main code.
"""
import os
import sys
import site

def fix_pyrtl_collections():
    """Find and patch PyRTL simulation.py file."""
    # Find the site-packages directory for the current Python environment
    site_packages = site.getsitepackages()[0]
    pyrtl_sim_path = os.path.join(site_packages, 'pyrtl', 'simulation.py')
    
    if not os.path.exists(pyrtl_sim_path):
        print(f"PyRTL simulation.py not found at {pyrtl_sim_path}")
        return False
    
    # Read file content
    with open(pyrtl_sim_path, 'r') as f:
        content = f.read()
    
    # Make the replacement
    if 'collections.Mapping' in content:
        content = content.replace('collections.Mapping', 'collections.abc.Mapping')
        content = content.replace('import collections', 'import collections.abc\nimport collections')
        
        # Write back the patched file
        with open(pyrtl_sim_path, 'w') as f:
            f.write(content)
        
        print(f"Successfully patched {pyrtl_sim_path}")
        return True
    else:
        print("The collections.Mapping pattern was not found. File might already be patched.")
        return False

if __name__ == "__main__":
    if fix_pyrtl_collections():
        print("PyRTL patch applied successfully!")
    else:
        print("PyRTL patch not applied.") 