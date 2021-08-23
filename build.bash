#!/usr/bin/env bash

if [ -d build ]; then
  rm -rf build
fi

# Recreate build directory
mkdir -p build/function/ build/layer/

# Copy source files
echo "Copy source files"
cp -r ./main.py build/function/

# Pack python libraries
echo "Pack python libraries"
pip3 install -r requirements.txt -t build/layer/python

# Remove pycache in build directory
find build -type f | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm
