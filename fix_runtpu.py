#!/usr/bin/env python
"""
Fix script for PyRTL 0.8.6 and runtpu.py compatibility with Python 3.8+

This script:
1. Patches PyRTL's simulation.py to use collections.abc.Mapping
2. Fixes any other common compatibility issues with runtpu.py

Run this after installing PyRTL but before running your main code.
"""
import os
import sys
import site
import shutil

def fix_pyrtl_collections():
    """Find and patch PyRTL simulation.py file to fix collections.Mapping."""
    # Find the site-packages directory for the current Python environment
    site_packages = site.getsitepackages()[0]
    pyrtl_sim_path = os.path.join(site_packages, 'pyrtl', 'simulation.py')
    
    if not os.path.exists(pyrtl_sim_path):
        print(f"PyRTL simulation.py not found at {pyrtl_sim_path}")
        return False
    
    # Create backup
    backup_path = pyrtl_sim_path + '.bak'
    if not os.path.exists(backup_path):
        shutil.copy2(pyrtl_sim_path, backup_path)
        print(f"Created backup at {backup_path}")
    
    # Read file content
    with open(pyrtl_sim_path, 'r') as f:
        content = f.read()
    
    # Make all needed replacements
    patches_applied = 0
    
    # Fix collections.Mapping
    if 'collections.Mapping' in content:
        content = content.replace('collections.Mapping', 'collections.abc.Mapping')
        content = content.replace('import collections', 'import collections.abc\nimport collections')
        patches_applied += 1
    
    # Fix collections.MutableMapping if present
    if 'collections.MutableMapping' in content:
        content = content.replace('collections.MutableMapping', 'collections.abc.MutableMapping')
        patches_applied += 1
    
    # Write back the patched file if changes were made
    if patches_applied > 0:
        with open(pyrtl_sim_path, 'w') as f:
            f.write(content)
        print(f"Applied {patches_applied} patches to {pyrtl_sim_path}")
        return True
    else:
        print("No patches needed for PyRTL simulation.py")
        return False

def fix_runtpu():
    """
    Check and fix known issues in runtpu.py
    """
    # Path to runtpu.py
    runtpu_path = 'runtpu.py'
    
    if not os.path.exists(runtpu_path):
        print(f"runtpu.py not found at {runtpu_path}")
        return False
    
    # Create backup
    backup_path = runtpu_path + '.bak'
    if not os.path.exists(backup_path):
        shutil.copy2(runtpu_path, backup_path)
        print(f"Created backup at {backup_path}")
    
    # Read file content
    with open(runtpu_path, 'r') as f:
        content = f.read()
    
    # Fix common issues (add more as needed)
    patches_applied = 0
    
    # Add any specific fixes for runtpu.py here
    # For example, if runtpu is using pickle with Python 2 syntax:
    if 'import cPickle' in content:
        content = content.replace('import cPickle', 'import pickle as cPickle')
        patches_applied += 1
    
    # Write back the patched file if changes were made
    if patches_applied > 0:
        with open(runtpu_path, 'w') as f:
            f.write(content)
        print(f"Applied {patches_applied} patches to {runtpu_path}")
        return True
    else:
        print("No patches needed for runtpu.py")
        return False

def check_error_logs():
    """Check error logs to find common patterns"""
    error_dir = os.path.join('fuzz_test_dir', 'errors', 'runtpu')
    if not os.path.exists(error_dir):
        print(f"Error directory {error_dir} not found")
        return
    
    error_files = [os.path.join(error_dir, f) for f in os.listdir(error_dir) 
                  if os.path.isfile(os.path.join(error_dir, f))]
    
    if not error_files:
        print("No error files found to analyze")
        return
    
    print(f"Found {len(error_files)} error logs to analyze")
    
    # Check first error file for debugging
    if error_files:
        with open(error_files[0], 'r') as f:
            error_content = f.read()
            print("\n--- Sample error log content ---")
            print(error_content[:500] + "..." if len(error_content) > 500 else error_content)
            print("-------------------------------\n")

if __name__ == "__main__":
    pyrtl_fixed = fix_pyrtl_collections()
    runtpu_fixed = fix_runtpu()
    
    if pyrtl_fixed or runtpu_fixed:
        print("Applied fixes successfully!")
    else:
        print("No fixes were needed or applied.")
    
    # Check error logs to diagnose issues
    check_error_logs() 