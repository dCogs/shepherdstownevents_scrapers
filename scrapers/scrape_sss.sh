#!/bin/bash

# Store the current date in a variable
today_date=$(date +"%Y%m%d")
# Store the file prefix in a variable
file_prefix="sss"

# Define the project directory and virtual environment path
PROJECT_DIR="/Users/dan/shepherdstownevents/scrapers"
VENV_PATH="/Users/dan/shepherdstownevents/scrapers" # Or .venv or whatever name you used
PROGRAM_DIR="/Users/dan/shepherdstownevents/scrapers/${file_prefix}"

# Change to the project directory
cd "$PROJECT_DIR" || exit

# Activate the virtual environment
source .venv/bin/activate

# Go to the PVAS directory
cd "$PROGRAM_DIR" || exit

# Run your Python program
python ${file_prefix}_extractor.py

# Remove lines beginning with DTSTAMP:
grep -v DTSTAMP: "${file_prefix}_${today_date}.ics" > file1
grep -v DTSTAMP: "../scraped_files/sss.ics" > file2
if cmp -s file1 file2
then
    echo "Files are identical"
else
    echo "Files are different"
    cp "${file_prefix}_${today_date}.ics" "../scraped_files/sss.ics" 
fi

# Optional: Deactivate the environment when finished (if you want the shell to return to normal after execution)
deactivate
