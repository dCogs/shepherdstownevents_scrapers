#!/bin/bash

# Define the project directory and virtual environment path
PROJECT_DIR="/Users/dan/shepherdstownevents/scrapers"
VENV_PATH="/Users/dan/shepherdstownevents/scrapers" # Or .venv or whatever name you used
PROGRAM_DIR="/Users/dan/shepherdstownevents/scrapers/library"

# Change to the project directory
cd "$PROJECT_DIR" || exit

# Activate the virtual environment
source .venv/bin/activate

# Go to the PVAS directory
cd "$PROGRAM_DIR" || exit

# Run your Python program
python library_extractor.py

# Store the current date in a variable
today_date=$(date +"%Y%m%d")

# Copy today's file to scraped_files
cp "library_${today_date}.ics" "../scraped_files/library.ics" 

# Optional: Deactivate the environment when finished (if you want the shell to return to normal after execution)
deactivate
