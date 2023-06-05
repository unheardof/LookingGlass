#!/bin/bash

# Navigate to the root project directory
cd $(dirname "${BASH_SOURCE[0]}")
cd ..

source venv/bin/activate
pytest
RESULT=$?
deactivate

exit $RESULT # Fail script if the tests failed
