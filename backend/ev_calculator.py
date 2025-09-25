import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

def american_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal odds"""
    if american_odds == 0:
        return 2.0  # Default to even odds if zero
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def decimal_to_probability(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability"""
    if decimal_odds <= 0:
        return 0.5  # Default to 50% if invalid odds
    return 1 / decimal_odds

def remove_vig(prob1: float, prob2: float) -> tuple:
    """Remove vigorish from two probabilities"""
    total = prob1 + prob2
    if total <= 1e-10:  # Check for very small values, not just zero
        return 0.5, 0.5  # Return 50/50 if invalid
    return prob1 / total, prob2 / total

def calculate_expected_value(true_prob: float, decimal_odds: float) -> float:
    """Calculate expected value given true probability and odds"""
    payout = decimal_odds - 1
    return (true_prob * payout) - ((1 - true_prob) * 1)

def get_sharp_consensus_probability(fighter_name: str, odds_data: List[Dict]) -> float:
    """
    Calculate sharp consensus probability using Pinnacle, Circa, and BetOnline as sharp books
    """
    sharp_books = ['pinnacle', 'pinnacle sports', 'circa', 'circa sports', 'betonline', 'bet online']
    sharp_odds = []
    
    for odds in odds_data:
        if (odds.get('fighter_name') == fighter_name and 
            odds.get('book', '').lower() in sharp_books):
            sharp_odds.append(odds.get('odds'))
    
    # Use average of sharp books if available
    if sharp_odds:
        avg_american = sum(sharp_odds) / len(sharp_odds)
        decimal_odds = american_to_decimal(int(avg_american))
        return decimal_to_probability(decimal_odds)
    
    # Fallback to all books average if no sharp books found
    all_odds = []
    for odds in odds_data:
        if odds.get('fighter_name') == fighter_name:
            all_odds.append(odds.get('odds'))
    
    if all_odds:
        avg_american = sum(all_odds) / len(all_odds)
        decimal_odds = american_to_decimal(int(avg_american))
        return decimal_to_probability(decimal_odds)
    
    return 0.5  # Default 50% if no odds found

def get_square_probability(fighter_name: str, odds_data: List[Dict]) -> float:
    """
    Calculate square book probability using recreational books
    Excludes sharp books: Pinnacle, Circa, BetOnline
    """
    square_books = ['draftkings', 'fanduel', 'betmgm', 'caesars', 'bet365', 'pointsbet', 'barstool']
    square_odds = []
    
    for odds in odds_data:
        if (odds.get('fighter_name') == fighter_name and 
            odds.get('book', '').lower() in square_books):
            square_odds.append(odds.get('odds'))
    
    if square_odds:
        avg_american = sum(square_odds) / len(square_odds)
        decimal_odds = american_to_decimal(int(avg_american))
        return decimal_to_probability(decimal_odds)
    
    # Fallback to sharp consensus if no square books found
    return get_sharp_consensus_probability(fighter_name, odds_data)

