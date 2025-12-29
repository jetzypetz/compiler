#!/bin/bash

dir="ex/bxc_scripts_and_tests/tests/examples"

# Loop through all .bx files in the specified directory
for file in "$dir"/*.bx; do
    # Check if there are any .bx files
    if [ ! -f "$file" ]; then
        echo "No .bx files found in $dir"
        exit 0
    fi
    
    # Extract just the filename without path
    filename=$(basename "$file")
    
    echo "$filename:"
    
    echo "expected:"

    txt_file="${file%.bx}_output.txt"
    
    cat $txt_file

    echo "got:"

    # Run prog on the file
    python3 bxc.py "$file"
    
    # Run the generated executable (remove .bx extension and add .exe)
    exe_file="${file%.bx}.exe"
    if [ -f "$exe_file" ]; then
        ./"$exe_file"
    else
        echo "Warning: $exe_file not found"
    fi
    
    # Wait for user to press Enter
    read -p "Press Enter to continue..."
    
    # Remove .s and .exe files
    s_file="${file%.bx}.s"
    if [ -f "$s_file" ]; then
        rm "$s_file"
    fi
    
    if [ -f "$exe_file" ]; then
        rm "$exe_file"
    fi
done
