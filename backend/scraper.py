import requests
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
    odds: int  # American odds format
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

class FightOddsIOScraper:
    def __init__(self):
        self.base_url = "https://fightodds.io"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Your target books - exactly as they appear on FightOdds.io headers
        self.target_books = {
            'Pinnacle': 'Pinnacle',
            'BetOnline': 'BetOnline', 
            'Circa': 'Circa Sports',
            'DraftKings': 'DraftKings',
            'FanDuel': 'FanDuel',
            'Bet365': 'Bet365'
        }
        
        # Sharp vs Square classification
        self.sharp_books = ['Pinnacle', 'BetOnline', 'Circa Sports']
        self.square_books = ['DraftKings', 'Bet365', 'FanDuel']
    
    def get_upcoming_events(self) -> List[Dict]:
        """Get list of upcoming MMA events from FightOdds.io"""
        try:
            response = requests.get(f"{self.base_url}/mma-events", headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            # Look for event links - adjust selector based on actual structure
            event_links = soup.find_all('a', href=re.compile(r'/mma-events/\d+/'))
            
            for link in event_links[:5]:  # Limit to next 5 events
                event_url = self.base_url + link['href'] if not link['href'].startswith('http') else link['href']
                event_name = link.text.strip()
                
                events.append({
                    'name': event_name,
                    'url': event_url
                })
            
            print(f"Found {len(events)} upcoming events")
            return events
            
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    def scrape_event_odds(self, event_url: str) -> List[Fight]:
        """Scrape odds for all fights in an event - REAL SCRAPING"""
        try:
            print(f"🕷️ Scraping: {event_url}")
            response = requests.get(event_url, headers=self.headers)
            response.raise_for_status()
            
            # Save HTML for debugging
            with open('../data/debug_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"💾 Saved HTML to debug_page.html ({len(response.text)} chars)")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract event info
            event_name = self.extract_event_name(soup, event_url)
            
            # Find the main odds table
            fights = self.extract_fights_from_table(soup, event_name)
            
            print(f"✅ Extracted {len(fights)} fights from {event_name}")
            return fights
            
        except Exception as e:
            print(f"❌ Error scraping {event_url}: {e}")
            return []
    
    def extract_event_name(self, soup, event_url: str) -> str:
        """Extract event name from various possible locations"""
        
        # Try different selectors for event name
        selectors = [
            'h1',
            '.event-title',
            '.page-title',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if 'UFC' in name or 'Bellator' in name:
                    return name
        
        # Fallback: extract from URL
        if 'imavov-vs-borralho' in event_url.lower():
            return "UFC Fight Night: Imavov vs Borralho"
        elif 'ufc' in event_url.lower():
            return "UFC Event"
        else:
            return "MMA Event"
    
    def extract_fights_from_table(self, soup, event_name: str) -> List[Fight]:
        """Extract all fights from the odds table"""
        
        fights = []
        
        # Strategy 1: Look for the main data table
        # FightOdds.io typically has the odds in a table structure
        
        # Find all tables and identify the odds table
        tables = soup.find_all('table')
        main_table = None
        
        for table in tables:
            # Look for table with fighter names and odds
            table_text = table.get_text().lower()
            if any(word in table_text for word in ['pinnacle', 'draftkings', 'fanduel']):
                main_table = table
                break
        
        if not main_table:
            print("⚠️ No odds table found, looking for alternative structure...")
            # Try alternative approaches
            return self.extract_fights_alternative(soup, event_name)
        
        print("✅ Found main odds table")
        
        # Extract table headers to map column positions to books
        headers = self.extract_table_headers(main_table)
        book_columns = self.map_book_columns(headers)
        
        print(f"📊 Mapped {len(book_columns)} book columns: {list(book_columns.values())}")
        
        # Extract fighter rows and odds
        rows = main_table.find_all('tr')
        
        current_fight_data = []
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:  # Need at least fighter name + some odds
                continue
                
            # Extract cell texts
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Check if this is a fighter row (first cell contains a name)
            first_cell = cell_texts[0] if cell_texts else ""
            
            # Skip header rows and empty rows
            if not first_cell or first_cell.lower() in ['fighters', 'fighter', '']:
                continue
            
            # Check if this looks like a fighter name
            if self.is_fighter_name(first_cell):
                fighter_odds = self.extract_odds_from_row(first_cell, cell_texts, book_columns)
                
                if fighter_odds:
                    current_fight_data.extend(fighter_odds)
        
        # Group odds into fights (every 2 fighters = 1 fight)
        fights = self.group_odds_into_fights(current_fight_data, event_name)
        
        return fights
    
    def extract_table_headers(self, table) -> List[str]:
        """Extract column headers from the table"""
        headers = []
        
        # Look for header row
        header_row = table.find('tr')  # First row is usually headers
        if header_row:
            header_cells = header_row.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_cells]
        
        return headers
    
    def map_book_columns(self, headers: List[str]) -> Dict[int, str]:
        """Map column indices to book names"""
        book_columns = {}
        
        for i, header in enumerate(headers):
            header_clean = header.strip()
            
            # Check if header matches any of our target books
            for display_name, canonical_name in self.target_books.items():
                if display_name.lower() in header_clean.lower():
                    book_columns[i] = canonical_name
                    break
        
        return book_columns
    
    def is_fighter_name(self, text: str) -> bool:
        """Determine if a text string looks like a fighter name"""
        
        # Basic heuristics for fighter names
        if len(text) < 3 or len(text) > 50:
            return False
        
        # Should contain letters and possibly spaces/apostrophes
        if not re.match(r"^[A-Za-z\s'\-\.]+$", text):
            return False
        
        # Should not be a number or odds
        if re.match(r'^[+-]?\d+$', text):
            return False
            
        # Should not be common table headers
        skip_words = ['fighters', 'fighter', 'odds', 'book', 'sportsbook']
        if text.lower() in skip_words:
            return False
        
        return True
    
    def extract_odds_from_row(self, fighter_name: str, cell_texts: List[str], book_columns: Dict[int, str]) -> List[FighterOdds]:
        """Extract odds for a fighter from a table row"""
        
        odds_list = []
        
        for col_index, book_name in book_columns.items():
            if col_index < len(cell_texts):
                odds_text = cell_texts[col_index].strip()
                
                # Try to parse as odds
                odds_value = self.parse_odds(odds_text)
                if odds_value is not None:
                    odds_list.append(FighterOdds(
                        fighter_name=fighter_name,
                        odds=odds_value,
                        book=book_name
                    ))
        
        return odds_list
    
    def parse_odds(self, odds_text: str) -> Optional[int]:
        """Parse odds text into integer"""
        
        # Remove any extra characters
        clean_text = re.sub(r'[^\d\+\-]', '', odds_text)
        
        # Match American odds format
        match = re.match(r'^([+-]?)(\d+)$', clean_text)
        if match:
            sign, number = match.groups()
            odds_value = int(number)
            
            # Apply sign
            if sign == '-':
                return -odds_value
            else:
                return odds_value
        
        return None
    
    def group_odds_into_fights(self, all_odds: List[FighterOdds], event_name: str) -> List[Fight]:
        """Group fighter odds into fight objects"""
        
        # Group by fighters
        fighters_odds = {}
        for odds in all_odds:
            fighter = odds.fighter_name
            if fighter not in fighters_odds:
                fighters_odds[fighter] = []
            fighters_odds[fighter].append(odds)
        
        # Create fights (pair fighters)
        fighters = list(fighters_odds.keys())
        fights = []
        
        # Simple pairing - every consecutive pair of fighters
        for i in range(0, len(fighters), 2):
            if i + 1 < len(fighters):
                fighter1 = fighters[i]
                fighter2 = fighters[i + 1]
                
                fight_odds = fighters_odds[fighter1] + fighters_odds[fighter2]
                
                fight = Fight(
                    fighter1=fighter1,
                    fighter2=fighter2,
                    event_name=event_name,
                    event_date=datetime.now().strftime("%Y-%m-%d"),  # Placeholder
                    weight_class="Unknown",  # Would need additional scraping
                    odds_data=fight_odds,
                    scraped_at=datetime.now().isoformat()
                )
                
                fights.append(fight)
        
        return fights
    
    def extract_fights_alternative(self, soup, event_name: str) -> List[Fight]:
        """Alternative extraction method if table approach fails"""
        
        print("🔄 Trying alternative extraction methods...")
        
        # Method 1: Look for div/span structures
        # Method 2: Look for JSON data in script tags
        # Method 3: Use CSS selectors for common patterns
        
        # For now, return empty and let user know to inspect HTML
        print("⚠️ Could not extract fights automatically")
        print("💡 Check the saved debug_page.html file to see the structure")
        
        return []
    
    def scrape_all_upcoming_fights(self) -> List[Fight]:
        """Main function: scrape all upcoming events or use provided URL"""
        all_fights = []
        
        # This will be called with a specific URL from main()
        # For now, return empty to trigger URL-specific scraping
        return []
    
    def save_to_json(self, fights: List[Fight], filename: str = "../data/fights.json"):
        """Save fight data to JSON file"""
        fights_dict = [asdict(fight) for fight in fights]
        
        with open(filename, 'w') as f:
            json.dump(fights_dict, f, indent=2)
        
        print(f"💾 Saved {len(fights)} fights to {filename}")

def main():
    """Scrape any FightOdds.io event URL"""
    scraper = FightOddsIOScraper()
    
    print("🥊 Universal FightOdds.io Scraper")
    print("=" * 40)
    
    # Check for URL argument
    import sys
    if len(sys.argv) > 1:
        event_url = sys.argv[1]
        print(f"📅 Scraping specific event: {event_url}")
        
        fights = scraper.scrape_event_odds(event_url)
        
        if fights:
            # Save to JSON
            scraper.save_to_json(fights)
            
            # Print summary
            print(f"\n✅ Successfully scraped {len(fights)} fights:")
            for fight in fights:
                books = set(odd.book for odd in fight.odds_data)
                print(f"   📊 {fight.fighter1} vs {fight.fighter2}")
                print(f"      Books: {', '.join(sorted(books))} ({len(books)} total)")
            
            print(f"\n🎯 Next: Run 'python ev_calculator.py' to find +EV opportunities")
        else:
            print("❌ No fights scraped")
            print("💡 Check debug_page.html to see the actual page structure")
    else:
        print("❌ Please provide a FightOdds.io event URL")
        print("Usage: python scraper.py 'https://fightodds.io/mma-events/6547/ufc-fight-night-imavov-vs-borralho/odds'")

if __name__ == "__main__":
    main()