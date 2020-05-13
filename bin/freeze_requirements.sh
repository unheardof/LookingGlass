#!/bin/bash

if pip list | grep -E '^virtualenv .*$' > /dev/null 2> /dev/null; then
     echo 'virtualenv is installed; continuing'
else
    echo 'virtualenv is not installed; installing now'
    pip install virtualenv
fi

cd $(dirname "${BASH_SOURCE[0]}")

if ls | grep -E '^venv$' > /dev/null 2> /dev/null; then
    echo 'venv has already been created; continuing'
else
    echo 'venv directory does not exist; creating now'
    
    # Create new virtual environment
    virtualenv venv

    # Set Python version
    virtualenv -p $(which python3) venv
fi

source venv/bin/activate
pip freeze | grep -v 'pkg-resources' > requirements.txt
deactivate
