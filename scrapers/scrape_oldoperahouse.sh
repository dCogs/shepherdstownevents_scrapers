#!/bin/bash

# Define the project directory and virtual environment path
PROJECT_DIR="/Users/dan/shepherdstownevents/scrapers"
VENV_PATH="/Users/dan/shepherdstownevents/scrapers" # Or .venv or whatever name you used
PROGRAM_DIR="/Users/dan/shepherdstownevents/scrapers/oldoperahouse"

# Change to the project directory
cd "$PROJECT_DIR" || exit

# Activate the virtual environment
source .venv/bin/activate

# Go to the PVAS directory
cd "$PROGRAM_DIR" || exit

# Run your Python program
python oldoperahouse_extractor.py

# Store the current date in a variable
today_date=$(date +"%Y%m%d")

cp "oldoperahouse_${today_date}.ics" "../scraped_files/oldoperahouse.ics" 

# Optional: Deactivate the environment when finished (if you want the shell to return to normal after execution)
deactivate
