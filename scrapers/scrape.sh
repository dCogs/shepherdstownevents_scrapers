#!/bin/zsh
# source ~/.zshrc
# echo $PATH
# Store the current date in a variable
today_date=$(date +"%Y%m%d")

# Store the file prefix in a variable
# file_prefix="sss"
file_prefix=$1
echo " "
echo " "
echo "The organization is: $1"

# Define the project directory and virtual environment path
PROJECT_DIR="/Users/dan/shepherdstownevents/scrapers"
# VENV_PATH="/Users/dan/shepherdstownevents/scrapers" # Or .venv or whatever name you used
ORG_DIR="/Users/dan/shepherdstownevents/scrapers/${file_prefix}"

# Change to the project directory
cd "$PROJECT_DIR" || exit
# Activate the virtual environment
source .venv/bin/activate
# Go to the org directory
cd "$ORG_DIR" || exit

# Run your Python program
python3 ${file_prefix}_extractor.py

# Remove lines beginning with DTSTAMP:
grep -v DTSTAMP: "${file_prefix}_${today_date}.ics" > file1
grep -v DTSTAMP: "../scraped_files/${file_prefix}.ics" > file2
if cmp -s file1 file2
then
    echo "Files are identical"
else
    echo "Files are different"
    cp "${file_prefix}_${today_date}.ics" "../scraped_files/${file_prefix}.ics" 
fi

# remove the temp file1 & file2
rm file1
rm file2

echo " "
echo " "

# Optional: Deactivate the environment when finished (if you want the shell to return to normal after execution)
deactivate
