#!/bin/bash

# Define the project directory and virtual environment path
PROJECT_DIR="/Users/dan/shepherdstownevents/scrapers"
VENV_PATH="/Users/dan/shepherdstownevents/scrapers" # Or .venv or whatever name you used
PROGRAM_DIR="/Users/dan/shepherdstownevents/scrapers/fom"

# Change to the project directory
cd "$PROJECT_DIR" || exit

# Activate the virtual environment
source .venv/bin/activate

# Go to the PVAS directory
cd "$PROGRAM_DIR" || exit

# Run your Python program
python fom_extractor.py

# Store the current date in a variable
today_date=$(date +"%Y%m%d")

cp "fom_${today_date}.ics" "../scraped_files/fom.ics" 

# Optional: Deactivate the environment when finished (if you want the shell to return to normal after execution)
deactivate
