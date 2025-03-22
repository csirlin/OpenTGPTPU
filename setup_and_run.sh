#!/bin/bash
# Setup script for running the fuzzer with Python 3.8.18 and PyRTL 0.8.6

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
    echo "pyenv is not installed. Installing via brew..."
    brew install pyenv
fi

# Install Python 3.8.18 if not already installed
if ! pyenv versions | grep -q 3.8.18; then
    echo "Installing Python 3.8.18 via pyenv..."
    pyenv install 3.8.18
fi

# Set local Python version to 3.8.18
echo "Setting local Python version to 3.8.18..."
pyenv local 3.8.18

# Create and activate virtual environment
echo "Creating virtual environment..."
python -m venv env_py38
echo "Activating virtual environment..."
source env_py38/bin/activate

# Verify Python version
python_version=$(python --version)
echo "Current Python version: $python_version"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply PyRTL patch
echo "Applying PyRTL compatibility patch..."
python fix_pyrtl.py

# Run the fuzzer
echo "Running fuzzer.py..."
python fuzzer.py

# Deactivate the virtual environment
deactivate
echo "Done!" 