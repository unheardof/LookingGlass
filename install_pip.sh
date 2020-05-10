#!/bin/bash
# From https://pip.pypa.io/en/stable/installing/

if [ $(type -P python3) ]; then
    echo 'Python 3 is installed; continuing'
else
    echo 'Python 3 is not installed; please install it before continuing'
    exit
fi

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
rm get-pip.py