def calculate_ev_for_fighter(fighter_name: str, book: str, odds_data: List[Dict]) -> Optional[Dict]:
    """Calculate EV opportunity for a specific fighter at a specific book"""
    
    # Get the odds for this fighter at this book
    fighter_odds = None
    for odds in odds_data:
        if odds.get('fighter_name') == fighter_name and odds.get('book') == book:
            fighter_odds = odds.get('odds')
            break
    
    if not fighter_odds or fighter_odds == 0:
        return None
    
    try:
        # Get sharp consensus probability (true probability)
        sharp_prob = get_sharp_consensus_probability(fighter_name, odds_data)
        
        # Get square book probability for comparison
        square_prob = get_square_probability(fighter_name, odds_data)
        
        # Validate probabilities
        if sharp_prob <= 0 or sharp_prob >= 1 or square_prob <= 0 or square_prob >= 1:
            return None
        
        # Calculate EV
        decimal_odds = american_to_decimal(fighter_odds)
        if decimal_odds <= 0:
            return None
            
        ev = calculate_expected_value(sharp_prob, decimal_odds)
        ev_percentage = ev * 100
        
        # Only return if EV is positive and meaningful
        if ev_percentage < 0.5:  # Less than 0.5% EV is not worth it
            return None
        
        # Determine recommendation based on EV
        if ev_percentage >= 2.5:
            recommendation = "Strong Bet"
        elif ev_percentage >= 1.5:
            recommendation = "Good Bet"
        elif ev_percentage >= 1.0:
            recommendation = "Decent Bet"
        else:
            recommendation = "Small Edge"
        
        # Calculate confidence score based on sample size and edge
        confidence_score = min(100, ev_percentage * 10)  # Simple confidence scoring
        
        return {
            'fighter': fighter_name,
            'book': book,
            'ev_percentage': ev_percentage,
            'confidence_score': confidence_score,
            'sharp_consensus_prob': sharp_prob,
            'square_prob': square_prob,
            'recommendation': recommendation,
            'fight_info': f"{fighter_name} odds analysis",
            'odds': fighter_odds
        }
    except Exception as e:
        print(f"Error calculating EV for {fighter_name} at {book}: {e}")
        return None

def calculate_ev_opportunities(fights_data: List[Dict]) -> List[Dict]:
    """
    Main function to calculate EV opportunities from fights data
    This is the function that the Flask API imports
    """
    if not fights_data:
        return []
    
    opportunities = []
    
    for fight in fights_data:
        if not isinstance(fight, dict):
            continue
            
        fighter1 = fight.get('fighter1', '')
        fighter2 = fight.get('fighter2', '')
        odds_data = fight.get('odds_data', [])
        
        if not odds_data:
            continue
        
        # Get all unique books
        books = set()
        for odds in odds_data:
            if odds.get('book'):
                books.add(odds.get('book'))
        
        # Calculate EV for each fighter at each book
        for book in books:
            # Check fighter 1
            ev_opp1 = calculate_ev_for_fighter(fighter1, book, odds_data)
            if ev_opp1:
                ev_opp1['fight_info'] = f"{fighter1} vs {fighter2}"
                opportunities.append(ev_opp1)
            
            # Check fighter 2
            ev_opp2 = calculate_ev_for_fighter(fighter2, book, odds_data)
            if ev_opp2:
                ev_opp2['fight_info'] = f"{fighter1} vs {fighter2}"
                opportunities.append(ev_opp2)
    
    # Sort by EV percentage (highest first)
    opportunities.sort(key=lambda x: x.get('ev_percentage', 0), reverse=True)
    
    return opportunities

def save_ev_opportunities(opportunities: List[Dict], filename: str = 'ev_opportunities.json'):
    """Save EV opportunities to a JSON file"""
    data = {
        'calculated_at': datetime.now().isoformat(),
        'opportunities': opportunities,
        'count': len(opportunities)
    }
    
    filepath = os.path.join('data', filename)
    os.makedirs('data', exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath

def load_fights_and_calculate_ev():
    """Load fights data and calculate EV opportunities"""
    fights_file = os.path.join('data', 'fights.json')
    
    if not os.path.exists(fights_file):
        print("No fights data found")
        return []
    
    try:
        with open(fights_file, 'r') as f:
            fights_data = json.load(f)
        
        opportunities = calculate_ev_opportunities(fights_data)
        
        if opportunities:
            save_ev_opportunities(opportunities)
            print(f"Calculated {len(opportunities)} EV opportunities")
        else:
            print("No EV opportunities found")
        
        return opportunities
        
    except Exception as e:
        print(f"Error calculating EV opportunities: {e}")
        return []

if __name__ == "__main__":
    # Can be run standalone to calculate and save EV opportunities
    opportunities = load_fights_and_calculate_ev()
    for opp in opportunities[:5]:  # Show top 5
        print(f"{opp['fighter']} at {opp['book']}: {opp['ev_percentage']:.1f}% EV ({opp['recommendation']})")