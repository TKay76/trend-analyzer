#!/bin/bash

# Enhanced script for complete daily music trend data collection
# This script runs all scrapers and UGC collection sequentially using the project's virtual environment.

# Define the python executable from the virtual environment
VENV_PYTHON="../test_env/bin/python3"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

echo "=========================================="
echo "🌅 Daily Complete Music Trend Collection"
echo "📅 Started at: $(date)"
echo "=========================================="

# Option 1: Run individual scrapers (legacy mode)
if [ "$1" = "legacy" ]; then
    echo "--- Starting TikTok Music Scraper ---"
    $VENV_PYTHON src/scrapers/tiktok_music_scraper.py
    
    if [ $? -ne 0 ]; then
        echo "❌ TikTok Scraper failed. Aborting."
        exit 1
    fi
    echo "✅ TikTok Music Scraper Finished"
    
    echo ""
    echo "--- Starting YouTube Music Scraper ---"
    $VENV_PYTHON src/scrapers/youtube_csv_scraper.py
    
    if [ $? -ne 0 ]; then
        echo "❌ YouTube Scraper failed."
        exit 1
    fi
    echo "✅ YouTube Music Scraper Finished"
    
    echo ""
    echo "--- Starting UGC Data Collection ---"
    echo "🎭 Collecting TikTok UGC data..."
    $VENV_PYTHON collect_all_tiktok_data.py
    
    echo "📺 Collecting YouTube UGC data..."
    $VENV_PYTHON collect_all_youtube_data.py
    
    echo "✅ All scraping tasks are complete."

# Option 2: Run complete daily collection (recommended)
else
    echo "🚀 Running Complete Daily Collection..."
    echo ""
    
    $VENV_PYTHON daily_complete_collection.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Complete daily collection finished successfully!"
    else
        echo ""
        echo "❌ Complete daily collection failed. Check logs for details."
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "📅 Finished at: $(date)"
echo "=========================================="