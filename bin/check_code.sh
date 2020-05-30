#!/bin/bash

# Navigate to the root project directory
cd $(dirname "${BASH_SOURCE[0]}")
cd ..

pwd
pip install --user bandit
bandit -r ./looking_glass
