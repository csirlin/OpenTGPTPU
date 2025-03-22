#!/bin/bash
# Setup script for running the fuzzer with Python 3.8 and PyRTL 0.8.6 using Conda

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "conda is not available. Please install Anaconda or Miniconda."
    exit 1
fi

# Create a new conda environment with Python 3.8
ENV_NAME="py38_pyrtl"
echo "Creating conda environment '$ENV_NAME' with Python 3.8..."
conda create -y -n $ENV_NAME python=3.8

# Activate the environment
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate $ENV_NAME

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

# Deactivate the environment
conda deactivate
echo "Done!" 