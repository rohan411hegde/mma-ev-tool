from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from ev_calculator import EVCalculator, Fight, FighterOdds

app = Flask(__name__)
CORS(app)  # Allow frontend to connect

def load_scraped_data():
    """Load the latest scraped fight data"""
    try:
        with open('../data/fights.json', 'r') as f:
            fights_data = json.load(f)
        
        # Convert back to Fight objects for EV calculation
        fights = []
        for fight_dict in fights_data:
            odds_data = [FighterOdds(**odds) for odds in fight_dict['odds_data']]
            fight = Fight(
                fighter1=fight_dict['fighter1'],
                fighter2=fight_dict['fighter2'],
                event_name=fight_dict['event_name'],
                event_date=fight_dict['event_date'],
                weight_class=fight_dict['weight_class'],
                odds_data=odds_data,
                scraped_at=fight_dict['scraped_at']
            )
            fights.append(fight)
        
        return fights
        
    except FileNotFoundError:
        print("No fights.json found - run scraper first!")
        return []
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

def calculate_live_evs():
    """Calculate EV opportunities from scraped data"""
    fights = load_scraped_data()
    if not fights:
        return []
    
    calculator = EVCalculator()
    ev_results = calculator.analyze_all_fights(fights)
    
    return ev_results

@app.route('/api/fights')
def get_fights():
    """API endpoint to get fight data for frontend"""
    
    fights = load_scraped_data()
    
    # Convert to frontend format
    fights_for_frontend = []
    
    for fight in fights:
        # Organize odds by book for easier frontend consumption
        odds_by_book = {}
        for odds in fight.odds_data:
            book = odds.book
            fighter = odds.fighter_name
            
            if book not in odds_by_book:
                odds_by_book[book] = {}
            
            odds_by_book[book][fighter] = odds.odds
        
        # Convert to frontend format
        frontend_odds = []
        for book, fighters in odds_by_book.items():
            if fight.fighter1 in fighters and fight.fighter2 in fighters:
                frontend_odds.append({
                    'book': book,
                    'fighter1_odds': fighters[fight.fighter1],
                    'fighter2_odds': fighters[fight.fighter2]
                })
        
        fights_for_frontend.append({
            'fighter1': fight.fighter1,
            'fighter2': fight.fighter2,
            'event_name': fight.event_name,
            'event_date': fight.event_date,
            'weight_class': fight.weight_class,
            'odds': frontend_odds,
            'scraped_at': fight.scraped_at
        })
    
    return jsonify({
        'success': True,
        'fights': fights_for_frontend,
        'count': len(fights_for_frontend),
        'last_updated': fights[0].scraped_at if fights else None
    })

@app.route('/api/ev-opportunities')
def get_ev_opportunities():
    """API endpoint to get +EV opportunities"""
    
    ev_results = calculate_live_evs()
    
    # Convert to frontend format
    opportunities = []
    
    for ev in ev_results:
        opportunities.append({
            'fighter': ev.fighter,
            'book': ev.book,
            'ev_percentage': ev.ev_percentage,
            'confidence_score': ev.confidence_score,
            'sharp_consensus_prob': ev.sharp_consensus_prob,
            'square_prob': ev.square_prob,
            'recommendation': ev.recommendation,
            'fight_info': ev.fight_info,
            'kelly_size': ev.kelly_size,
            'kelly_dollars': ev.kelly_dollars,
            'kelly_units': ev.kelly_units,
            'kelly_category': ev.kelly_category
        })
    
    return jsonify({
        'success': True,
        'opportunities': opportunities,
        'count': len(opportunities),
        'strong_bets': len([ev for ev in ev_results if ev.ev_percentage >= 2.5]),
        'avg_ev': round(sum(ev.ev_percentage for ev in ev_results) / len(ev_results), 1) if ev_results else 0
    })

@app.route('/api/stats')
def get_stats():
    """API endpoint to get overall stats"""
    
    fights = load_scraped_data()
    ev_results = calculate_live_evs()
    
    if not fights:
        return jsonify({
            'success': False,
            'error': 'No data available'
        })
    
    # Calculate stats
    total_fights = len(fights)
    total_books = len(set(odds.book for fight in fights for odds in fight.odds_data))
    total_evs = len(ev_results)
    strong_bets = len([ev for ev in ev_results if ev.ev_percentage >= 2.5])
    avg_ev = round(sum(ev.ev_percentage for ev in ev_results) / len(ev_results), 1) if ev_results else 0
    
    return jsonify({
        'success': True,
        'total_fights': total_fights,
        'total_books': total_books,
        'total_opportunities': total_evs,
        'strong_bets': strong_bets,
        'avg_ev': avg_ev,
        'event_name': fights[0].event_name if fights else 'No Event',
        'last_updated': fights[0].scraped_at if fights else None
    })

@app.route('/api/refresh')
def refresh_data():
    """Trigger a fresh EV calculation"""
    try:
        ev_results = calculate_live_evs()
        
        return jsonify({
            'success': True,
            'message': f'Recalculated {len(ev_results)} EV opportunities',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting MMA EV API server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
