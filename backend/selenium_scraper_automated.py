import os
import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def extract_event_id_from_url(url):
    """Extract event ID from FightOdds.io URL"""
    match = re.search(r'/mma-events/(\d+)/', url)
    return match.group(1) if match else 'unknown'

def extract_event_name_from_fights(fights_data):
    """Get event name from first fight's event_name field"""
    if fights_data and len(fights_data) > 0:
        return fights_data[0].get('event_name', 'UFC Event')
    return 'UFC Event'

def extract_event_date_from_fights(fights_data):
    """Get event date from first fight's event_date field"""
    if fights_data and len(fights_data) > 0:
        return fights_data[0].get('event_date', datetime.now().isoformat())
    return datetime.now().isoformat()

def save_event_data(fights_data, event_url):
    """Save event data with unique identifier and update events list"""
    # Extract event info
    event_id = extract_event_id_from_url(event_url)
    event_name = extract_event_name_from_fights(fights_data)
    event_date = extract_event_date_from_fights(fights_data)
    
    # Create event-specific filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"event_{event_id}_{timestamp}.json"
    
    event_data = {
        'event_id': event_id,
        'event_name': event_name,
        'event_date': event_date,
        'scraped_at': datetime.now().isoformat(),
        'fights': fights_data,
        'url': event_url,
        'fights_count': len(fights_data)
    }
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save individual event file
    filepath = os.path.join('data', filename)
    with open(filepath, 'w') as f:
        json.dump(event_data, f, indent=2)
    
    print(f"Saved event data to: {filepath}")
    
    # Update events list
    update_events_list(event_data)
    
    # Also save as latest for backward compatibility
    latest_filepath = os.path.join('data', 'fights.json')
    with open(latest_filepath, 'w') as f:
        json.dump(fights_data, f, indent=2)
    
    print(f"Also saved as latest: {latest_filepath}")

def update_events_list(new_event):
    """Update the events list with new event data"""
    events_file = os.path.join('data', 'events_list.json')
    
    # Load existing events or create new list
    if os.path.exists(events_file):
        with open(events_file, 'r') as f:
            events = json.load(f)
    else:
        events = []
    
    # Remove existing event with same ID (update case)
    events = [e for e in events if e['event_id'] != new_event['event_id']]
    
    # Add new event
    events.append({
        'event_id': new_event['event_id'],
        'event_name': new_event['event_name'],
        'event_date': new_event['event_date'],
        'fights_count': new_event['fights_count'],
        'last_updated': new_event['scraped_at'],
        'url': new_event['url']
    })
    
    # Sort by date (newest first)
    events.sort(key=lambda x: x['event_date'], reverse=True)
    
    # Keep only last 10 events to avoid too much data
    events = events[:10]
    
    with open(events_file, 'w') as f:
        json.dump(events, f, indent=2)
    
    print(f"Updated events list with {len(events)} events")

