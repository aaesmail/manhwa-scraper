# Manhwa-Scraper
A python script to go through links in manhwa favorites folder in Chrome and reports what manhwa has new updates not yet read

- This is made to only work on windows 10 machines.
- This script only works with Server Side Rendered pages.
- It reports which pages are dynamically rendered.
- The user has to manually replace dynamically rendered pages with statically rendered ones in the favorites Manhwa folder.

## How to run:
  - Have a folder named Manhwa in your bookmarks that contains Manhwa pages
  - Have python installed on your machine
  - Open a terminal in script location
  - Run `pip install -r requirements.txt`
  - Make sure chrome is closed (To not deny the DB connection)
  - Run `py Manhwa.py`
