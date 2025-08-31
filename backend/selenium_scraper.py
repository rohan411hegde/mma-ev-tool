from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class FighterOdds:
    fighter_name: str
    odds: int
    book: str
    
@dataclass  
class Fight:
    fighter1: str
    fighter2: str
    event_name: str
    event_date: str
    weight_class: str
    odds_data: List[FighterOdds]
    scraped_at: str

class SeleniumFightOddsScraper:
    def __init__(self):
        self.target_books = {
            'Pinnacle': 'Pinnacle',
            'BetOnline': 'BetOnline', 
            'Circa': 'Circa Sports',
            'DraftKings': 'DraftKings',
            'FanDuel': 'FanDuel',
            'Bet365': 'Bet365'
        }
    
    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"❌ Chrome WebDriver error: {e}")
            print("💡 You need to install ChromeDriver:")
            print("   brew install chromedriver")
            print("   or download from: https://chromedriver.chromium.org/")
            return None
    
    def scrape_with_selenium(self, event_url: str) -> List[Fight]:
        """Scrape using Selenium to handle JavaScript"""
        
        driver = self.setup_driver()
        if not driver:
            return []
        
        try:
            print(f"🚀 Loading page with Selenium: {event_url}")
            driver.get(event_url)
            
            # Wait for page to load
            print("⏳ Waiting for content to load...")
            time.sleep(5)  # Give JavaScript time to load
            
            # Try to wait for specific elements that indicate the odds have loaded
            try:
                # Wait for table or odds elements to appear
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                print("✅ Table elements loaded")
            except:
                print("⚠️ No table found, but continuing...")
            
            # Get the fully rendered HTML
            html = driver.page_source
            
            # Save for debugging
            with open('../data/selenium_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"💾 Saved Selenium HTML ({len(html)} chars)")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract fights from the rendered HTML
            fights = self.extract_fights_from_rendered_html(soup)
            
            return fights
            
        except Exception as e:
            print(f"❌ Selenium scraping error: {e}")
            return []
        
        finally:
            driver.quit()
    
    def extract_fights_from_rendered_html(self, soup) -> List[Fight]:
        """Extract fights from fully rendered HTML - DYNAMIC VERSION"""
        
        print("🔍 Analyzing rendered HTML structure...")
        
        # Save full HTML for debugging
        with open('../data/full_rendered.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        # Strategy 1: Look for the main odds table
        fights = self.extract_from_odds_table(soup)
        if fights:
            return fights
        
        # Strategy 2: Look for CSS grid/flex layouts (modern approach)
        fights = self.extract_from_css_layout(soup)
        if fights:
            return fights
        
        # Strategy 3: Look for JavaScript-generated content patterns
        fights = self.extract_from_js_content(soup)
        if fights:
            return fights
        
        print("⚠️ Could not extract fights automatically")
        return []
    
    def extract_from_odds_table(self, soup) -> List[Fight]:
        """Extract from traditional HTML table structure"""
        
        print("📊 Looking for HTML table structure...")
        
        tables = soup.find_all('table')
        if not tables:
            print("   No tables found")
            return []
        
        print(f"   Found {len(tables)} table(s)")
        
        # Find the main odds table (usually the largest one with the most rows)
        main_table = max(tables, key=lambda t: len(t.find_all('tr')))
        rows = main_table.find_all('tr')
        
        print(f"   Main table has {len(rows)} rows")
        
        if len(rows) < 5:  # Need at least header + a few fighter rows
            print("   Table too small, likely not the odds table")
            return []
        
        # Extract header row to map columns to sportsbooks
        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        print(f"   Headers: {headers[:10]}...")  # Show first 10
        
        # Map column indices to sportsbooks
        book_columns = {}
        for i, header in enumerate(headers):
            header_lower = header.lower()
            for book_key, book_name in self.target_books.items():
                if book_key.lower() in header_lower:
                    book_columns[i] = book_name
                    break
        
        print(f"   Found books in columns: {book_columns}")
        
        if len(book_columns) < 2:
            print("   Not enough sportsbook columns found")
            return []
        
        # Extract fighter data from remaining rows
        fighter_odds_list = []
        
        for row_idx, row in enumerate(rows[1:], 1):  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) < max(book_columns.keys()) + 1:
                continue
            
            # First cell should be fighter name
            fighter_cell = cells[0]
            fighter_name = fighter_cell.get_text(strip=True)
            
            # Skip if doesn't look like a fighter name
            if not self.is_valid_fighter_name(fighter_name):
                continue
            
            print(f"   Processing fighter: {fighter_name}")
            
            # Extract odds for each sportsbook
            fighter_odds = []
            for col_idx, book_name in book_columns.items():
                if col_idx < len(cells):
                    odds_cell = cells[col_idx]
                    odds_text = odds_cell.get_text(strip=True)
                    odds_value = self.parse_american_odds(odds_text)
                    
                    if odds_value is not None:
                        fighter_odds.append(FighterOdds(
                            fighter_name=fighter_name,
                            odds=odds_value,
                            book=book_name
                        ))
            
            if fighter_odds:
                fighter_odds_list.extend(fighter_odds)
        
        print(f"   Extracted odds for {len(set(odd.fighter_name for odd in fighter_odds_list))} fighters")
        
        # Group fighters into fights
        if len(fighter_odds_list) >= 4:  # Need at least 2 fighters with 2 books each
            return self.group_fighters_into_fights(fighter_odds_list)
        
        return []
    
    def extract_from_css_layout(self, soup) -> List[Fight]:
        """Extract from CSS grid/flexbox layouts (modern sites)"""
        
        print("🎨 Looking for CSS layout structure...")
        
        # Look for common CSS patterns for odds displays
        selectors_to_try = [
            '.fighter-row',
            '.odds-row', 
            '.matchup',
            '.fight-card',
            '[class*="fighter"]',
            '[class*="odds"]',
            '[class*="matchup"]'
        ]
        
        for selector in selectors_to_try:
            elements = soup.select(selector)
            if elements:
                print(f"   Found {len(elements)} elements with selector: {selector}")
                # Could implement parsing logic here
        
        return []
    
    def extract_from_js_content(self, soup) -> List[Fight]:
        """Extract from JavaScript-generated content patterns"""
        
        print("🔧 Looking for JavaScript-generated patterns...")
        
        # Look for script tags that might contain JSON data
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                script_content = script.string
                
                # Look for JSON data patterns
                if 'fighter' in script_content.lower() and ('odds' in script_content.lower() or 'line' in script_content.lower()):
                    print("   Found script with fighter/odds data")
                    # Could implement JSON parsing here
                    
                # Look for variable assignments with odds data
                if re.search(r'var\s+\w+\s*=\s*\{.*fighter.*\}', script_content, re.IGNORECASE):
                    print("   Found JavaScript variable with fighter data")
        
        return []
    
    def is_valid_fighter_name(self, name: str) -> bool:
        """Enhanced fighter name validation"""
        
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Must contain letters
        if not re.search(r'[A-Za-z]', name):
            return False
        
        # Skip obvious non-names
        skip_patterns = [
            r'^\d+$',  # Just numbers
            r'^[+-]\d+$',  # Odds format
            r'^\$',  # Prices
            r'^(odds|fighter|fighters|book|sportsbook|total|vs)$',  # Common headers
            r'^\W+$'  # Only special characters
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, name.lower().strip()):
                return False
        
        # Should look like a name (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[A-Za-z\s'\-\.]+$", name):
            return False
        
        # Should have at least one space (first name + last name)
        if ' ' not in name.strip():
            return False
        
        return True
    
    def parse_american_odds(self, odds_text: str) -> Optional[int]:
        """Enhanced American odds parsing"""
        
        if not odds_text:
            return None
        
        # Clean the text
        clean_text = odds_text.strip()
        
        # Remove common prefixes/suffixes
        clean_text = re.sub(r'[^\d\+\-]', '', clean_text)
        
        # Match American odds patterns
        patterns = [
            r'^([+-])(\d+)$',  # +150, -200
            r'^(\d+)$'  # 150 (assume positive)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, clean_text)
            if match:
                if len(match.groups()) == 2:
                    sign, number = match.groups()
                    odds_value = int(number)
                    return odds_value if sign == '+' else -odds_value
                else:
                    # Just a number, assume positive
                    return int(match.group(1))
        
        return None
    
    def group_fighters_into_fights(self, fighter_odds_list: List[FighterOdds]) -> List[Fight]:
        """Group individual fighter odds into fight matchups"""
        
        # Group by fighter name
        fighters_dict = {}
        for odds in fighter_odds_list:
            fighter = odds.fighter_name
            if fighter not in fighters_dict:
                fighters_dict[fighter] = []
            fighters_dict[fighter].append(odds)
        
        fighter_names = list(fighters_dict.keys())
        print(f"   Grouping {len(fighter_names)} fighters into fights")
        
        fights = []
        used_fighters = set()
        
        # Try to intelligently pair fighters
        for i, fighter1 in enumerate(fighter_names):
            if fighter1 in used_fighters:
                continue
                
            # Look for the next unused fighter
            for j, fighter2 in enumerate(fighter_names[i+1:], i+1):
                if fighter2 in used_fighters:
                    continue
                
                # Create fight with both fighters' odds
                fight_odds = fighters_dict[fighter1] + fighters_dict[fighter2]
                
                fight = Fight(
                    fighter1=fighter1,
                    fighter2=fighter2,
                    event_name=self.extract_event_name_from_content(),
                    event_date=datetime.now().strftime("%Y-%m-%d"),
                    weight_class="Unknown",  # Would need additional parsing
                    odds_data=fight_odds,
                    scraped_at=datetime.now().isoformat()
                )
                
                fights.append(fight)
                used_fighters.add(fighter1)
                used_fighters.add(fighter2)
                break
        
        print(f"   Created {len(fights)} fight matchups")
        return fights
    
    def extract_event_name_from_content(self) -> str:
        """Extract event name from page content"""
        
        # Try to read from saved HTML
        try:
            with open('../data/full_rendered.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for title, h1, or other header elements
            for selector in ['title', 'h1', '.event-title', '.page-header']:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if 'UFC' in text or 'Bellator' in text:
                        return text
            
        except:
            pass
        
        return "UFC Event"

def main():
    """Main scraping function"""
    
    print("🤖 Selenium-Based FightOdds Scraper")
    print("=" * 40)
    
    import sys
    if len(sys.argv) < 2:
        print("❌ Please provide a FightOdds.io event URL")
        print("Usage: python selenium_scraper.py 'https://fightodds.io/...'")
        return
    
    event_url = sys.argv[1]
    
    scraper = SeleniumFightOddsScraper()
    fights = scraper.scrape_with_selenium(event_url)
    
    if fights:
        # Save to the same format your EV calculator expects
        fights_dict = [asdict(fight) for fight in fights]
        
        with open('../data/fights.json', 'w') as f:
            json.dump(fights_dict, f, indent=2)
        
        print(f"\n✅ Successfully scraped {len(fights)} fights:")
        for fight in fights:
            books = set(odd.book for odd in fight.odds_data)
            print(f"   📊 {fight.fighter1} vs {fight.fighter2}")
            print(f"      Books: {', '.join(sorted(books))} ({len(books)} total)")
        
        print(f"\n🎯 Next: Run 'python ev_calculator.py'")
        
    else:
        print("❌ No fights scraped")
        print("💡 Check selenium_debug.html for the actual page content")

if __name__ == "__main__":
    main()