def setup_driver():
    """Setup Chrome WebDriver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_fights(url):
    """Scrape fight data from the given URL"""
    print(f"Starting to scrape: {url}")
    
    driver = setup_driver()
    
    try:
        # Navigate to the page
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Wait for table to be present
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Get page source and parse with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save debug HTML
        debug_path = os.path.join('data', 'selenium_debug.html')
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Find the main table
        table = soup.find('table')
        if not table:
            print("No table found on the page")
            return []
        
        # Extract fights data
        fights_data = parse_fights_table(table, soup)
        
        return fights_data
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []
    
    finally:
        driver.quit()

def parse_fights_table(table, soup):
    """Parse the fights table and extract fight data"""
    fights_data = []
    
    # Find all rows in the table
    rows = table.find_all('tr')
    if not rows:
        print("No rows found in table")
        return fights_data
    
    # Get header row to map columns to sportsbooks
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    print(f"Found headers: {headers}")
    
    # Map common sportsbook names
    book_mapping = {
        'pinnacle': 'Pinnacle',
        'betonline': 'BetOnline', 
        'draftkings': 'DraftKings',
        'fanduel': 'FanDuel',
        'circa': 'Circa Sports',
        'bet365': 'Bet365'
    }
    
    # Create column index mapping
    col_to_book = {}
    for i, header in enumerate(headers):
        header_lower = header.lower()
        for key, book_name in book_mapping.items():
            if key in header_lower:
                col_to_book[i] = book_name
                break
    
    print(f"Column to book mapping: {col_to_book}")
    
    # Process data rows
    current_fight_data = []
    
    for row in rows[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])
        if not cells:
            continue
        
        row_data = [cell.get_text(strip=True) for cell in cells]
        
        # Check if this is a fighter row
        if len(row_data) > 0 and is_valid_fighter_name(row_data[0]):
            fighter_name = row_data[0]
            
            # Extract odds for this fighter
            fighter_odds = []
            for col_idx, book_name in col_to_book.items():
                if col_idx < len(row_data):
                    odds_text = row_data[col_idx]
                    odds_value = parse_odds(odds_text)
                    if odds_value is not None:
                        fighter_odds.append({
                            'fighter_name': fighter_name,
                            'odds': odds_value,
                            'book': book_name
                        })
            
            if fighter_odds:
                current_fight_data.append({
                    'fighter': fighter_name,
                    'odds': fighter_odds
                })
        
        # If we have data for 2 fighters, create a fight
        if len(current_fight_data) == 2:
            fight = create_fight_from_data(current_fight_data, soup)
            if fight:
                fights_data.append(fight)
            current_fight_data = []
    
    print(f"Extracted {len(fights_data)} fights")
    return fights_data

def is_valid_fighter_name(name):
    """Check if the name looks like a valid fighter name"""
    if not name or len(name) < 3 or len(name) > 50:
        return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    # Skip obvious non-fighter entries
    skip_patterns = [
        r'^\d+$',  # Pure numbers
        r'^[+-]\d+$',  # Odds format
        r'^(over|under)',  # Betting terms
        r'^(moneyline|spread|total)',  # Betting types
        r'^(home|away|draw)',  # Generic terms
    ]
    
    for pattern in skip_patterns:
        if re.match(pattern, name.lower()):
            return False
    
    return True

def parse_odds(odds_text):
    """Parse odds text into numeric value"""
    if not odds_text:
        return None
    
    # Clean the text
    odds_text = odds_text.strip().replace(',', '')
    
    # Look for American odds format (+150, -200)
    match = re.search(r'([+-]?\d+)', odds_text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    return None

def create_fight_from_data(fighter_data, soup):
    """Create a fight object from fighter data"""
    if len(fighter_data) != 2:
        return None
    
    fighter1_data = fighter_data[0]
    fighter2_data = fighter_data[1]
    
    # Combine all odds data
    all_odds = fighter1_data['odds'] + fighter2_data['odds']
    
    # Extract event info from page
    event_name = extract_event_name_from_page(soup)
    event_date = extract_event_date_from_page(soup)
    weight_class = "Unknown"  # Could be extracted if available
    
    fight = {
        'fighter1': fighter1_data['fighter'],
        'fighter2': fighter2_data['fighter'],
        'event_name': event_name,
        'event_date': event_date,
        'weight_class': weight_class,
        'odds_data': all_odds,
        'scraped_at': datetime.now().isoformat()
    }
    
    return fight

def extract_event_name_from_page(soup):
    """Extract event name from the page"""
    # Try to find event name in various places
    selectors = [
        'h1',
        '.event-title',
        '.page-title',
        'title'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            if text and 'ufc' in text.lower():
                return text
    
    return "UFC Event"

def extract_event_date_from_page(soup):
    """Extract event date from the page"""
    # Try to find date information
    date_selectors = [
        '.event-date',
        '.date',
        '[class*="date"]'
    ]
    
    for selector in date_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            # Try to parse date
            try:
                # This is a simple approach - could be enhanced
                if re.search(r'\d{4}', text):
                    return datetime.now().isoformat()
            except:
                pass
    
    return datetime.now().isoformat()

def main():
    """Main function to run the scraper"""
    # Default URL - this should be updated for each event
    url = "https://fightodds.io/odds/6602/ufc-fight-night-ulberg-vs-reyes"
    
    print("Starting UFC odds scraper...")
    
    fights = scrape_fights(url)
    
    if fights:
        save_event_data(fights, url)
        print(f"Successfully scraped and saved {len(fights)} fights")
    else:
        print("No fights data scraped")

if __name__ == "__main__":
    main()