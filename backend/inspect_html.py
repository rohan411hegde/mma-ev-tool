import json
from bs4 import BeautifulSoup

def inspect_html():
    """Inspect the saved HTML to understand the structure"""
    
    try:
        with open('../data/debug_page.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"📄 HTML File Size: {len(html_content)} characters")
        print("=" * 60)
        
        # Show first 500 characters
        print("🔍 First 500 characters:")
        print("-" * 30)
        print(html_content[:500])
        print("-" * 30)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for key elements
        print("\n📋 Page Analysis:")
        
        # Check for common elements
        title = soup.find('title')
        print(f"Title: {title.text if title else 'Not found'}")
        
        h1_tags = soup.find_all('h1')
        print(f"H1 tags: {[h1.text.strip() for h1 in h1_tags]}")
        
        # Look for tables
        tables = soup.find_all('table')
        print(f"Tables found: {len(tables)}")
        
        # Look for common class names that might contain odds
        divs_with_classes = soup.find_all('div', class_=True)
        class_names = set()
        for div in divs_with_classes[:20]:  # First 20 divs
            if div.get('class'):
                class_names.update(div.get('class'))
        
        print(f"Common CSS classes: {sorted(list(class_names))[:10]}")
        
        # Look for any mention of fighter names or books
        page_text = soup.get_text().lower()
        
        fighter_names = ['imavov', 'borralho', 'saint-denis', 'ruffy']
        book_names = ['pinnacle', 'draftkings', 'fanduel', 'bet365']
        
        found_fighters = [name for name in fighter_names if name in page_text]
        found_books = [name for name in book_names if name in page_text]
        
        print(f"Fighter names found: {found_fighters}")
        print(f"Book names found: {found_books}")
        
        # Check if it's a redirect, error page, or requires JavaScript
        if 'javascript' in page_text or 'js' in page_text:
            print("\n⚠️ Page may require JavaScript to load content")
        
        if 'error' in page_text or '404' in page_text or '403' in page_text:
            print("\n❌ Page contains error messages")
        
        if 'redirect' in page_text or 'location.href' in page_text:
            print("\n🔄 Page may be redirecting")
        
        # Check if content is minimal (might be blocked or requires JS)
        if len(html_content) < 2000:
            print(f"\n⚠️ HTML content is very small ({len(html_content)} chars) - might be blocked or require JS")
        
        # Look for script tags that might contain data
        scripts = soup.find_all('script')
        print(f"\nScript tags found: {len(scripts)}")
        
        for i, script in enumerate(scripts[:3]):
            if script.string and len(script.string) > 50:
                print(f"Script {i+1} preview: {script.string[:100]}...")
        
        # Save a cleaned version for easier reading
        with open('../data/cleaned_html.txt', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        print(f"\n💾 Saved cleaned HTML to cleaned_html.txt")
        
    except FileNotFoundError:
        print("❌ debug_page.html not found - run scraper first")
    except Exception as e:
        print(f"❌ Error inspecting HTML: {e}")

def suggest_next_steps():
    """Suggest next steps based on what we found"""
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Check if the site requires JavaScript (common with modern sites)")
    print(f"2. Try using Selenium instead of requests for JavaScript-heavy sites")
    print(f"3. Check if we're being blocked (user agent, rate limiting)")
    print(f"4. Look for API endpoints that return JSON data instead of HTML")
    print(f"5. Try different headers or request parameters")

if __name__ == "__main__":
    print("🔍 HTML Structure Inspector")
    print("=" * 40)
    inspect_html()
    suggest_next_steps()