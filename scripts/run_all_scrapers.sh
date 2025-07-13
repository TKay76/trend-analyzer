#!/bin/bash

# This script runs all scrapers sequentially using the project's virtual environment.

# Define the python executable from the virtual environment
VENV_PYTHON="venv/bin/python3"

echo "--- Starting TikTok Scraper ---"
$VENV_PYTHON tiktok_music_scraper.py

# Check if the first script was successful before proceeding
if [ $? -ne 0 ]; then
    echo "TikTok Scraper failed. Aborting."
    exit 1
fi

echo "--- TikTok Scraper Finished ---"

echo ""

echo "--- Starting YouTube Scraper ---"
$VENV_PYTHON youtube_music_scraper.py

if [ $? -ne 0 ]; then
    echo "YouTube Scraper failed."
    exit 1
fi

echo "--- YouTube Scraper Finished ---"

echo ""
echo "All scraping tasks are complete."