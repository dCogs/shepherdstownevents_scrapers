#!/bin/zsh
# source ~/.zshrc
# echo "PATH="
# echo $PATH

echo "Parent script started."

# Pass each organization to the org_scraper script
# ./scrape.sh "4seasons"
./scrape.sh "library"
./scrape.sh "operahouse"
./scrape.sh "pvas"
./scrape.sh "shepinfo"

# Show the scraped_files directory
echo "Here are the scraped_files."
ls -l -lt scraped_files

