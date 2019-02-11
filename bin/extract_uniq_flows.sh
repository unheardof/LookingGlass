#!/bin/bash

# Taken from https://stackoverflow.com/questions/13492611/tcpdump-output-only-source-and-destination-addresses
tcpdump -nt -r $1 | grep -P -o '([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+).*? ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)' | grep -P -o '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | xargs -n 2 echo | sort | uniq
