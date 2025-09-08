import os
import sys
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Import your existing classes
from selenium_scraper import FighterOdds, Fight, SeleniumFightOddsScraper

class AutomatedSeleniumScraper(SeleniumFightOddsScraper):
    
    def setup_driver(self):
        """Setup Chrome WebDriver for GitHub Actions environment"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Use system Chrome in GitHub Actions
        chrome_bin = os.environ.get('CHROME_BIN')
        if chrome_bin:
            chrome_options.binary_location = chrome_bin
            
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
        
        try:
            if chromedriver_path:
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"Chrome WebDriver error: {e}")
            return None

def main():
    """Automated main function for GitHub Actions"""
    
    print("Running automated odds scraper...")
    
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        event_url = sys.argv[1]
    else:
        event_url = 'https://fightodds.io'
        print(f"Using default URL: {event_url}")
    
    scraper = AutomatedSeleniumScraper()
    fights = scraper.scrape_with_selenium(event_url)
    
    if fights:
        # Ensure data directory exists (relative to backend folder)
        os.makedirs('data', exist_ok=True)
        
        # Save to correct location
        fights_dict = [asdict(fight) for fight in fights]
        
        with open('data/fights.json', 'w') as f:
            json.dump(fights_dict, f, indent=2)
        
        print(f"Successfully scraped {len(fights)} fights")
        return True
    else:
        print("No fights scraped")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)