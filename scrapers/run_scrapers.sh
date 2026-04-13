#!/bin/zsh
# source ~/.zshrc
# echo "PATH="
# echo $PATH
echo "Parent script started."

# Call the first script and wait for it to finish
# ./org_scraper.sh "4seasons"
./org_scraper.sh "greenhill"
./org_scraper.sh "grow_yoga"
./org_scraper.sh "library"
./org_scraper.sh "fom"
./org_scraper.sh "ghost"
./org_scraper.sh "operahouse"
./org_scraper.sh "pvas"
./org_scraper.sh "scc"
./org_scraper.sh "shepinfo"
./org_scraper.sh "sss"
./org_scraper.sh "su"
./org_scraper.sh "sua"
./org_scraper.sh "sum"
./org_scraper.sh "sull"
./org_scraper.sh "trptc"
./org_scraper.sh "trw"

echo "Here are the scraped_files."
ls -l -lt scraped_files
