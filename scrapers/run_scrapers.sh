#!/bin/zsh
# source ~/.zshrc
# echo "PATH="
# echo $PATH

echo "Parent script started."

# Pass each organization to the org_scraper script
# ./scrape.sh "4seasons"
./scrape.sh "anb"
./scrape.sh "fom"
./scrape.sh "ghost"
./scrape.sh "greenhill"
./scrape.sh "grow_yoga"
./scrape.sh "hfnhp"
./scrape.sh "library"
./scrape.sh "operahouse"
./scrape.sh "prbrewing"
./scrape.sh "pvas"
./scrape.sh "scc"
./scrape.sh "shepinfo"
./scrape.sh "sss"
./scrape.sh "su"
./scrape.sh "sua"
./scrape.sh "sum"
./scrape.sh "sull"
./scrape.sh "trptc"
./scrape.sh "trw"

# Show the scraped_files directory
echo "Here are the scraped_files."
ls -l -lt scraped_files

