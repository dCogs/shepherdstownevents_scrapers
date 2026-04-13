#find . -type f -name "*.ics"  -not -path "./scraped_files/*"
find . -type f -name "*.ics"  -not -path "./scraped_files/*" -delete
find . -type f -name "*.ics"
