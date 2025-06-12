#!/bin/bash

# Check for input file
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"
line_num=1

# Read file line by line
while IFS=$'\t' read -r f1 f2 _; do
    echo "Line $line_num - Field 1: $f1"
    echo "Line $line_num - Field 2: $f2"
    ((line_num++))
done < "$input_file"

